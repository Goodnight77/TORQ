"""MQTT check: publish a fault to the broker, confirm the listener queues a work order.

Run:  uv run python scripts/run_mqtt.py
"""

import sys
import time
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

import paho.mqtt.client as mqtt

from torq.config import settings
from torq.db import models
from torq.events.schemas import MachineFaultEvent


def main() -> None:
    models.init_db()
    before = {w.id for w in models.list_by_status("pending")}

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(settings.mqtt_broker_url, settings.mqtt_port, keepalive=60)
    client.loop_start()
    time.sleep(1.0)

    event = MachineFaultEvent(
        machine_id="PK-9 Line 3",
        fault_code="J-108",
        timestamp=datetime.now(timezone.utc).isoformat(),
        severity=3,
        context="Film not advancing.",
    )
    client.publish(settings.mqtt_topic, event.model_dump_json(), qos=0)
    print(f"[MQTT] published {event.model_dump_json()}")

    new: set[str] = set()
    for _ in range(30):
        time.sleep(2.0)
        new = {w.id for w in models.list_by_status("pending")} - before
        if new:
            break

    client.loop_stop()
    client.disconnect()

    assert new, "no work order was queued from the MQTT fault"
    print(f"\nMQTT fault -> queued work order(s): {new} ✅")


if __name__ == "__main__":
    main()
