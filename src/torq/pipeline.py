"""End-to-end orchestration of the fault -> fix flow."""

from datetime import datetime, timezone

from torq.agent.diagnose import diagnose
from torq.agent.schemas import WorkOrder
from torq.db import models
from torq.dispatch import approval
from torq.workorder.generate import build_work_order


def handle_fault(
    fault_code: str,
    machine: str = "",
    context: str = "",
    translate: bool = True,
    fault_arrived_at: str | None = None,
) -> WorkOrder:
    """Fault event -> diagnosis -> work order -> queued for supervisor approval."""
    if fault_arrived_at is None:
        fault_arrived_at = datetime.now(timezone.utc).isoformat()
    models.init_db()
    diag = diagnose(fault_code, machine, context)
    wo = build_work_order(diag, translate=translate, fault_arrived_at=fault_arrived_at)
    return approval.submit(wo)
