"""Thread-safe shared state between the MQTT listener and the SSE stream."""

from collections import deque
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
