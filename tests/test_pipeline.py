"""End-to-end pipeline tests (with mocked external dependencies)."""

import unittest
from unittest.mock import MagicMock, patch

from torq.agent.schemas import Diagnosis, WorkOrder
from torq.pipeline import handle_fault

MOCK_DIAGNOSIS = Diagnosis(
    fault_code="E-471",
    machine="CM-350 Line 2",
    root_cause="Clogged intake louvers restricting cooling airflow.",
    confidence=0.85,
    repair_steps=["Lockout/tagout the drive.", "Clean intake louvers.", "Reset and monitor."],
    parts=["Intake filter mat AF-12"],
    tools=["Screwdriver", "Torque wrench"],
    safety_warnings=["Disconnect power before servicing."],
    sources=["cm-350-manual"],
)


class HandleFaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.init_db_patch = patch("torq.pipeline.models.init_db")
        self.diagnose_patch = patch("torq.pipeline.diagnose", return_value=MOCK_DIAGNOSIS)
        self.build_patch = patch("torq.pipeline.build_work_order")
        self.submit_patch = patch("torq.pipeline.approval.submit")

        self.mock_init_db = self.init_db_patch.start()
        self.mock_diagnose = self.diagnose_patch.start()
        self.mock_build = self.build_patch.start()
        self.mock_submit = self.submit_patch.start()

    def tearDown(self) -> None:
        for p in (self.init_db_patch, self.diagnose_patch, self.build_patch, self.submit_patch):
            p.stop()

    def _mock_work_order(self, **overrides: object) -> WorkOrder:
        defaults: dict[str, object] = dict(
            id="wo-test",
            fault_code="E-471",
            machine="CM-350 Line 2",
            root_cause="Clogged intake louvers.",
            status="pending",
        )
        defaults.update(overrides)
        return WorkOrder(**defaults)  # type: ignore[arg-type]

    def test_handle_fault_returns_work_order(self) -> None:
        wo = self._mock_work_order()
        self.mock_build.return_value = wo
        self.mock_submit.return_value = wo

        result = handle_fault("E-471", "CM-350 Line 2", "Motor tripped.")

        self.mock_init_db.assert_called_once()
        self.mock_diagnose.assert_called_once_with("E-471", "CM-350 Line 2", "Motor tripped.")
        self.mock_build.assert_called_once()
        self.mock_submit.assert_called_once_with(wo)
        self.assertIs(result, wo)

    def test_handle_fault_translate_default_true(self) -> None:
        wo = self._mock_work_order()
        self.mock_build.return_value = wo
        self.mock_submit.return_value = wo

        handle_fault("E-471", "CM-350 Line 2", "")
        _call = self.mock_build.call_args
        assert _call is not None
        _kwargs = _call[1] if _call[1] else {}
        self.assertNotIn("translate", _kwargs) or self.assertTrue(_kwargs.get("translate", True))

    def test_handle_fault_translate_false(self) -> None:
        wo = self._mock_work_order()
        self.mock_build.return_value = wo
        self.mock_submit.return_value = wo

        handle_fault("E-471", "CM-350 Line 2", "", translate=False)
        self.mock_build.assert_called_once()
        _call = self.mock_build.call_args
        assert _call is not None
        _kwargs = _call[1] if _call[1] else {}
        self.assertFalse(_kwargs.get("translate", True))

    def test_handle_fault_defaults_empty_context(self) -> None:
        wo = self._mock_work_order()
        self.mock_build.return_value = wo
        self.mock_submit.return_value = wo

        handle_fault("E-471")
        self.mock_diagnose.assert_called_once_with("E-471", "", "")

    def test_handle_fault_submit_queues_pending(self) -> None:
        wo_pending = self._mock_work_order(status="pending")
        self.mock_build.return_value = wo_pending
        self.mock_submit.return_value = wo_pending

        result = handle_fault("E-471")
        self.assertEqual(result.status, "pending")


if __name__ == "__main__":
    unittest.main()
