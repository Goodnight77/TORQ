"""Supervisor approval queue (AgentRQ pattern): approve/reject before dispatch."""

from torq.agent.schemas import WorkOrder
from torq.db import models
from torq.dispatch import notify, routing


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

    delivery = notify.dispatch(wo, tech)
    wo.status = "dispatched"
    wo.assigned_to = tech.get("name")
    models.save(wo)
    return wo, delivery
