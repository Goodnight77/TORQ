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
    """Index a single repair record.

    Dedup-on-write: if a near-identical repair for the same machine + fault code
    already exists, merge into it (bump `times_seen`, refresh `updated_at`) instead
    of adding another near-duplicate point. A record re-indexing under its own id
    still updates in place (handled by upsert_document's stable id)."""
    from datetime import datetime, timezone

    from torq.ingest import _point_id, merge_payload, nearest_dense, upsert_document

    doc = _record_to_text(record)
    doc_id = record.get("id") or "WO-unknown"

    if settings.use_dedup:
        hit = nearest_dense(
            settings.history_collection,
            doc,
            {"machine": record.get("machine"), "fault_code": record.get("fault_code")},
        )
        if hit and hit[1] >= settings.dedup_threshold and str(hit[0]) != str(_point_id(doc_id)):
            pid, _score, payload = hit
            merge_payload(
                settings.history_collection,
                pid,
                {
                    "times_seen": int(payload.get("times_seen", 1)) + 1,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

    upsert_document(settings.history_collection, doc_id, doc, record)


if __name__ == "__main__":
    print(f"Indexed {ingest_history()} repair records.")
