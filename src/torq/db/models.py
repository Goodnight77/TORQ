"""Work-order persistence (SQLite). Stores each WorkOrder as JSON + a status column."""

from datetime import datetime

from torq.agent.schemas import WorkOrder
from torq.db.session import get_conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS work_orders (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                machine TEXT,
                fault_code TEXT,
                assigned_to TEXT,
                data TEXT NOT NULL
            )
            """
        )


def save(wo: WorkOrder) -> None:
    with get_conn() as conn:
        conn.execute(
            "REPLACE INTO work_orders (id, status, machine, fault_code, assigned_to, data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (wo.id, wo.status, wo.machine, wo.fault_code, wo.assigned_to, wo.model_dump_json()),
        )


def get(wo_id: str) -> WorkOrder | None:
    with get_conn() as conn:
        row = conn.execute("SELECT data FROM work_orders WHERE id = ?", (wo_id,)).fetchone()
    return WorkOrder.model_validate_json(row["data"]) if row else None


def list_by_status(status: str) -> list[WorkOrder]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT data FROM work_orders WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
    return [WorkOrder.model_validate_json(r["data"]) for r in rows]


def list_all() -> list[WorkOrder]:
    with get_conn() as conn:
        rows = conn.execute("SELECT data FROM work_orders ORDER BY rowid").fetchall()
    return [WorkOrder.model_validate_json(r["data"]) for r in rows]


def _secs(start: str, end: str) -> float | None:
    try:
        return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    except (TypeError, ValueError):
        return None


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 1) if xs else None


def metrics() -> dict:
    """Downtime metrics for the dashboard (the measured-impact numbers)."""
    wos = list_all()
    by_status: dict[str, int] = {}
    for w in wos:
        by_status[w.status] = by_status.get(w.status, 0) + 1

    ttd = [s for w in wos if (s := _secs(w.created_at, w.dispatched_at)) is not None]
    resolved = [w for w in wos if w.status == "resolved"]
    ttf = [
        w.outcome["time_to_fix_min"]
        for w in resolved
        if w.outcome and w.outcome.get("time_to_fix_min") is not None
    ]
    return {
        "total_work_orders": len(wos),
        "by_status": by_status,
        "avg_time_to_diagnosis_sec": _avg(ttd),
        "avg_time_to_fix_min": _avg(ttf),
        "resolved": len(resolved),
        "resolution_rate": round(len(resolved) / len(wos), 2) if wos else None,
    }
