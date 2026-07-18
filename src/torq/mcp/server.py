"""MCP server for on-premise knowledge.

Exposes plant-local OEM manuals and repair history as MCP tools/resources so
the agent can query them; data never leaves the plant network.
"""

# TODO: define MCP server with tools: search_manuals, search_history
# TODO: expose resources for manual sections and history records
# TODO: back tools with connectors from mcp.connectors
# TODO: enforce on-premise-only access boundaries
