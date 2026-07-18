"""MQTT fault listener: subscribe to fault codes and trigger the pipeline."""

import json

import paho.mqtt.client as mqtt

from torq.agent.schemas import WorkOrder
from torq.config import settings
from torq.pipeline import handle_fault


def handle_payload(payload: bytes) -> WorkOrder | None:
    """Parse one fault message and run it through the pipeline."""
    try:
        fault = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        print(f"[MQTT] ignored bad payload: {e}")
        return None
    if "fault_code" not in fault:
        print("[MQTT] ignored payload without fault_code")
        return None
    wo = handle_fault(
        fault["fault_code"], fault.get("machine", ""), fault.get("context", "")
    )
    print(f"[MQTT] {fault['fault_code']} -> work order {wo.id} queued for approval")
    return wo


def _on_connect(client, userdata, flags, reason_code, properties=None) -> None:
    client.subscribe(settings.mqtt_topic)
    print(f"[MQTT] subscribed to {settings.mqtt_topic}")


def _on_message(client, userdata, msg) -> None:
    handle_payload(msg.payload)


def build_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect(settings.mqtt_broker_url, settings.mqtt_port, keepalive=60)
    return client


def run() -> None:
    """Blocking listener. Falls back with a clear message if the broker is down."""
    client = build_client()
    print(f"[MQTT] listening on {settings.mqtt_broker_url}:{settings.mqtt_port}")
    client.loop_forever()


if __name__ == "__main__":
    run()
