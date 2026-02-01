"""
Django Signal: 신규 정책 감지 → 알림 발송
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from policies.models import Policy
from .services import notify_matching_users

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Policy)
def notify_on_new_policy(sender, instance, created, **kwargs):
    """
    신규 정책 생성 시 매칭 회원에게 알림 발송
    
    Note: load_policies 커맨드의 update_or_create()에서도 호출됨
          created=True일 때만 알림 발송 (업데이트 시 발송 안함)
    """
    if not created:
        return
    
    logger.info(f"[시그널] 신규 정책 감지: {instance.title}")
    
    try:
        stats = notify_matching_users(instance)
        logger.info(f"[시그널] 알림 발송 완료: 성공 {stats['sent']}, 스킵 {stats['skipped']}, 실패 {stats['failed']}")
    except Exception as e:
        logger.error(f"[시그널] 알림 발송 중 오류: {e}")
