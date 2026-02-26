"""Search backend adapters for the `search_policies` tool."""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from langchain_core.documents import Document

from .rewrite_query import rewrite_query_internal

DEFAULT_TOP_K = 10
MAX_TOP_K = 20

logger = logging.getLogger(__name__)


def _normalize_top_k(top_k: int) -> int:
    """Normalize top_k to the supported range."""
    try:
        parsed = int(top_k)
    except (TypeError, ValueError):
        parsed = DEFAULT_TOP_K
    return min(max(1, parsed), MAX_TOP_K)


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse a boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _compose_full_text(title: str, description: str, support_content: str) -> str:
    parts = [title.strip(), description.strip(), support_content.strip()]
    return "\n\n".join(part for part in parts if part)


def _doc_to_policy(doc: Document) -> dict[str, Any]:
    """Convert a LangChain Document to MCP-canonical policy dict."""
    metadata = doc.metadata or {}
    title = metadata.get("plcyNm", "")
    description = (doc.page_content or "")[:1200]
    support_content = metadata.get("plcySprtCn", "")

    return {
        "policy_id": (metadata.get("plcyNo") or "").strip(),
        "title": title,
        "description": description,
        "support_content": support_content,
        "apply_method": "",
        "apply_url": metadata.get("aplyUrlAddr", ""),
        "district": metadata.get("region", ""),
        "category": metadata.get("lclsfNm", ""),
        "subcategory": metadata.get("mclsfNm", ""),
        "age_min": metadata.get("minAge"),
        "age_max": metadata.get("maxAge"),
        "income_level": metadata.get("earnCndSeCd", ""),
        "apply_start_date": None,
        "apply_end_date": None,
        "business_start_date": None,
        "business_end_date": None,
        "full_text": _compose_full_text(title, description, support_content),
        "retrieval_score": metadata.get("score"),
        "rerank_score": metadata.get("rerank_score"),
        "source": "direct_retriever",
    }


class SearchBackend(Protocol):
    """Search backend protocol for adapter switching."""

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
        """Run policy search and return normalized result payload."""


class DirectSearchBackend:
    """Local search backend using retriever modules directly."""

    def __init__(self, use_reranker: bool | None = None) -> None:
        self.use_reranker = (
            _parse_bool_env("USE_RERANKER", True)
            if use_reranker is None
            else use_reranker
        )

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
        """Search policies with local retrievers."""
        original_query = (query or "").strip()
        if not original_query:
            return {
                "original_query": "",
                "rewritten_query": "",
                "result_count": 0,
                "policies": [],
            }

        normalized_top_k = _normalize_top_k(top_k)
        rewritten_query = (rewrite_query_internal(original_query) or "").strip() or original_query
        docs = self._search_docs(query=rewritten_query, top_k=normalized_top_k)
        policies = [_doc_to_policy(doc) for doc in docs][:normalized_top_k]

        return {
            "original_query": original_query,
            "rewritten_query": rewritten_query,
            "result_count": len(policies),
            "policies": policies,
        }

    def _search_docs(self, query: str, top_k: int) -> list[Document]:
        if self.use_reranker:
            return self._search_with_bge(query=query, top_k=top_k)
        return self._search_without_reranker(query=query, top_k=top_k)

    def _search_with_bge(self, query: str, top_k: int) -> list[Document]:
        try:
            from llm.embeddings.ensemble_retriever_bge import ensemble_search_with_bge

            docs = ensemble_search_with_bge(
                query=query,
                top_k=top_k,
                return_metadata=False,
                verbose=False,
            )
            return list(docs or [])
        except Exception:
            logger.error("DirectSearchBackend BGE search failed", exc_info=True)
            return []

    def _search_without_reranker(self, query: str, top_k: int) -> list[Document]:
        try:
            from llm.embeddings.ensemble_retriever import ensemble_search

            docs = ensemble_search(
                query=query,
                k=top_k,
                use_reranker=False,
                verbose=False,
            )
            return list(docs or [])
        except Exception:
            logger.error("DirectSearchBackend non-reranked search failed", exc_info=True)
            return []


class MCPSearchBackend:
    """MCP search adapter placeholder."""

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
        raise NotImplementedError("MCPSearchBackend is not implemented yet.")


def get_search_backend() -> SearchBackend:
    """Resolve backend from SEARCH_BACKEND env (default: direct)."""
    backend_name = (os.getenv("SEARCH_BACKEND") or "direct").strip().lower()

    if backend_name == "mcp":
        return MCPSearchBackend()
    if backend_name != "direct":
        logger.warning("Unknown SEARCH_BACKEND=%s. Falling back to direct.", backend_name)
    return DirectSearchBackend()
