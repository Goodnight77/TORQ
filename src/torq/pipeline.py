"""End-to-end orchestration of the fault -> fix flow."""

from datetime import datetime, timezone

from torq.agent.diagnose import diagnose
from torq.agent.schemas import WorkOrder
from torq.db import models
from torq.dispatch import approval
from torq.events import live
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
    live.push_activity("fault_received", machine, fault_code)
    live.push_activity("diagnosing", machine, fault_code, detail="reading manuals + repair history")
    diag = diagnose(fault_code, machine, context)
    wo = build_work_order(diag, translate=translate, fault_arrived_at=fault_arrived_at)
    live.push_activity("work_order_created", machine, fault_code, detail=diag.root_cause, wo_id=wo.id)
    return approval.submit(wo)
