"""Capture a technician's repair outcome and feed it back into the knowledge base."""

import json

from torq.agent.schemas import WorkOrder, _now
from torq.config import settings
from torq.db import models
from torq.ingest.history import ingest_history


def _append_to_history(wo: WorkOrder) -> None:
    """Add the resolved work order to the repair-history file and re-index it,
    so future diagnoses of the same fault can retrieve this fix."""
    o = wo.outcome or {}
    record = {
        "id": f"WO-{wo.id}",
        "machine": wo.machine,
        "fault_code": wo.fault_code,
        "date": (wo.resolved_at or _now())[:10],
        "symptom": wo.root_cause,
        "root_cause": wo.root_cause,
        "fix": o.get("actual_fix") or " ".join(wo.repair_steps[:2]),
        "technician_notes": o.get("notes", ""),
        "outcome": "resolved" if o.get("resolved") else "unresolved",
        "time_to_fix_min": o.get("time_to_fix_min"),
    }
    path = settings.history_file
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    records.append(record)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    ingest_history()  # re-embed history so the new fix is retrievable


def record_outcome(
    wo_id: str,
    resolved: bool,
    actual_fix: str = "",
    notes: str = "",
    time_to_fix_min: float | None = None,
) -> WorkOrder | None:
    wo = models.get(wo_id)
    if not wo:
        return None
    wo.outcome = {
        "resolved": resolved,
        "actual_fix": actual_fix,
        "notes": notes,
        "time_to_fix_min": time_to_fix_min,
    }
    wo.resolved_at = _now()
    wo.status = "resolved" if resolved else "failed"
    models.save(wo)
    if resolved:
        _append_to_history(wo)
    return wo
