"""HTTP endpoints: faults, work orders, approvals, outcomes, dashboard metrics."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from torq.agent.schemas import WorkOrder
from torq.config import settings
from torq.db import models
from torq.dispatch import approval
from torq.events import live
from torq.knowledge import feedback
from torq.pipeline import handle_fault
from torq.workorder.pdf import render_pdf

router = APIRouter()


class MachineIn(BaseModel):
    id: str = Field(max_length=100)
    model: str = Field(max_length=200)
    location: str = Field(max_length=200)


class FaultIn(BaseModel):
    fault_code: str = Field(min_length=1, max_length=50)
    machine: str = ""
    context: str = ""
    translate: bool = True


class OutcomeIn(BaseModel):
    resolved: bool
    actual_fix: str = ""
    notes: str = ""
    time_to_fix_min: float | None = None


@router.get("/machines")
def machines() -> list[dict[str, Any]]:
    return models.list_machines()


@router.get("/machines/{machine_id}")
def machine(machine_id: str) -> dict[str, Any]:
    registered = models.get_machine(machine_id)
    if not registered:
        raise HTTPException(404, "machine not found")
    return registered


@router.post("/machines", status_code=201)
def create_machine(machine: MachineIn) -> dict[str, Any]:
    machine_id = machine.id.strip()
    model = machine.model.strip()
    location = machine.location.strip()
    if not machine_id or not model or not location:
        raise HTTPException(422, "id, model, and location are required")
    if not models.create_machine(machine_id, model, location):
        raise HTTPException(409, "machine already exists")
    return models.get_machine(machine_id)


@router.post("/faults", status_code=201)
def report_fault(f: FaultIn) -> WorkOrder:
    """A machine fault arrives -> diagnose -> queue a work order for approval."""
    arrival = datetime.now(timezone.utc).isoformat()
    return handle_fault(
        f.fault_code, f.machine, f.context,
        translate=f.translate, fault_arrived_at=arrival,
    )


@router.get("/work-orders")
def work_orders(status: str | None = None) -> list[WorkOrder]:
    return models.list_by_status(status) if status else models.list_all()


@router.get("/work-orders/{wo_id}")
def work_order(wo_id: str) -> WorkOrder:
    wo = models.get(wo_id)
    if not wo:
        raise HTTPException(404, "work order not found")
    return wo


@router.get("/work-orders/{wo_id}/pdf")
def work_order_pdf(wo_id: str) -> FileResponse:
    """Download the work-order PDF. Served from a disk cache; rendered once on miss."""
    path = settings.workorder_dir / f"work_order_{wo_id}.pdf"
    if not path.exists():  # cache miss: fetch once, render, no DB write
        wo = models.get(wo_id)
        if not wo:
            raise HTTPException(404, "work order not found")
        render_pdf(wo, path)
    return FileResponse(path, media_type="application/pdf", filename=f"work_order_{wo_id}.pdf")


@router.post("/work-orders/{wo_id}/approve")
def approve(wo_id: str) -> dict[str, Any]:
    res = approval.approve(wo_id)
    if not res:
        raise HTTPException(404, "work order not found")
    wo, delivery = res
    return {"work_order": wo, "delivery": delivery}


@router.post("/work-orders/{wo_id}/reject")
def reject(wo_id: str) -> WorkOrder:
    wo = approval.reject(wo_id)
    if not wo:
        raise HTTPException(404, "work order not found")
    return wo


@router.post("/work-orders/{wo_id}/notify")
def notify_work_order(wo_id: str) -> dict[str, Any]:
    """Manually (re)send the work order to its matched technician via WhatsApp."""
    res = approval.notify_technician(wo_id)
    if not res:
        raise HTTPException(404, "work order not found")
    wo, delivery = res
    return {"work_order": wo, "delivery": delivery}


@router.post("/work-orders/{wo_id}/outcome")
def outcome(wo_id: str, o: OutcomeIn) -> WorkOrder:
    wo = feedback.record_outcome(
        wo_id, o.resolved, o.actual_fix, o.notes, o.time_to_fix_min
    )
    if not wo:
        raise HTTPException(404, "work order not found")
    return wo


@router.get("/metrics")
def metrics() -> dict[str, Any]:
    return models.metrics()


@router.get("/metrics/trend")
def metrics_trend() -> list[dict[str, Any]]:
    """Per-day diagnosis latency + MTTR for the trend chart."""
    return models.trend()


@router.get("/metrics/faults-per-machine")
def metrics_faults_per_machine() -> list[dict[str, Any]]:
    """Work-order count per machine for the bar chart."""
    return models.faults_per_machine()


@router.get("/events/stream")
async def event_stream(request: Request) -> StreamingResponse:
    """SSE endpoint: streams incoming MachineFaultEvent in real-time."""

    async def generate():
        last_seq = 0
        while True:
            for seq, event in list(live.RECENT_FAULTS):
                if seq > last_seq:
                    yield f"event: fault\ndata: {json.dumps(event)}\n\n"
                    last_seq = seq
            if await request.is_disconnected():
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/events/recent")
def recent_events() -> list[dict[str, Any]]:
    """Return the last 50 MachineFaultEvent dicts."""
    return [event for _seq, event in live.RECENT_FAULTS]


@router.get("/events/activity/stream")
async def activity_stream(request: Request) -> StreamingResponse:
    """SSE endpoint: streams pipeline activity (received -> diagnosed -> dispatched)."""

    async def generate():
        last_seq = 0
        while True:
            for seq, event in list(live.RECENT_ACTIVITY):
                if seq > last_seq:
                    yield f"event: activity\ndata: {json.dumps(event)}\n\n"
                    last_seq = seq
            if await request.is_disconnected():
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/events/activity/recent")
def recent_activity() -> list[dict[str, Any]]:
    """Return the recent pipeline activity entries (oldest first)."""
    return [event for _seq, event in live.RECENT_ACTIVITY]


@router.get("/eval")
def eval_results() -> dict[str, Any]:
    """Precomputed retrieval-eval results (dense vs hybrid vs hybrid+rerank)."""
    p = settings.eval_results_file
    if not p.exists():
        return {"configs": []}
    return json.loads(p.read_text(encoding="utf-8"))
