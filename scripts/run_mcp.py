"""MCP check: connect to the TORQ MCP server over stdio and call its tools.

Proves plant knowledge is reachable through MCP (the on-premise trust boundary).
Run:  uv run python scripts/run_mcp.py
"""

import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(command=sys.executable, args=["-m", "torq.mcp.server"])


async def main() -> None:
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = [t.name for t in (await session.list_tools()).tools]
            print("MCP tools:", tools)
            assert {"search_manuals", "search_history"} <= set(tools), "tools missing"

            man = await session.call_tool("search_manuals", {"query": "E-471 overtemperature", "limit": 2})
            hist = await session.call_tool("search_history", {"query": "E-471 lint", "limit": 2})

            man_rows = man.structuredContent.get("result", []) if man.structuredContent else []
            hist_rows = hist.structuredContent.get("result", []) if hist.structuredContent else []
            print(f"\nsearch_manuals -> {len(man_rows)} hits")
            for r in man_rows:
                print(f"  [{r.get('source')}] {r.get('text','')[:80]}...")
            print(f"\nsearch_history -> {len(hist_rows)} hits")
            for r in hist_rows:
                print(f"  [{r.get('id')}] {r.get('fault_code')}: {r.get('fix')}")

            assert man_rows, "no manual hits via MCP"
    print("\nMCP server reachable; plant knowledge served over MCP. ✅")


if __name__ == "__main__":
    asyncio.run(main())
