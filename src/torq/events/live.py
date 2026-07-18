"""Thread-safe shared state between the MQTT listener and the SSE stream."""

from collections import deque

from torq.events.schemas import MachineFaultEvent

# Rolling window of recent events for the SSE stream and REST endpoint.
RECENT_FAULTS: deque = deque(maxlen=50)


def push(event: MachineFaultEvent) -> None:
    """Push a validated fault event into the recent buffer."""
    RECENT_FAULTS.append(event.model_dump())
