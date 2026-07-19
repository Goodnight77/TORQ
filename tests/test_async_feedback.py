import unittest
from unittest.mock import patch, MagicMock
from torq.agent.schemas import WorkOrder
from torq.knowledge.feedback import record_outcome

class AsyncFeedbackTests(unittest.TestCase):
    @patch("torq.knowledge.feedback.upsert_history_record")
    @patch("torq.knowledge.feedback.models")
    def test_record_outcome_sync_when_no_background_tasks(self, mock_models, mock_upsert):
        """Verify that record_outcome runs synchronously when background_tasks is None."""
        wo = WorkOrder(
            id="test-wo-id",
            fault_code="E-471",
            machine="CM-350 Line 2",
            root_cause="Tripped",
            status="pending",
        )
        mock_models.get.return_value = wo
        
        with patch("torq.knowledge.feedback._append_to_history") as mock_append:
            result = record_outcome(
                wo_id="test-wo-id",
                resolved=True,
                actual_fix="Reset switch",
                notes="none",
                time_to_fix_min=15,
                background_tasks=None
            )
            mock_append.assert_called_once_with(wo)
            self.assertEqual(result.status, "resolved")
            self.assertEqual(result.outcome["actual_fix"], "Reset switch")

    @patch("torq.knowledge.feedback.models")
    def test_record_outcome_async_when_background_tasks_provided(self, mock_models):
        """Verify that record_outcome registers background task and returns immediately."""
        wo = WorkOrder(
            id="test-wo-id",
            fault_code="E-471",
            machine="CM-350 Line 2",
            root_cause="Tripped",
            status="pending",
        )
        mock_models.get.return_value = wo
        
        mock_background = MagicMock()
        
        with patch("torq.knowledge.feedback._append_to_history") as mock_append:
            result = record_outcome(
                wo_id="test-wo-id",
                resolved=True,
                actual_fix="Reset switch",
                notes="none",
                time_to_fix_min=15,
                background_tasks=mock_background
            )
            mock_append.assert_not_called()
            mock_background.add_task.assert_called_once_with(mock_append, wo)
            self.assertEqual(result.status, "resolved")
