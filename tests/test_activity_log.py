"""The pipeline emits activity-log stages that the dashboard SSE stream serves."""

from unittest.mock import MagicMock, patch

from torq.agent.schemas import Diagnosis, WorkOrder
from torq.events import live


def _stages():
    return [e["stage"] for _seq, e in live.RECENT_ACTIVITY]


def test_push_activity_records_shape():
    live.RECENT_ACTIVITY.clear()
    live.push_activity("dispatched", "CM-350", "E-201", detail="whatsapp to Adam", wo_id="ab12")
    _seq, e = live.RECENT_ACTIVITY[-1]
    assert e["stage"] == "dispatched"
    assert e["machine"] == "CM-350"
    assert e["fault_code"] == "E-201"
    assert e["wo_id"] == "ab12"
    assert e["ts"]  # timestamp present


@patch("torq.pipeline.approval.submit", side_effect=lambda wo: wo)
@patch("torq.pipeline.build_work_order")
@patch("torq.pipeline.diagnose")
def test_handle_fault_emits_stages(mock_diag, mock_build, _submit):
    from torq.pipeline import handle_fault

    live.RECENT_ACTIVITY.clear()
    mock_diag.return_value = Diagnosis(fault_code="E-201", root_cause="seized bearing")
    mock_build.return_value = WorkOrder(id="wo1", fault_code="E-201", root_cause="seized bearing")

    handle_fault("E-201", "CM-350")

    stages = _stages()
    assert stages == ["fault_received", "diagnosing", "work_order_created"]
