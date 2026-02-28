"""
복지나침반 도구 모음

오케스트레이터가 호출할 수 있는 도구들
"""

from typing import Optional

from langchain_core.tools import BaseTool

from .check_eligibility import PolicyFetcher, create_check_eligibility
from .extract_info import extract_info
from .rewrite_query import rewrite_query
from .search_policies import search_policies


def _default_policy_fetcher(_policy_ids: Optional[list[str]]) -> list[dict]:
    """기본 policy fetcher (개발/테스트용)."""
    return []


def create_tools(policy_fetcher: PolicyFetcher | None = None) -> list[BaseTool]:
    """policy_fetcher를 주입받아 도구 리스트를 생성한다."""
    fetcher = policy_fetcher or _default_policy_fetcher
    check_eligibility_tool = create_check_eligibility(fetcher)
    return [extract_info, search_policies, check_eligibility_tool]


# 하위호환: 기본 fetcher로 생성된 정적 도구
ALL_TOOLS = create_tools()
check_eligibility = ALL_TOOLS[2]


__all__ = [
    "extract_info",
    "rewrite_query", 
    "search_policies",
    "create_tools",
    "check_eligibility",
    "ALL_TOOLS",
]
