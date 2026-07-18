"""End-to-end orchestration of the fault -> fix flow."""

from torq.agent.diagnose import diagnose
from torq.agent.schemas import WorkOrder
from torq.db import models
from torq.dispatch import approval
from torq.workorder.generate import build_work_order


def handle_fault(
    fault_code: str, machine: str = "", context: str = "", translate: bool = True
) -> WorkOrder:
    """Fault event -> diagnosis -> work order -> queued for supervisor approval."""
    models.init_db()
    diag = diagnose(fault_code, machine, context)
    wo = build_work_order(diag, translate=translate)
    return approval.submit(wo)
