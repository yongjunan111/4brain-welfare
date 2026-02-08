"""MCP RAG 서버 스모크 테스트."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


def _unwrap_mcp_result(value):
    """langchain_mcp_adapters 결과를 기본 파이썬 타입으로 변환."""
    if isinstance(value, list):
        text_chunks = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    text_chunks.append(text)
            elif isinstance(item, str):
                text_chunks.append(item)

        if not text_chunks:
            return value

        joined = "\n".join(chunk for chunk in text_chunks if chunk).strip()
        if not joined:
            return ""
        try:
            return json.loads(joined)
        except json.JSONDecodeError:
            return joined

    return value


async def main() -> int:
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        print("langchain-mcp-adapters 미설치: `uv sync` 후 다시 실행하세요.")
        return 1

    project_root = Path(__file__).resolve().parents[1]
    server_path = project_root / "llm" / "mcp" / "server.py"

    client = MultiServerMCPClient(
        {
            "welfare-rag": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(server_path)],
            }
        }
    )

    try:
        tools = await client.get_tools()
        print(f"도구 로드: {len(tools)}개")
        for tool in tools:
            print(f"  - {tool.name}")

        rewrite = next((t for t in tools if t.name == "rewrite_query"), None)
        search = next((t for t in tools if t.name == "search_policies"), None)
        rag = next((t for t in tools if t.name == "rag_pipeline"), None)

        if not rewrite or not search or not rag:
            print("필수 MCP 도구(rewrite_query/search_policies/rag_pipeline) 누락")
            return 1

        rewritten_raw = await rewrite.ainvoke({"query": "월세 도와줘"})
        rewritten = _unwrap_mcp_result(rewritten_raw)
        if not isinstance(rewritten, str):
            rewritten = str(rewritten)
        print(f"rewrite_query -> {rewritten}")

        search_raw = await search.ainvoke({"query": rewritten, "top_k": 3})
        search_result = _unwrap_mcp_result(search_raw)
        search_count = len(search_result) if isinstance(search_result, list) else 0
        print(f"search_policies -> {search_count}건")

        rag_raw = await rag.ainvoke({"query": "청년 취업 지원", "top_k": 3})
        rag_result = _unwrap_mcp_result(rag_raw)
        rag_count = rag_result.get("result_count", 0) if isinstance(rag_result, dict) else 0
        print(f"rag_pipeline -> {rag_count}건")

        print("MCP 스모크 테스트 성공")
        return 0
    finally:
        if hasattr(client, "aclose"):
            await client.aclose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
