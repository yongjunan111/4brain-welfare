from __future__ import annotations

import logging
import os
from contextlib import contextmanager, nullcontext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

_LANGFUSE_ENABLED = None  # lazy cache


def _is_langfuse_enabled() -> bool:
    global _LANGFUSE_ENABLED
    if _LANGFUSE_ENABLED is None:
        _LANGFUSE_ENABLED = bool(
            os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY")
        )
    return _LANGFUSE_ENABLED


def get_langfuse_handler(
    session_id: str | None = None,
    user_id: str | None = None,
) -> "CallbackHandler | None":
    """
    LangFuse CallbackHandler 생성.

    환경변수(LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY)가 없으면 None 반환 (graceful degradation).

    Args:
        session_id: LangFuse 세션 ID — langfuse_session()으로 전파 필요 (v4)
        user_id: LangFuse 사용자 ID

    Returns:
        CallbackHandler | None
    """
    if not _is_langfuse_enabled():
        return None

    try:
        from langfuse.langchain import CallbackHandler

        # v4: secret_key/host는 환경변수에서 자동으로 읽힘
        # session_id는 langfuse_session() context manager로 전파
        return CallbackHandler()
    except Exception:
        logger.warning("LangFuse CallbackHandler 생성 실패 — tracing 비활성화", exc_info=True)
        return None


@contextmanager
def langfuse_session(session_id: str | None = None):
    """
    LangFuse session_id를 하위 모든 trace에 전파하는 context manager.

    v4에서 session_id는 propagate_attributes()로 설정해야 합니다.

    Usage:
        with langfuse_session(session_id="thread-123"):
            result = agent.invoke(inputs, config=config)
    """
    if not session_id or not _is_langfuse_enabled():
        yield
        return

    try:
        from langfuse import get_client, propagate_attributes

        langfuse = get_client()
        with langfuse.start_as_current_observation(as_type="span", name="agent-run"):
            with propagate_attributes(session_id=session_id):
                yield
    except Exception:
        logger.warning("LangFuse session 설정 실패 — session 없이 진행", exc_info=True)
        yield
