"""MCP client helpers: call the torq-knowledge MCP server over stdio.

Each public function spawns a short-lived MCP session (the server runs as a
subprocess), calls one tool, and returns the parsed result.  If *anything* goes
wrong (server not found, timeout, malformed response) the function returns
``None`` so the caller can fall back to a direct retrieval path.

ponytail: one subprocess per call, so every call cold-loads the embedding models
in the server. Fine for a demo; if latency bites, hold one long-lived session
open (background thread + loop) and reuse it across calls.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from torq.config import settings

log = logging.getLogger(__name__)


def mcp_available() -> bool:
    """Whether MCP retrieval is usable.

    Needs a networked Qdrant (``qdrant_url``): the embedded on-disk store is
    single-process (file-locked), so the server subprocess cannot open the same
    store while the parent holds the lock; MCP would then silently and
    permanently fall back to direct. With no ``qdrant_url`` the caller retrieves
    directly instead.
    """
    return settings.use_mcp and bool(settings.qdrant_url)


def _server_params() -> StdioServerParameters:
    """Build stdio launch parameters from config."""
    return StdioServerParameters(
        command=settings.mcp_server_command,
        args=settings.mcp_server_args,
    )


def _extract_list(result: Any) -> list[dict]:
    """Pull the list payload out of a CallToolResult.

    FastMCP serializes a ``list[dict]`` return as
    ``structuredContent={"result": [...]}`` and, separately, as one TextContent
    block *per item* (so ``content[0]`` is only the first record - never parse
    just that). Prefer the structured payload; rebuild from the blocks otherwise.
    """
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    return [json.loads(c.text) for c in result.content]  # type: ignore[union-attr]


async def _call_tool(name: str, arguments: dict[str, Any]) -> list[dict] | None:
    """Open a stdio MCP session, call *name*, and return the parsed JSON list."""
    try:
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                if result.isError:
                    log.warning("MCP tool %s returned an error: %s", name, result.content)
                    return None
                return _extract_list(result)
    except Exception:  # noqa: BLE001 — any failure → caller falls back
        log.warning("MCP call to '%s' failed, will fall back to direct retrieval", name, exc_info=True)
        return None


def _run(coro):
    """Run an async coroutine from sync code, handling an already-running loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # We're inside an existing event loop (e.g. FastAPI).
        # Create a new loop in a thread to avoid nested-run errors.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


# ── Public sync API ──────────────────────────────────────────────────────────


def mcp_search_manuals(query: str, limit: int = 4) -> list[dict] | None:
    """Search manuals via MCP.  Returns ``None`` on any failure."""
    return _run(_call_tool("search_manuals", {"query": query, "limit": limit}))


def mcp_search_history(
    query: str, limit: int = 4, machine: str = ""
) -> list[dict] | None:
    """Search repair history via MCP.  Returns ``None`` on any failure."""
    args: dict[str, Any] = {"query": query, "limit": limit}
    if machine:
        args["machine"] = machine
    return _run(_call_tool("search_history", args))
