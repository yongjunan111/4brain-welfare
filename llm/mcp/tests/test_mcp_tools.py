"""MCP 도구 단위 테스트."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from llm.mcp.tools.rag_pipeline import rag_pipeline_tool
from llm.mcp.tools.search import search_policies_tool


class SearchPoliciesToolTests(unittest.TestCase):
    @patch("llm.mcp.tools.search._fetch_policies_by_ids")
    @patch("llm.mcp.tools.search._run_search_docs")
    def test_search_policies_tool_merges_retrieval_order(self, mock_run_search_docs, mock_fetch_policies_by_ids):
        # retriever/reranker 순서: P2 -> P1
        mock_run_search_docs.return_value = [
            SimpleNamespace(
                metadata={"plcyNo": "P2", "plcyNm": "정책2", "rerank_score": 0.95},
                page_content="정책2 내용",
            ),
            SimpleNamespace(
                metadata={"plcyNo": "P1", "plcyNm": "정책1", "rerank_score": 0.88},
                page_content="정책1 내용",
            ),
        ]
        mock_fetch_policies_by_ids.return_value = {
            "P1": {"policy_id": "P1", "title": "DB정책1", "full_text": "DB1", "source": "postgres"},
            "P2": {"policy_id": "P2", "title": "DB정책2", "full_text": "DB2", "source": "postgres"},
        }

        result = search_policies_tool(query="청년 주거", top_k=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["policy_id"], "P2")
        self.assertEqual(result[1]["policy_id"], "P1")
        self.assertEqual(result[0]["source"], "postgres")

    @patch("llm.mcp.tools.search._fetch_policies_by_ids")
    @patch("llm.mcp.tools.search._run_search_docs")
    def test_search_policies_tool_falls_back_when_postgres_miss(self, mock_run_search_docs, mock_fetch_policies_by_ids):
        mock_run_search_docs.return_value = [
            SimpleNamespace(
                metadata={
                    "plcyNo": "P404",
                    "plcyNm": "메타 정책",
                    "plcySprtCn": "메타 지원",
                    "aplyUrlAddr": "https://example.com",
                },
                page_content="메타 본문",
            ),
        ]
        mock_fetch_policies_by_ids.return_value = {}

        result = search_policies_tool(query="청년", top_k=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["policy_id"], "P404")
        self.assertEqual(result[0]["source"], "retriever_fallback")


class RagPipelineToolTests(unittest.TestCase):
    @patch("llm.mcp.tools.rag_pipeline.search_policies_tool")
    @patch("llm.mcp.tools.rag_pipeline.rewrite_query_tool")
    def test_rag_pipeline_runs_rewrite_then_search(self, mock_rewrite_query_tool, mock_search_policies_tool):
        mock_rewrite_query_tool.return_value = "청년 주거 지원"
        mock_search_policies_tool.return_value = [{"policy_id": "P1", "title": "정책1"}]

        result = rag_pipeline_tool(query="월세 도와줘", top_k=3)

        mock_rewrite_query_tool.assert_called_once_with("월세 도와줘")
        mock_search_policies_tool.assert_called_once_with(
            query="청년 주거 지원",
            top_k=3,
        )
        self.assertEqual(result["rewritten_query"], "청년 주거 지원")
        self.assertEqual(result["result_count"], 1)


if __name__ == "__main__":
    unittest.main()
