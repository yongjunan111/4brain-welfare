"""Tests for search backend adapter and search_policies tool."""

from __future__ import annotations

import os
import importlib
from unittest.mock import patch

import pytest
from langchain_core.documents import Document


def _make_doc(idx: int = 1) -> Document:
    return Document(
        page_content=f"정책 본문 {idx}",
        metadata={
            "plcyNo": f"P{idx}",
            "plcyNm": f"정책{idx}",
            "plcySprtCn": f"지원내용{idx}",
            "minAge": 19,
            "maxAge": 39,
            "region": "서울특별시",
            "earnCndSeCd": "0043001",
            "aplyYmd": "20240101~20261231",
            "aplyUrlAddr": f"https://example.com/{idx}",
            "lclsfNm": "주거",
            "mclsfNm": "월세",
            "score": 0.91,
            "rerank_score": 0.87,
        },
    )


class TestBackendSelector:
    def test_get_search_backend_default_direct(self, monkeypatch):
        monkeypatch.delenv("SEARCH_BACKEND", raising=False)

        from llm.agents.tools.search_backend import DirectSearchBackend, get_search_backend

        backend = get_search_backend()
        assert isinstance(backend, DirectSearchBackend)

    def test_get_search_backend_mcp(self, monkeypatch):
        monkeypatch.setenv("SEARCH_BACKEND", "mcp")

        from llm.agents.tools.search_backend import MCPSearchBackend, get_search_backend

        backend = get_search_backend()
        assert isinstance(backend, MCPSearchBackend)

    def test_all_tools_excludes_rewrite_query(self):
        from llm.agents.tools import ALL_TOOLS

        tool_names = [getattr(tool, "name", "") for tool in ALL_TOOLS]
        assert "rewrite_query" not in tool_names


class TestDirectSearchBackend:
    def test_empty_query_returns_no_results(self):
        from llm.agents.tools.search_backend import DirectSearchBackend

        backend = DirectSearchBackend(use_reranker=True)
        result = backend.search("   ", top_k=5)

        assert result["result_count"] == 0
        assert result["policies"] == []

    @patch("llm.agents.tools.search_backend.rewrite_query_internal", return_value="청년 주거 지원")
    def test_reranker_on_path(self, _mock_rewrite):
        from llm.agents.tools.search_backend import DirectSearchBackend

        backend = DirectSearchBackend(use_reranker=True)

        with patch.object(backend, "_search_with_bge", return_value=[_make_doc(1)]) as mock_bge, patch.object(
            backend,
            "_search_without_reranker",
            return_value=[],
        ) as mock_no_rerank:
            result = backend.search("월세 지원", top_k=3)

        mock_bge.assert_called_once_with(query="청년 주거 지원", top_k=3)
        mock_no_rerank.assert_not_called()
        assert result["result_count"] == 1
        assert result["policies"][0]["policy_id"] == "P1"

    @patch("llm.agents.tools.search_backend.rewrite_query_internal", return_value="청년 취업 지원")
    def test_reranker_off_path(self, _mock_rewrite):
        from llm.agents.tools.search_backend import DirectSearchBackend

        backend = DirectSearchBackend(use_reranker=False)

        with patch.object(backend, "_search_without_reranker", return_value=[_make_doc(2)]) as mock_no_rerank, patch.object(
            backend,
            "_search_with_bge",
            return_value=[],
        ) as mock_bge:
            result = backend.search("취업 지원", top_k=2)

        mock_no_rerank.assert_called_once_with(query="청년 취업 지원", top_k=2)
        mock_bge.assert_not_called()
        assert result["result_count"] == 1
        assert result["policies"][0]["title"] == "정책2"

    @patch("llm.agents.tools.search_backend.rewrite_query_internal", return_value="청년 주거")
    def test_top_k_is_clamped(self, _mock_rewrite):
        from llm.agents.tools.search_backend import DirectSearchBackend

        backend = DirectSearchBackend(use_reranker=True)
        docs = [_make_doc(i) for i in range(1, 35)]

        with patch.object(backend, "_search_with_bge", return_value=docs):
            result = backend.search("월세", top_k=999)

        assert result["result_count"] == 20
        assert len(result["policies"]) == 20

    def test_use_reranker_from_env(self, monkeypatch):
        from llm.agents.tools.search_backend import DirectSearchBackend

        monkeypatch.setenv("USE_RERANKER", "0")
        backend_off = DirectSearchBackend()
        assert backend_off.use_reranker is False

        monkeypatch.setenv("USE_RERANKER", "1")
        backend_on = DirectSearchBackend()
        assert backend_on.use_reranker is True


class TestSearchPoliciesTool:
    def test_format_no_results(self):
        from llm.agents.tools.search_policies import _format_for_orchestrator

        text = _format_for_orchestrator(
            {
                "original_query": "월세",
                "rewritten_query": "청년 월세",
                "result_count": 0,
                "policies": [],
            }
        )
        assert text == "검색 결과 없음"

    def test_search_policies_formats_backend_result(self, monkeypatch):
        from llm.agents.tools.search_policies import search_policies
        search_module = importlib.import_module("llm.agents.tools.search_policies")

        class DummyBackend:
            def __init__(self):
                self.calls = []

            def search(self, query: str, top_k: int = 10):
                self.calls.append((query, top_k))
                return {
                    "original_query": query,
                    "rewritten_query": "청년 월세 지원",
                    "result_count": 1,
                    "policies": [
                        {
                            "policy_id": "P100",
                            "title": "청년월세지원",
                            "description": "월세를 지원합니다",
                            "category": "주거",
                            "district": "서울특별시",
                            "age_min": 19,
                            "age_max": 39,
                            "apply_url": "https://example.com/p100",
                        }
                    ],
                }

        backend = DummyBackend()
        monkeypatch.setattr(search_module, "get_search_backend", lambda: backend)

        result = search_policies.invoke({"query": "월세", "top_k": 100})

        assert "검색 결과: 1건" in result
        assert "청년월세지원" in result
        assert "https://example.com/p100" in result
        assert backend.calls[0] == ("월세", 20)

    def test_search_policies_returns_no_result_message(self, monkeypatch):
        from llm.agents.tools.search_policies import search_policies
        search_module = importlib.import_module("llm.agents.tools.search_policies")

        class DummyBackend:
            def search(self, query: str, top_k: int = 10):
                return {
                    "original_query": query,
                    "rewritten_query": query,
                    "result_count": 0,
                    "policies": [],
                }

        monkeypatch.setattr(search_module, "get_search_backend", lambda: DummyBackend())

        result = search_policies.invoke({"query": "없는 정책", "top_k": 5})
        assert result == "검색 결과 없음"


needs_openai_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)

needs_chroma_db = pytest.mark.skipif(
    not os.path.exists("data/chroma_db"),
    reason="local Chroma DB not found",
)


@pytest.mark.integration
@needs_openai_key
@needs_chroma_db
def test_integration_direct_backend_calls_local_ensemble(monkeypatch):
    """Integration test: run direct backend against local ensemble stack."""
    from llm.agents.tools.search_backend import DirectSearchBackend

    # Keep integration focused on retriever path, not LLM rewrite quality.
    monkeypatch.setenv("USE_RERANKER", "0")

    with patch("llm.agents.tools.search_backend.rewrite_query_internal", return_value="청년 월세 지원"):
        backend = DirectSearchBackend()
        result = backend.search("월세 지원", top_k=2)

    assert isinstance(result, dict)
    assert result["original_query"] == "월세 지원"
    assert "policies" in result
    assert result["result_count"] <= 2
