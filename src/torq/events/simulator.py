"""MQTT fault simulator: publish synthetic fault-code events to drive the demo."""

import json
import time

import paho.mqtt.client as mqtt

from torq.config import settings


def load_scenarios() -> list[dict]:
    return json.loads(settings.scenarios_file.read_text(encoding="utf-8"))


def publish(faults: list[dict], delay: float = 1.0) -> None:
    """Publish each fault to the broker, `delay` seconds apart."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(settings.mqtt_broker_url, settings.mqtt_port, keepalive=60)
    client.loop_start()
    try:
        for f in faults:
            client.publish(settings.mqtt_topic, json.dumps(f), qos=1)
            print(f"[SIM] published {f.get('fault_code')} to {settings.mqtt_topic}")
            time.sleep(delay)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    # Fire the first seeded scenario by default.
    publish(load_scenarios()[:1])
