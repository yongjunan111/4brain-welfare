"""
데이터 정제 서비스 - 회의 결정사항 반영

정제 규칙:
1. 나이: 빈 값 → 키워드 기반 추론 → 기본값 19-39, 0은 유지
2. 신청기간: 전체 +2년 변환
3. 카테고리: 대분류 5개 + 중분류 보존
"""

import logging
import re
from datetime import datetime, date
from typing import Optional, Any, Tuple
from dataclasses import dataclass
from django.utils import timezone

logger = logging.getLogger(__name__)


# 나이 추론 규칙 (키워드 기반)
AGE_RULES = [
    # (키워드 리스트, min, max, 라벨)
    (['청년', '청년센터'], 19, 39, '청년'),
    (['대학생', '대학교', '대학원', '실습생'], 18, 99, '대학생'),
    (['학부모', '부모교실', '청소년기부모'], 25, 55, '학부모'),
    (['양육', '영유아', '성장지원금'], 20, 55, '양육'),
    (['장애인', '장애'], 0, 99, '장애인'),
    (['다문화', '이민자'], 0, 99, '다문화'),
    (['1인가구'], 19, 39, '1인가구'),
    (['예술인', '예술가'], 19, 65, '예술인'),
    (['어르신', '노인', '65세'], 0, 99, '전연령'),
    (['코로나', '예방접종', '백신'], 0, 99, '전연령'),
    (['상품권', '축제', '탐방'], 0, 99, '전연령'),
    (['취업', '일자리', '면접', '취업사관'], 19, 39, '청년취업'),
]
DEFAULT_MIN_AGE = 0
DEFAULT_MAX_AGE = 99


@dataclass
class TransformedPolicy:
    """변환된 정책 데이터"""
    plcy_no: str
    plcy_nm: str
    plcy_expln_cn: str
    plcy_sprt_cn: str

    # 나이 (정제 규칙 적용)
    sprt_trgt_min_age: Optional[int]
    sprt_trgt_max_age: Optional[int]

    # 소득/자격 조건
    earn_cnd_se_cd: str
    earn_min_amt: Optional[int]
    earn_max_amt: Optional[int]
    mrg_stts_cd: str
    job_cd: str
    school_cd: str

    # 신청기간 (2024→2026 변환 적용)
    aply_start_dt: Optional[date]
    aply_end_dt: Optional[date]
    biz_prd_bgng_ymd: Optional[date]
    biz_prd_end_ymd: Optional[date]

    # 신청 방법
    plcy_aply_mthd_cn: str
    aply_url_addr: str

    # 지역
    district: Optional[str]

    # 카테고리 (대분류 + 중분류)
    lclsf_nm: str  # 대분류: UI 표시용
    mclsf_nm: str  # 중분류: 매칭 로직용

    # 메타데이터
    frst_reg_dt: Optional[datetime]
    last_mdfcn_dt: Optional[datetime]


class PolicyTransformer:
    """정책 데이터 정제"""

    def transform(self, raw: dict) -> TransformedPolicy:
        # 나이 정제: 빈 값 → 키워드 추론 → 기본값, 0은 유지
        policy_name = raw.get('plcyNm', '')
        min_age, max_age = self._infer_age(
            raw.get('sprtTrgtMinAge'),
            raw.get('sprtTrgtMaxAge'),
            policy_name
        )

        # 신청기간 정제: 2024 → 2026 변환
        aply_start, aply_end = self._parse_date_range_with_year_fix(raw.get('aplyYmd', ''))

        return TransformedPolicy(
            plcy_no=raw['plcyNo'],
            plcy_nm=raw.get('plcyNm', ''),
            plcy_expln_cn=raw.get('plcyExplnCn', ''),
            plcy_sprt_cn=raw.get('plcySprtCn', ''),

            sprt_trgt_min_age=min_age,
            sprt_trgt_max_age=max_age,

            earn_cnd_se_cd=raw.get('earnCndSeCd', ''),
            earn_min_amt=self._parse_int(raw.get('earnMinAmt')),
            earn_max_amt=self._parse_int(raw.get('earnMaxAmt')),
            mrg_stts_cd=raw.get('mrgSttsCd', ''),
            job_cd=raw.get('jobCd', ''),
            school_cd=raw.get('schoolCd', ''),

            aply_start_dt=aply_start,
            aply_end_dt=aply_end,
            biz_prd_bgng_ymd=self._parse_date_with_year_fix(raw.get('bizPrdBgngYmd')),
            biz_prd_end_ymd=self._parse_date_with_year_fix(raw.get('bizPrdEndYmd')),

            plcy_aply_mthd_cn=raw.get('plcyAplyMthdCn', ''),
            aply_url_addr=raw.get('aplyUrlAddr', ''),

            district=self._parse_district(raw.get('rgtrInstCdNm', '')),

            lclsf_nm=raw.get('lclsfNm', '').strip(),  # 대분류
            mclsf_nm=raw.get('mclsfNm', '').strip(),  # 중분류

            frst_reg_dt=self._parse_datetime(raw.get('frstRegDt')),
            last_mdfcn_dt=self._parse_datetime(raw.get('lastMdfcnDt')),
        )

    def transform_many(self, raw_list: list[dict]) -> list[TransformedPolicy]:
        results = []
        errors = []

        for raw in raw_list:
            try:
                results.append(self.transform(raw))
            except Exception as e:
                plcy_no = raw.get('plcyNo', 'UNKNOWN')
                logger.warning(f"변환 실패 ({plcy_no}): {e}")
                errors.append(plcy_no)

        if errors:
            logger.warning(f"총 {len(errors)}개 변환 실패")

        return results

    def _infer_age(self, raw_min: Any, raw_max: Any, policy_name: str) -> Tuple[Optional[int], Optional[int]]:
        """
        나이 추론 로직:
        1. 원본 값이 있고 0이 아니면 → 그대로 사용
        2. 빈 값이면 → 정책명 키워드로 추론
        3. 추론 실패 → 기본값 (loader에서 적용)
        4. 0은 그대로 유지
        """
        min_age = self._parse_age_value(raw_min)
        max_age = self._parse_age_value(raw_max)

        # 둘 다 유효한 값이면 그대로 반환 (0 포함)
        if min_age is not None and max_age is not None:
            return min_age, max_age

        # 빈 값이 있으면 키워드 기반 추론
        inferred_min, inferred_max = self._infer_age_from_keywords(policy_name)

        # 빈 값만 추론값으로 대체
        if min_age is None:
            min_age = inferred_min
        if max_age is None:
            max_age = inferred_max

        return min_age, max_age

    def _parse_age_value(self, value: Any) -> Optional[int]:
        """단순 파싱 (0 포함 그대로 반환)"""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _infer_age_from_keywords(self, policy_name: str) -> Tuple[Optional[int], Optional[int]]:
        """정책명 키워드로 나이 추론"""
        for keywords, min_age, max_age, label in AGE_RULES:
            for keyword in keywords:
                if keyword in policy_name:
                    logger.debug(f"나이 추론: '{policy_name}' → {label} ({min_age}-{max_age})")
                    return min_age, max_age

        # 매칭 안 되면 None (loader에서 기본값 적용)
        return None, None

    def _parse_date_with_year_fix(self, value: str) -> Optional[date]:
        """
        날짜 정제 + 전체 +2년 변환

        예: "20240916" → date(2026, 9, 16)
            "20250630" → date(2027, 6, 30)
        """
        if not value or len(value) != 8:
            return None

        try:
            parsed = datetime.strptime(value, '%Y%m%d').date()
            # 전체 +2년
            parsed = parsed.replace(year=parsed.year + 2)
            return parsed
        except ValueError:
            return None

    def _parse_date_range_with_year_fix(self, value: str) -> tuple[Optional[date], Optional[date]]:
        """
        날짜 범위 정제 + 전체 +2년 변환

        예: "20240916 ~ 20251231" → (date(2026,9,16), date(2027,12,31))
        """
        if not value or '~' not in value:
            return None, None

        try:
            parts = value.split('~')
            start_str = parts[0].strip()
            end_str = parts[1].strip() if len(parts) > 1 else ''

            start_dt = self._parse_date_with_year_fix(start_str) if start_str else None
            end_dt = self._parse_date_with_year_fix(end_str) if end_str else None

            return start_dt, end_dt
        except Exception:
            return None, None

    def _parse_int(self, value: Any) -> Optional[int]:
        if not value or value == '' or value == '0':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_datetime(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            # 1. 일단 문자를 날짜시간으로 바꿈 (아직 타임존 정보 없음)
            naive_dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            
            # 2. Django 설정(Asia/Seoul)에 맞춰 타임존 도장을 찍어줌 (이게 핵심!)
            return timezone.make_aware(naive_dt)
            
        except ValueError:
            return None

    def _parse_district(self, value: str) -> Optional[str]:
        """서울특별시 은평구 → 은평구"""
        if not value or value == '서울특별시':
            return None
        return value.replace('서울특별시 ', '')
