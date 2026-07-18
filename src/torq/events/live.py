"""Thread-safe shared state between the MQTT listener and the SSE stream."""

import asyncio
from collections import deque
from datetime import datetime, timezone
from itertools import count
from typing import Any, Set

from torq.events.schemas import MachineFaultEvent

# Broadcast listeners (FastAPI SSE clients)
loop: asyncio.AbstractEventLoop | None = None
mqtt_client: Any = None
_fault_listeners: Set[asyncio.Queue] = set()
_activity_listeners: Set[asyncio.Queue] = set()

# Rolling window of recent events for the SSE stream and REST endpoint.
# Each entry is (seq, event_dict). The monotonic seq lets the SSE stream track
# its position even after this bounded deque evicts old items (a plain list
# index breaks once the buffer is full and eviction shifts everything).
RECENT_FAULTS: deque = deque(maxlen=50)
_seq = count(1)  # next() is atomic under the GIL


def push(event: MachineFaultEvent) -> None:
    """Push a validated fault event into the recent buffer and broadcast to listeners."""
    event_dict = event.model_dump()
    RECENT_FAULTS.append((next(_seq), event_dict))
    
    if loop is not None:
        for q in list(_fault_listeners):
            try:
                loop.call_soon_threadsafe(q.put_nowait, event_dict)
            except Exception:  # noqa: BLE001 - ignore listener queue errors
                pass


# Pipeline activity log: one entry per stage of the fault -> fix flow, streamed
# to the dashboard so operators watch faults move through diagnosis and dispatch
# in near real-time. Same (seq, dict) shape as RECENT_FAULTS.
RECENT_ACTIVITY: deque = deque(maxlen=100)
_act_seq = count(1)


def push_activity(
    stage: str,
    machine: str = "",
    fault_code: str = "",
    detail: str = "",
    wo_id: str = "",
) -> None:
    """Record one pipeline stage (received, diagnosing, dispatched, ...) and broadcast."""
    activity_dict = {
        "stage": stage,
        "machine": machine,
        "fault_code": fault_code,
        "detail": detail,
        "wo_id": wo_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    RECENT_ACTIVITY.append((next(_act_seq), activity_dict))
    
    if loop is not None:
        for q in list(_activity_listeners):
            try:
                loop.call_soon_threadsafe(q.put_nowait, activity_dict)
            except Exception:  # noqa: BLE001
                pass
