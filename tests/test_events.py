"""Tests for MQTT event schema, listener parsing, and simulator format."""

import json
import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from torq.events.schemas import MachineFaultEvent


class MachineFaultEventTests(unittest.TestCase):
    def test_valid_event_minimal(self) -> None:
        event = MachineFaultEvent(machine_id="CM-350", fault_code="E-471")
        self.assertEqual(event.machine_id, "CM-350")
        self.assertEqual(event.fault_code, "E-471")
        self.assertEqual(event.severity, 3)
        self.assertIsInstance(event.timestamp, str)
        self.assertEqual(event.context, "")

    def test_valid_event_full(self) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        event = MachineFaultEvent(
            machine_id="PK-9 Line 3",
            fault_code="J-108",
            timestamp=ts,
            severity=4,
            context="Film jam",
        )
        self.assertEqual(event.severity, 4)
        self.assertEqual(event.context, "Film jam")

    def test_severity_must_be_ge_1(self) -> None:
        with self.assertRaises(ValidationError):
            MachineFaultEvent(machine_id="X", fault_code="X", severity=0)

    def test_severity_must_be_le_5(self) -> None:
        with self.assertRaises(ValidationError):
            MachineFaultEvent(machine_id="X", fault_code="X", severity=6)

    def test_severity_accepts_1_to_5(self) -> None:
        for s in range(1, 6):
            event = MachineFaultEvent(machine_id="X", fault_code="X", severity=s)
            self.assertEqual(event.severity, s)

    def test_machine_id_is_required(self) -> None:
        with self.assertRaises(ValidationError):
            MachineFaultEvent(fault_code="X")  # type: ignore[call-arg]

    def test_fault_code_is_required(self) -> None:
        with self.assertRaises(ValidationError):
            MachineFaultEvent(machine_id="X")  # type: ignore[call-arg]

    def test_json_roundtrip(self) -> None:
        original = MachineFaultEvent(
            machine_id="CM-350 Line 2",
            fault_code="E-471",
            severity=4,
            context="Motor trip",
        )
        raw = original.model_dump_json()
        restored = MachineFaultEvent.model_validate_json(raw)
        self.assertEqual(original.machine_id, restored.machine_id)
        self.assertEqual(original.fault_code, restored.fault_code)
        self.assertEqual(original.severity, restored.severity)
        self.assertEqual(original.context, restored.context)

    def test_severity_labels_cover_all_levels(self) -> None:
        for s in range(1, 6):
            label = MachineFaultEvent.SEVERITY_LABELS.get(s)
            self.assertIsNotNone(label)
            self.assertIsInstance(label, str)

    def test_parse_valid_json_dict(self) -> None:
        raw = {"machine_id": "CM-350", "fault_code": "E-471", "severity": 2}
        event = MachineFaultEvent.model_validate(raw)
        self.assertEqual(event.severity, 2)

    def test_parse_invalid_json_dict(self) -> None:
        with self.assertRaises(ValidationError):
            MachineFaultEvent.model_validate({"machine_id": "X"})  # missing fault_code


class ListenerParseTests(unittest.TestCase):
    def test_listener_rejects_bad_utf8(self) -> None:
        from torq.events.listener import handle_payload

        result = handle_payload(b"\xff\xfe\x00\x01")
        self.assertIsNone(result)

    def test_listener_rejects_non_json(self) -> None:
        from torq.events.listener import handle_payload

        result = handle_payload(b"not json")
        self.assertIsNone(result)

    def test_listener_rejects_missing_fields(self) -> None:
        from torq.events.listener import handle_payload

        result = handle_payload(json.dumps({"foo": "bar"}).encode())
        self.assertIsNone(result)


class SimulatorFormatTests(unittest.TestCase):
    def test_simulator_scenarios_load(self) -> None:
        from torq.events.simulator import _load_faults

        faults = _load_faults()
        self.assertGreater(len(faults), 0)
        for f in faults:
            self.assertIn("machine", f)
            self.assertIn("fault_code", f)

    def test_simulator_publishes_valid_event(self) -> None:
        from torq.events.simulator import _load_faults
        from torq.events.schemas import MachineFaultEvent

        faults = _load_faults()
        scenario = faults[0]
        event = MachineFaultEvent(
            machine_id=scenario["machine"],
            fault_code=scenario["fault_code"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=3,
            context=scenario.get("context", ""),
        )
        parsed = json.loads(event.model_dump_json())
        self.assertEqual(parsed["machine_id"], scenario["machine"])
        self.assertEqual(parsed["fault_code"], scenario["fault_code"])
        self.assertIn("timestamp", parsed)
        self.assertIn("severity", parsed)


class LiveBufferTests(unittest.TestCase):
    def setUp(self) -> None:
        from torq.events import live

        live.RECENT_FAULTS.clear()

    def _push(self, n: int) -> None:
        from torq.events import live

        for i in range(n):
            live.push(MachineFaultEvent(machine_id="M", fault_code=f"F{i}"))

    def test_seq_monotonic_and_unique(self) -> None:
        from torq.events import live

        self._push(5)
        seqs = [s for s, _ in live.RECENT_FAULTS]
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(len(set(seqs)), len(seqs))

    def test_consumer_gets_new_events_after_buffer_full(self) -> None:
        from torq.events import live

        # Fill past maxlen so old entries evict: the case the old index-based
        # SSE cursor broke on (it returned nothing once the buffer was full).
        self._push(60)
        buf = list(live.RECENT_FAULTS)
        self.assertEqual(len(buf), 50)  # bounded window
        last_seq = buf[-1][0]  # a consumer caught up to the newest event
        self._push(3)  # three more faults arrive
        fresh = [e for s, e in live.RECENT_FAULTS if s > last_seq]
        self.assertEqual(len(fresh), 3)  # old code yielded 0 here

    def test_recent_events_returns_plain_dicts(self) -> None:
        from torq.api.routes import recent_events

        self._push(2)
        out = recent_events()
        self.assertTrue(all(isinstance(e, dict) for e in out))
        self.assertEqual(out[0]["machine_id"], "M")


class GatewaySourceTests(unittest.TestCase):
    def test_every_source_row_publishes(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        rows = json.loads(
            (root / "data" / "gateway_source.json").read_text(encoding="utf-8")
        )
        # Full-entry fingerprint keeps every row distinct, so none is dropped.
        full = {json.dumps(r, sort_keys=True) for r in rows}
        self.assertEqual(len(full), len(rows))
        # machine+code alone collides (a recurring fault), which is exactly the
        # bug the full-entry fingerprint fixes.
        code_only = {f"{r['machine_id']}:{r['fault_code']}" for r in rows}
        self.assertLess(len(code_only), len(rows))


if __name__ == "__main__":
    unittest.main()
