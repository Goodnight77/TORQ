"""Connectors backing the MCP server: plant-local manual and history retrieval."""

from torq.config import settings
from torq.ingest import search


def search_manuals(query: str, limit: int = 4) -> list[dict]:
    """Return matching OEM manual chunks (source + text)."""
    hits = search(settings.manuals_collection, query, limit)
    return [{"source": h.get("source", "manual"), "text": h.get("document", "")} for h in hits]


def search_history(query: str, limit: int = 4) -> list[dict]:
    """Return matching past repairs (fault, cause, fix, notes)."""
    hits = search(settings.history_collection, query, limit)
    return [
        {
            "id": h.get("id"),
            "machine": h.get("machine"),
            "fault_code": h.get("fault_code"),
            "root_cause": h.get("root_cause"),
            "fix": h.get("fix"),
            "notes": h.get("technician_notes"),
        }
        for h in hits
    ]
