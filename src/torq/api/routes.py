"""HTTP endpoints: faults, work orders, approvals, outcomes, dashboard metrics."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from torq.config import settings
from torq.db import models
from torq.dispatch import approval
from torq.knowledge import feedback
from torq.pipeline import handle_fault
from torq.workorder.pdf import render_pdf

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


@router.get("/work-orders/{wo_id}/pdf")
def work_order_pdf(wo_id: str):
    """Download the work-order PDF. Renders it on demand if not generated yet."""
    wo = models.get(wo_id)
    if not wo:
        raise HTTPException(404, "work order not found")
    path = Path(wo.pdf_path) if wo.pdf_path else None
    if not path or not path.exists():
        path = render_pdf(wo)
        wo.pdf_path = str(path)
        models.save(wo)
    return FileResponse(path, media_type="application/pdf", filename=f"work_order_{wo.id}.pdf")


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


@router.get("/eval")
def eval_results():
    """Precomputed retrieval-eval results (dense vs hybrid vs hybrid+rerank)."""
    p = settings.eval_results_file
    if not p.exists():
        return {"configs": []}
    return json.loads(p.read_text(encoding="utf-8"))
