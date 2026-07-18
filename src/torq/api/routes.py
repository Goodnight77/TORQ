"""HTTP endpoints: faults, work orders, approvals, outcomes, dashboard metrics."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from torq.db import models
from torq.dispatch import approval
from torq.knowledge import feedback
from torq.pipeline import handle_fault

router = APIRouter()


class FaultIn(BaseModel):
    fault_code: str
    machine: str = ""
    context: str = ""
    translate: bool = True


class OutcomeIn(BaseModel):
    resolved: bool
    actual_fix: str = ""
    notes: str = ""
    time_to_fix_min: float | None = None


@router.post("/faults")
def report_fault(f: FaultIn):
    """A machine fault arrives -> diagnose -> queue a work order for approval."""
    return handle_fault(f.fault_code, f.machine, f.context, translate=f.translate)


@router.get("/work-orders")
def work_orders(status: str | None = None):
    return models.list_by_status(status) if status else models.list_all()


@router.get("/work-orders/{wo_id}")
def work_order(wo_id: str):
    wo = models.get(wo_id)
    if not wo:
        raise HTTPException(404, "work order not found")
    return wo


@router.post("/work-orders/{wo_id}/approve")
def approve(wo_id: str):
    res = approval.approve(wo_id)
    if not res:
        raise HTTPException(404, "work order not found")
    wo, delivery = res
    return {"work_order": wo, "delivery": delivery}


@router.post("/work-orders/{wo_id}/reject")
def reject(wo_id: str):
    wo = approval.reject(wo_id)
    if not wo:
        raise HTTPException(404, "work order not found")
    return wo


@router.post("/work-orders/{wo_id}/outcome")
def outcome(wo_id: str, o: OutcomeIn):
    wo = feedback.record_outcome(
        wo_id, o.resolved, o.actual_fix, o.notes, o.time_to_fix_min
    )
    if not wo:
        raise HTTPException(404, "work order not found")
    return wo


@router.get("/metrics")
def metrics():
    return models.metrics()
