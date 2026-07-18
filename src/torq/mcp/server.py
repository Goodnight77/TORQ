"""MCP server exposing plant-local OEM manuals and repair history as tools.

Runs over stdio so an MCP client (the agent, Claude Desktop, etc.) can query
plant knowledge without the proprietary data leaving the local network.

Run:  uv run python -m torq.mcp.server
"""

from mcp.server.fastmcp import FastMCP

from torq.mcp import connectors

mcp = FastMCP("torq-knowledge")


@mcp.tool()
def search_manuals(query: str, limit: int = 4) -> list[dict]:
    """Search the plant's OEM manuals for text relevant to a fault or symptom."""
    return connectors.search_manuals(query, limit)


@mcp.tool()
def search_history(query: str, limit: int = 4, machine: str = "") -> list[dict]:
    """Search past repair records for fixes to similar faults."""
    return connectors.search_history(query, limit, machine=machine)


if __name__ == "__main__":
    mcp.run()
