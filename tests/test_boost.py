"""Recency/outcome boost: newer and resolved records should rank ahead of stale
or unresolved ones once semantic scores are close."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from torq.ingest import _boost, _recency


def _pt(payload):
    return SimpleNamespace(payload=payload)


def test_recency_monotonic_and_bounded():
    now = datetime(2026, 7, 18, tzinfo=timezone.utc)
    fresh = _recency("2026-07-18", now)
    old = _recency("2020-01-01", now)
    assert 0.9 <= fresh <= 1.0
    assert 0.0 <= old < fresh
    assert _recency(None, now) == 0.0
    assert _recency("not-a-date", now) == 0.0


def test_boost_promotes_recent_resolved_at_equal_base():
    today = datetime.now(timezone.utc).date().isoformat()
    stale = (datetime.now(timezone.utc) - timedelta(days=2000)).date().isoformat()
    # Same base score; the recent resolved record must come out on top.
    scored = [
        (_pt({"id": "old", "date": stale, "outcome": "unresolved"}), 0.5),
        (_pt({"id": "new", "date": today, "outcome": "resolved"}), 0.5),
    ]
    order = [pt.payload["id"] for pt, _ in _boost(scored)]
    assert order[0] == "new"


def test_boost_keeps_semantic_dominant():
    today = datetime.now(timezone.utc).date().isoformat()
    stale = "2015-01-01"
    # A much stronger semantic match that is old should still beat a weak-but-fresh
    # one: recency only breaks near-ties, it does not override relevance.
    scored = [
        (_pt({"id": "relevant", "date": stale, "outcome": "resolved"}), 10.0),
        (_pt({"id": "fresh", "date": today, "outcome": "resolved"}), 1.0),
    ]
    order = [pt.payload["id"] for pt, _ in _boost(scored)]
    assert order[0] == "relevant"
