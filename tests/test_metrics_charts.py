"""Trend + faults-per-machine aggregation, and diagnosis latency semantics."""

from unittest.mock import patch

from torq.agent.schemas import WorkOrder
from torq.db import models


def _wo(**kw):
    base = dict(id=kw.pop("id", "x"), fault_code="E-201", machine="CM-350", root_cause="rc")
    base.update(kw)
    return WorkOrder(**base)


SAMPLE = [
    _wo(id="a", machine="CM-350", fault_arrived_at="2026-07-18T10:00:00+00:00",
        created_at="2026-07-18T10:00:20+00:00", status="resolved",
        outcome={"time_to_fix_min": 30}),
    _wo(id="b", machine="Pump 3", fault_arrived_at="2026-07-18T11:00:00+00:00",
        created_at="2026-07-18T11:00:40+00:00", status="pending"),
    _wo(id="c", machine="CM-350", fault_arrived_at="2026-07-19T09:00:00+00:00",
        created_at="2026-07-19T09:00:10+00:00", status="resolved",
        outcome={"time_to_fix_min": 50}),
]


@patch("torq.db.models.list_all", return_value=SAMPLE)
def test_faults_per_machine_counts_and_orders(_):
    fpm = models.faults_per_machine()
    assert fpm[0] == {"machine": "CM-350", "count": 2}  # most first
    assert {"machine": "Pump 3", "count": 1} in fpm


@patch("torq.db.models.list_all", return_value=SAMPLE)
def test_trend_buckets_by_day(_):
    rows = models.trend()
    assert [r["label"] for r in rows] == ["07-18", "07-19"]
    # diagnosis is fault->created latency in minutes (20s/40s avg = 0.5 on day 1)
    assert rows[0]["diagnosis"] == 0.5
    assert rows[0]["mttr"] == 30.0  # only the resolved one counts
    assert rows[1]["mttr"] == 50.0
