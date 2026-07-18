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


if __name__ == "__main__":
    unittest.main()
