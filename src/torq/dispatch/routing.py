"""Skill-matched routing: pick the best on-shift technician for a work order."""

import json
from pathlib import Path

from torq.agent.schemas import WorkOrder
from torq.config import settings


def _load_roster(shifts_file: Path | None = None) -> list[dict]:
    shifts_file = shifts_file or settings.shifts_file
    if not shifts_file.exists():
        return []
    try:
        return json.loads(shifts_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def choose_technician(wo: WorkOrder, roster: list[dict] | None = None) -> dict | None:
    """Best on-shift technician whose skills cover the required skill.

    Score = skill match first, then fewer skills (more specialised) as a tiebreak.
    """
    roster = roster if roster is not None else _load_roster()
    candidates = [
        t
        for t in roster
        if t.get("on_shift") and wo.required_skill in t.get("skills", [])
    ]
    if not candidates:
        # fall back to any on-shift 'general' tech so a fault is never unassigned
        candidates = [
            t for t in roster if t.get("on_shift") and "general" in t.get("skills", [])
        ]
    if not candidates:
        return None
    return min(candidates, key=lambda t: len(t.get("skills", [])))
