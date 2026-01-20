"""DB 적재 서비스"""

import logging
from typing import NamedTuple
from django.db import transaction
from policies.models import Policy, Category
from .transformer import TransformedPolicy

logger = logging.getLogger(__name__)


class LoadResult(NamedTuple):
    created: int
    updated: int
    skipped: int
    errors: list[str]


class PolicyLoader:
    """정책 DB 적재 (UPSERT)"""

    # 대분류 5개 (원본 API)
    CATEGORY_MAPPING = {
        '일자리': '일자리',
        '주거': '주거',
        '교육': '교육',
        '복지문화': '복지문화',
        '참여권리': '참여권리',
    }

    # 나이 기본값 (빈 값일 때)
    DEFAULT_MIN_AGE = 0
    DEFAULT_MAX_AGE = 99

    def __init__(self):
        self._category_cache: dict[str, Category] = {}
        self._init_categories()

    def _init_categories(self):
        category_names = list(self.CATEGORY_MAPPING.values()) + ['기타']
        for name in category_names:
            cat, created = Category.objects.get_or_create(name=name)
            self._category_cache[name] = cat

    @transaction.atomic
    def load(self, policies: list[TransformedPolicy]) -> LoadResult:
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for policy in policies:
            try:
                was_created = self._load_one(policy)
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                logger.error(f"적재 실패 ({policy.plcy_no}): {e}")
                errors.append(policy.plcy_no)
                skipped += 1

        logger.info(f"적재 완료: 생성 {created}, 수정 {updated}, 스킵 {skipped}")
        return LoadResult(created, updated, skipped, errors)

    def _load_one(self, policy: TransformedPolicy) -> bool:
        # 나이 기본값 적용 (빈 값일 때만, 0은 유지)
        min_age = policy.sprt_trgt_min_age
        max_age = policy.sprt_trgt_max_age

        if min_age is None:
            min_age = self.DEFAULT_MIN_AGE
        if max_age is None:
            max_age = self.DEFAULT_MAX_AGE

        obj, created = Policy.objects.update_or_create(
            plcy_no=policy.plcy_no,
            defaults={
                'plcy_nm': policy.plcy_nm,
                'plcy_expln_cn': policy.plcy_expln_cn,
                'plcy_sprt_cn': policy.plcy_sprt_cn,
                'sprt_trgt_min_age': min_age,
                'sprt_trgt_max_age': max_age,
                'earn_cnd_se_cd': policy.earn_cnd_se_cd,
                'earn_min_amt': policy.earn_min_amt,
                'earn_max_amt': policy.earn_max_amt,
                'mrg_stts_cd': policy.mrg_stts_cd,
                'job_cd': policy.job_cd,
                'school_cd': policy.school_cd,
                'aply_start_dt': policy.aply_start_dt,
                'aply_end_dt': policy.aply_end_dt,
                'biz_prd_bgng_ymd': policy.biz_prd_bgng_ymd,
                'biz_prd_end_ymd': policy.biz_prd_end_ymd,
                'plcy_aply_mthd_cn': policy.plcy_aply_mthd_cn,
                'aply_url_addr': policy.aply_url_addr,
                'district': policy.district,
                'lclsf_nm': policy.lclsf_nm,  # 대분류
                'mclsf_nm': policy.mclsf_nm,  # 중분류
                'frst_reg_dt': policy.frst_reg_dt,
                'last_mdfcn_dt': policy.last_mdfcn_dt,
            }
        )

        # 카테고리 연결 (대분류 기준)
        self._link_categories(obj, policy.lclsf_nm)

        return created

    def _link_categories(self, policy_obj: Policy, lclsf_nm: str):
        policy_obj.categories.clear()

        if not lclsf_nm:
            policy_obj.categories.add(self._category_cache['기타'])
            return

        mapped_name = self.CATEGORY_MAPPING.get(lclsf_nm, '기타')
        category = self._category_cache.get(mapped_name)
        if category:
            policy_obj.categories.add(category)
