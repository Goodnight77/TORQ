"""MQTT fault event schema for real-time plant machine ingestion."""

from datetime import datetime, timezone
from typing import ClassVar

from pydantic import BaseModel, Field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MachineFaultEvent(BaseModel):
    """Schema for fault messages arriving from plant machines via MQTT.

    Expected JSON payload published to ``MQTT_TOPIC``::

        {
            "machine_id": "CM-350 Line 2",
            "fault_code": "E-471",
            "timestamp": "2026-07-18T12:00:00+00:00",
            "severity": 4,
            "context": "Motor tripped after hours running."
        }

    Plant SCADA or the edge gateway script (``scripts/mqtt_gateway.py``) is
    responsible for publishing messages that match this schema.
    """

    machine_id: str
    fault_code: str
    timestamp: str = Field(default_factory=_now)
    severity: int = Field(default=3, ge=1, le=5)
    context: str = ""

    SEVERITY_LABELS: ClassVar[dict[int, str]] = {1: "info", 2: "low", 3: "warning", 4: "high", 5: "critical"}
