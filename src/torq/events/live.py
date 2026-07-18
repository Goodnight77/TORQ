"""Thread-safe shared state between the MQTT listener and the SSE stream."""

from collections import deque
from datetime import datetime, timezone
from itertools import count

from torq.events.schemas import MachineFaultEvent

# Rolling window of recent events for the SSE stream and REST endpoint.
# Each entry is (seq, event_dict). The monotonic seq lets the SSE stream track
# its position even after this bounded deque evicts old items (a plain list
# index breaks once the buffer is full and eviction shifts everything).
RECENT_FAULTS: deque = deque(maxlen=50)
_seq = count(1)  # next() is atomic under the GIL


def push(event: MachineFaultEvent) -> None:
    """Push a validated fault event into the recent buffer."""
    RECENT_FAULTS.append((next(_seq), event.model_dump()))


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
    """Record one pipeline stage (received, diagnosing, dispatched, ...)."""
    RECENT_ACTIVITY.append(
        (
            next(_act_seq),
            {
                "stage": stage,
                "machine": machine,
                "fault_code": fault_code,
                "detail": detail,
                "wo_id": wo_id,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )
    )
