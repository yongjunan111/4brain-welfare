"""MCP RAG 서버 스모크 테스트."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


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

        rewritten = await rewrite.ainvoke({"query": "월세 도와줘"})
        print(f"rewrite_query -> {rewritten}")

        search_result = await search.ainvoke({"query": rewritten, "top_k": 3})
        print(f"search_policies -> {len(search_result)}건")

        rag_result = await rag.ainvoke({"query": "청년 취업 지원", "top_k": 3})
        print(f"rag_pipeline -> {rag_result.get('result_count', 0)}건")

        print("MCP 스모크 테스트 성공")
        return 0
    finally:
        if hasattr(client, "aclose"):
            await client.aclose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
