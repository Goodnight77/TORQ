"""Persistence for work orders and the machine registry."""

import json
from datetime import datetime
from typing import Any

from torq.agent.schemas import WorkOrder
from torq.config import settings
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS machines (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                location TEXT NOT NULL
            )
            """
        )
        for machine in _demo_machines():
            conn.execute(
                "INSERT INTO machines (id, model, location) VALUES (?, ?, ?) "
                "ON CONFLICT (id) DO NOTHING",
                (machine["id"], machine["model"], machine["location"]),
            )


def _demo_machines() -> list[dict[str, str]]:
    """Build the initial registry from the machines used by demo scenarios."""
    try:
        scenarios = json.loads(settings.scenarios_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    machines: dict[str, dict[str, str]] = {}
    for scenario in scenarios:
        machine_id = str(scenario.get("machine", "")).strip()
        if not machine_id or machine_id in machines:
            continue
        model, separator, line = machine_id.rpartition(" Line ")
        machines[machine_id] = {
            "id": machine_id,
            "model": model if separator else machine_id,
            "location": f"Line {line}" if separator else "",
        }
    return list(machines.values())


def create_machine(machine_id: str, model: str, location: str) -> bool:
    """Add a machine, returning false when its ID is already registered."""
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO machines (id, model, location) VALUES (?, ?, ?) "
            "ON CONFLICT (id) DO NOTHING",
            (machine_id, model, location),
        )
    return cursor.rowcount == 1


def get_machine(machine_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, model, location FROM machines WHERE id = ?", (machine_id,)
        ).fetchone()
    return dict(row) if row else None


def list_machines() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, model, location FROM machines ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


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


def _secs(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    try:
        return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    except ValueError:
        return None


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 1) if xs else None


def _downtime_min(wo: WorkOrder) -> float | None:
    """Return a completed outage duration, preferring the technician's value."""
    recorded = (wo.outcome or {}).get("time_to_fix_min")
    if isinstance(recorded, (int, float)) and not isinstance(recorded, bool):
        return float(recorded)
    elapsed = _secs(wo.created_at, wo.resolved_at)
    return elapsed / 60 if elapsed is not None else None


def metrics() -> dict:
    """Downtime metrics for the dashboard (the measured-impact numbers)."""
    wos = list_all()
    by_status: dict[str, int] = {}
    for w in wos:
        by_status[w.status] = by_status.get(w.status, 0) + 1

    ttd = [s for w in wos if (s := _secs(w.created_at, w.dispatched_at)) is not None]
    resolved = [w for w in wos if w.status == "resolved"]
    ttf = [
        float(w.outcome["time_to_fix_min"])
        for w in resolved
        if w.outcome
        and isinstance(w.outcome.get("time_to_fix_min"), (int, float))
        and not isinstance(w.outcome.get("time_to_fix_min"), bool)
    ]

    machine_rows = {machine["id"]: machine for machine in list_machines()}
    downtime_by_machine: dict[str, float] = {machine_id: 0.0 for machine_id in machine_rows}
    work_orders_by_machine: dict[str, int] = {machine_id: 0 for machine_id in machine_rows}
    for wo in wos:
        if not wo.machine:
            continue
        if wo.machine not in machine_rows:
            machine_rows[wo.machine] = {
                "id": wo.machine,
                "model": wo.machine,
                "location": "",
            }
            downtime_by_machine[wo.machine] = 0.0
            work_orders_by_machine[wo.machine] = 0
        work_orders_by_machine[wo.machine] += 1
        downtime = _downtime_min(wo)
        if downtime is not None:
            downtime_by_machine[wo.machine] += downtime

    machine_downtime = [
        {
            "machine_id": machine_id,
            "model": machine["model"],
            "location": machine["location"],
            "work_orders": work_orders_by_machine[machine_id],
            "downtime_min": round(downtime_by_machine[machine_id], 1),
        }
        for machine_id, machine in sorted(machine_rows.items())
    ]
    return {
        "total_work_orders": len(wos),
        "by_status": by_status,
        "avg_time_to_diagnosis_sec": _avg(ttd),
        "avg_time_to_fix_min": _avg(ttf),
        "resolved": len(resolved),
        "resolution_rate": round(len(resolved) / len(wos), 2) if wos else None,
        "machine_downtime": machine_downtime,
    }
