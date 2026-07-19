"""Repair-history ingestion: load past repairs, index in Qdrant for reuse."""

import json
from pathlib import Path

from torq.config import settings
from torq.ingest import index_docs


def _record_to_text(r: dict) -> str:
    """Flatten a repair record into a searchable document."""
    return (
        f"Machine {r.get('machine')} fault {r.get('fault_code')}: "
        f"symptom: {r.get('symptom')} "
        f"root cause: {r.get('root_cause')} "
        f"fix: {r.get('fix')} "
        f"notes: {r.get('technician_notes')}"
    )


def ingest_history(history_file: Path | None = None) -> int:
    """Index every repair record. Returns record count."""
    history_file = history_file or settings.history_file
    if not history_file.exists():
        return 0
    records = json.loads(history_file.read_text(encoding="utf-8"))
    docs = [_record_to_text(r) for r in records]
    payloads = [dict(r) for r in records]
    return index_docs(settings.history_collection, docs, payloads)


def upsert_history_record(record: dict) -> None:
    """Index a single repair record."""
    from torq.ingest import upsert_document
    doc = _record_to_text(record)
    doc_id = record.get("id") or "WO-unknown"
    upsert_document(settings.history_collection, doc_id, doc, record)


if __name__ == "__main__":
    print(f"Indexed {ingest_history()} repair records.")
