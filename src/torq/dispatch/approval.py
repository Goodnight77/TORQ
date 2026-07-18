"""Supervisor approval queue: approve/reject before dispatch."""

from torq.agent.schemas import WorkOrder, _now
from torq.db import models
from torq.dispatch import notify, routing
from torq.workorder.pdf import render_pdf


def submit(wo: WorkOrder) -> WorkOrder:
    """Queue a work order for supervisor approval."""
    wo.status = "pending"
    models.save(wo)
    return wo


def pending() -> list[WorkOrder]:
    return models.list_by_status("pending")


def reject(wo_id: str) -> WorkOrder | None:
    wo = models.get(wo_id)
    if not wo:
        return None
    wo.status = "rejected"
    models.save(wo)
    return wo


def approve(wo_id: str) -> tuple[WorkOrder, dict] | None:
    """Approve, route to a technician, dispatch. Returns (work order, delivery)."""
    wo = models.get(wo_id)
    if not wo:
        return None
    tech = routing.choose_technician(wo)
    if not tech:
        wo.status = "approved"  # approved but no one on shift to take it
        models.save(wo)
        return wo, {"channel": "none", "error": "no technician available"}

    try:
        wo.pdf_path = str(render_pdf(wo))
    except Exception as e:  # noqa: BLE001 - PDF is a nice-to-have, never block dispatch
        print(f"[approval] PDF render skipped: {e}")

    delivery = notify.dispatch(wo, tech)
    wo.status = "dispatched"
    wo.assigned_to = tech.get("name")
    wo.dispatched_at = _now()
    models.save(wo)
    return wo, delivery
