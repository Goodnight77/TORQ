"""Diagnosis agent.

Reads a fault code plus retrieved manual/history context (via MCP) and
produces a structured root-cause analysis with a recommended fix.
"""

# TODO: build agent with access to MCP manual/history tools
# TODO: assemble prompt from agent.prompts with fault + retrieved context
# TODO: invoke LLM and parse into a DiagnosisResult schema
# TODO: handle low-confidence / no-context graceful fallbacks
