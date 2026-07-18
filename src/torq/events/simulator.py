"""MQTT fault simulator: publish synthetic plant faults in real-time.

Publishes ``MachineFaultEvent`` messages to the configured MQTT topic
at random intervals to simulate a live plant floor.

Run::

    uv run python -m torq.events.simulator
    uv run python -m torq.events.simulator --min-interval 10 --max-interval 60
"""

import argparse
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from torq.config import settings
from torq.events.schemas import MachineFaultEvent


def _load_faults() -> list[dict]:
    """Load seeded scenarios as the pool of possible faults."""
    try:
        return json.loads(settings.scenarios_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[SIM] cannot load scenarios: {exc}")
        return [
            {"machine": "CM-350 Line 2", "fault_code": "E-471",
             "context": "Motor overtemperature trip."},
            {"machine": "CM-350 Line 1", "fault_code": "E-201",
             "context": "Motor will not start, overcurrent on ramp-up."},
            {"machine": "PK-9 Line 3", "fault_code": "J-108",
             "context": "Film not advancing, feed jam suspected."},
            {"machine": "PK-9 Line 3", "fault_code": "J-233",
             "context": "Seal temperature timeout, heater cartridge degraded."},
        ]


def run(min_interval: float = 15.0, max_interval: float = 90.0) -> None:
    """Publish random faults at random intervals until interrupted.

    Parameters
    ----------
    min_interval:
        Minimum seconds between publishes (HiveMQ rate-limit safety).
    max_interval:
        Maximum seconds between publishes.
    """
    faults = _load_faults()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(settings.mqtt_broker_url, settings.mqtt_port, keepalive=60)
    except Exception as exc:
        print(f"[SIM] cannot connect to broker: {exc}")
        return

    client.loop_start()
    print(
        f"[SIM] publishing {len(faults)} fault variants to "
        f"{settings.mqtt_topic} every {min_interval}-{max_interval}s"
    )

    try:
        while True:
            scenario = random.choice(faults)
            event = MachineFaultEvent(
                machine_id=scenario["machine"],
                fault_code=scenario["fault_code"],
                timestamp=datetime.now(timezone.utc).isoformat(),
                severity=random.choice([1, 2, 3, 4, 5]),
                context=scenario.get("context", ""),
            )
            payload = event.model_dump_json()
            client.publish(settings.mqtt_topic, payload, qos=0)
            sev = MachineFaultEvent.SEVERITY_LABELS.get(event.severity, "?")
            print(
                f"[SIM] {event.machine_id} {event.fault_code} "
                f"(sev={sev})  topic={settings.mqtt_topic}"
            )

            delay = random.uniform(min_interval, max_interval)
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\n[SIM] stopped")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TORQ plant-floor simulator")
    parser.add_argument(
        "--min-interval", type=float, default=15.0,
        help="Minimum seconds between publishes (default 15)",
    )
    parser.add_argument(
        "--max-interval", type=float, default=90.0,
        help="Maximum seconds between publishes (default 90)",
    )
    args = parser.parse_args()
    run(min_interval=args.min_interval, max_interval=args.max_interval)
