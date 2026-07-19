"""Supervisor approval queue: approve/reject before dispatch."""

import logging

from torq.agent.schemas import WorkOrder, _now

log = logging.getLogger(__name__)
from torq.db import models
from torq.dispatch import notify, routing
from torq.events import live
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
    live.push_activity("rejected", wo.machine, wo.fault_code, wo_id=wo.id)
    return wo


def approve(wo_id: str) -> tuple[WorkOrder, dict] | None:
    """Approve, route to a technician, dispatch. Returns (work order, delivery)."""
    wo = models.get(wo_id)
    if not wo:
        return None
    live.push_activity("approved", wo.machine, wo.fault_code, wo_id=wo.id)
    tech = routing.choose_technician(wo)
    if not tech:
        wo.status = "approved"  # approved but no one on shift to take it
        models.save(wo)
        live.push_activity(
            "dispatch_failed", wo.machine, wo.fault_code,
            detail="no technician on shift", wo_id=wo.id,
        )
        return wo, {"channel": "none", "error": "no technician available"}

    try:
        path = render_pdf(wo)
        wo.pdf_path = str(path)
    except Exception as e:
        log.warning("PDF render failed for %s: %s", wo.id, e)

    delivery = notify.dispatch(wo, tech)
    wo.status = "dispatched"
    wo.assigned_to = tech.get("name")
    wo.dispatched_at = _now()
    models.save(wo)
    live.push_activity(
        "dispatched", wo.machine, wo.fault_code,
        detail=f"{delivery.get('channel', '?')} to {tech.get('name', '?')}", wo_id=wo.id,
    )
    return wo, delivery


def notify_technician(wo_id: str) -> tuple[WorkOrder, dict] | None:
    """Manually (re)send a work order's WhatsApp to its matched technician.

    On-demand send for the supervisor/demo: works on any work order regardless
    of status, so a message can be pushed (or re-pushed) at will.
    """
    wo = models.get(wo_id)
    if not wo:
        return None
    tech = routing.choose_technician(wo)
    if not tech:
        live.push_activity(
            "dispatch_failed", wo.machine, wo.fault_code,
            detail="no technician on shift", wo_id=wo.id,
        )
        return wo, {"channel": "none", "error": "no technician available"}

    delivery = notify.dispatch(wo, tech)
    wo.assigned_to = tech.get("name")
    if wo.status in ("pending", "approved"):
        wo.status = "dispatched"
        wo.dispatched_at = _now()
    models.save(wo)
    live.push_activity(
        "dispatched", wo.machine, wo.fault_code,
        detail=f"{delivery.get('channel', '?')} to {tech.get('name', '?')}", wo_id=wo.id,
    )
    return wo, delivery
