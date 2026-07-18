"""MQTT check: publish a fault to the broker, confirm the listener queues a work order.

Run:  uv run python scripts/run_mqtt.py
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from torq.db import models
from torq.events import simulator
from torq.events.listener import build_client


def main() -> None:
    models.init_db()
    before = {w.id for w in models.list_by_status("pending")}

    client = build_client()  # subscribes on connect
    client.loop_start()
    time.sleep(1.0)  # let the subscription establish

    simulator.publish(
        [{"fault_code": "J-108", "machine": "PK-9 Line 3", "context": "Film not advancing."}]
    )

    new: set[str] = set()
    for _ in range(30):  # up to ~60s for round trip + diagnosis
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
