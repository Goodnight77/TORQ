"""Work-order persistence (SQLite). Stores each WorkOrder as JSON + a status column."""

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
