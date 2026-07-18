"""Prompt templates for fault diagnosis."""

SYSTEM = (
    "You are a maintenance diagnosis engine for industrial machines. "
    "Given a fault code and retrieved OEM manual excerpts plus past repair "
    "history, identify the most likely root cause and a concrete repair plan. "
    "Ground every claim in the provided context; do not invent part numbers. "
    "Reply with ONE JSON object only, no prose, no markdown fences, matching:\n"
    '{"root_cause": str, "confidence": float 0-1, "repair_steps": [str], '
    '"parts": [str], "tools": [str], "safety_warnings": [str], "sources": [str]}'
)


def build_user_prompt(
    fault_code: str, machine: str, context: str, manuals: str, history: str
) -> str:
    return (
        f"FAULT CODE: {fault_code}\n"
        f"MACHINE: {machine or 'unknown'}\n"
        f"SITUATION: {context or 'n/a'}\n\n"
        f"=== OEM MANUAL EXCERPTS ===\n{manuals or 'none'}\n\n"
        f"=== PAST REPAIRS ON SIMILAR FAULTS ===\n{history or 'none'}\n\n"
        "Produce the JSON diagnosis now. Put the manual/repair sources you used "
        "in the 'sources' field."
    )
