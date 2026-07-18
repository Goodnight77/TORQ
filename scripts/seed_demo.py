"""Seed the store with resolved work orders so the dashboard shows populated metrics.

Run before a demo:  uv run python scripts/seed_demo.py
"""

import sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from torq.agent.schemas import WorkOrder
from torq.db import models

_BASE = datetime.now(timezone.utc) - timedelta(days=2)


def _wo(i, machine, fault, cause, skill, tech, ttd_sec, ttf_min):
    created = _BASE + timedelta(hours=i * 5)
    return WorkOrder(
        id=f"seed{i:02d}",
        fault_code=fault,
        machine=machine,
        root_cause=cause,
        repair_steps=["Lockout/tagout the machine.", "Apply the corrective fix.", "Reset and monitor."],
        parts=["see manual"],
        required_skill=skill,
        content={"en": f"WORK ORDER {machine} fault {fault}: {cause}"},
        status="resolved",
        assigned_to=tech,
        confidence=0.9,
        created_at=created.isoformat(),
        dispatched_at=(created + timedelta(seconds=ttd_sec)).isoformat(),
        resolved_at=(created + timedelta(minutes=ttf_min)).isoformat(),
        outcome={"resolved": True, "actual_fix": cause, "notes": "", "time_to_fix_min": ttf_min},
    )


SEED = [
    _wo(1, "CM-350 Line 2", "E-471", "Clogged intake louvers, lint buildup.", "electromechanical", "Ahmed Ben Salah", 41, 30),
    _wo(2, "CM-350 Line 1", "E-201", "Seized drive-end bearing.", "electromechanical", "Karim Haddad", 38, 85),
    _wo(3, "PK-9 Line 3", "J-108", "Feed roller glazed, low nip pressure.", "packaging", "Sonia Trabelsi", 45, 40),
    _wo(4, "PK-9 Line 3", "J-233", "Failed heater cartridge.", "packaging", "Sonia Trabelsi", 52, 25),
]


def main() -> None:
    models.init_db()
    for wo in SEED:
        models.save(wo)
    m = models.metrics()
    print(f"Seeded {len(SEED)} resolved work orders.")
    print("Dashboard metrics:", m)


if __name__ == "__main__":
    main()
