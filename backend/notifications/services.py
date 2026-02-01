"""
알림 발송 서비스
신규 정책 → 매칭 회원 → 이메일 발송
"""
import logging
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from accounts.models import Profile
from policies.models import Policy
from policies.services.matching import match_policies
from .models import NotificationLog

logger = logging.getLogger(__name__)


def notify_matching_users(policy: Policy) -> dict:
    """
    신규 정책에 매칭되는 회원들에게 이메일 알림 발송
    
    Args:
        policy: 신규 Policy 객체
        
    Returns:
        dict: {'sent': int, 'skipped': int, 'failed': int}
    """
    stats = {'sent': 0, 'skipped': 0, 'failed': 0}
    
    # 알림 수신 동의한 회원들 조회
    eligible_profiles = Profile.objects.filter(
        email_notification_enabled=True,
        notification_email__isnull=False,
    ).exclude(notification_email='').select_related('user')
    
    logger.info(f"[알림] 정책 '{policy.title}' - 알림 대상 회원 {eligible_profiles.count()}명 조회")
    
    for profile in eligible_profiles:
        try:
            # 이미 발송한 적 있는지 확인
            if NotificationLog.objects.filter(user=profile.user, policy=policy).exists():
                stats['skipped'] += 1
                continue
            
            # 매칭 여부 확인
            # match_policies는 여러 정책과 매칭하지만, 우리는 특정 정책만 체크
            user_info = profile.to_matching_dict()
            if not _is_policy_matching(policy, user_info):
                stats['skipped'] += 1
                continue
            
            # 이메일 발송
            success = send_policy_notification(
                email=profile.notification_email,
                user_name=profile.user.username,
                policy=policy,
            )
            
            # 발송 이력 저장
            NotificationLog.objects.create(
                user=profile.user,
                policy=policy,
                email=profile.notification_email,
                status='sent' if success else 'failed',
                sent_at=datetime.now() if success else None,
            )
            
            if success:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
                
        except IntegrityError:
            # 중복 발송 시도 (unique_together 위반)
            stats['skipped'] += 1
        except Exception as e:
            logger.error(f"[알림] 발송 실패 ({profile.user.username}): {e}")
            stats['failed'] += 1
    
    logger.info(f"[알림] 정책 '{policy.title}' 발송 완료: {stats}")
    return stats


def _is_policy_matching(policy: Policy, user_info: dict) -> bool:
    """
    특정 정책이 사용자 정보와 매칭되는지 확인
    matching.py의 필터링 로직 간소화 버전
    """
    # 나이 체크
    user_age = user_info.get('age')
    if user_age is not None:
        if policy.age_min and user_age < policy.age_min:
            return False
        if policy.age_max and user_age > policy.age_max:
            return False
    
    # 지역 체크 (정책에 지역 제한이 있는 경우)
    user_residence = user_info.get('residence', '')
    if policy.district and user_residence:
        if policy.district not in user_residence and user_residence not in policy.district:
            return False
    
    # 특수조건 체크 (정책이 특수조건 전용인 경우)
    user_special = user_info.get('special_conditions', [])
    
    if policy.is_for_single_parent and '한부모' not in str(user_special):
        return False
    if policy.is_for_disabled and '장애' not in str(user_special) and '장애인' not in str(user_special):
        return False
    if policy.is_for_low_income and '기초수급' not in str(user_special) and '수급자' not in str(user_special):
        return False
    if policy.is_for_newlywed and '신혼' not in str(user_special):
        return False
    
    return True


def send_policy_notification(email: str, user_name: str, policy: Policy) -> bool:
    """
    이메일 발송
    
    Args:
        email: 수신자 이메일
        user_name: 수신자 이름
        policy: 정책 객체
        
    Returns:
        bool: 발송 성공 여부
    """
    subject = f"[복지나침반] 새로운 맞춤 정책 알림: {policy.title}"
    
    message = f"""
안녕하세요, {user_name}님!

회원님의 프로필과 매칭되는 새로운 정책이 등록되었습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 정책명: {policy.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 정책 설명:
{policy.description[:300]}{'...' if len(policy.description) > 300 else ''}

📅 신청 기간: {policy.apply_start_date or '미정'} ~ {policy.apply_end_date or '미정'}

🔗 자세히 보기: {policy.apply_url or '복지나침반 앱에서 확인하세요'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

본 메일은 '정책정보 알림 수신 동의'에 따라 발송되었습니다.
알림 수신을 원하지 않으시면 마이페이지에서 설정을 변경해주세요.

복지나침반 드림
"""
    
    try:
        # 실제 이메일 발송
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"[이메일 발송 성공] {email} - {policy.title}")
        return True
        
    except Exception as e:
        logger.error(f"[이메일 발송 실패] {email}: {e}")
        return False
