"""MQTT fault listener: subscribe to plant machine faults and trigger the pipeline.

Runs in a background thread inside the API process (see ``torq.api.main``
lifespan). Falls back gracefully if the broker is unreachable.
"""

import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from torq.agent.schemas import WorkOrder
from torq.config import settings
from torq.events import live
from torq.events.schemas import MachineFaultEvent
from torq.pipeline import handle_fault


def handle_payload(payload: bytes) -> WorkOrder | None:
    """Parse, validate, publish to live feed, and run through the pipeline."""
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"[MQTT] bad payload: {exc}")
        return None

    try:
        event = MachineFaultEvent.model_validate(raw)
    except Exception as exc:
        print(f"[MQTT] schema validation failed: {exc}")
        return None

    live.push(event)

    arrival = datetime.now(timezone.utc).isoformat()
    wo = handle_fault(
        event.fault_code,
        machine=event.machine_id,
        context=event.context,
        fault_arrived_at=arrival,
    )
    sev = MachineFaultEvent.SEVERITY_LABELS.get(event.severity, "unknown")
    print(
        f"[MQTT] {event.machine_id} {event.fault_code} "
        f"(severity={sev}) -> work order {wo.id}"
    )
    return wo


def _on_connect(client, userdata, flags, reason_code, properties=None) -> None:
    if reason_code == 0:
        # QoS 0 is at-most-once, so a fault can be dropped silently. Bump to
        # qos=1 (here and on the publisher) if lost faults matter.
        client.subscribe(settings.mqtt_topic, qos=0)
        print(f"[MQTT] subscribed to {settings.mqtt_topic}")
    else:
        print(f"[MQTT] connect failed (reason={reason_code}), will retry…")


def _on_disconnect(client, userdata, disconnect_flags, reason, properties) -> None:
    rc = reason.value if hasattr(reason, "value") else reason
    if rc != 0:
        print(f"[MQTT] disconnected (reason={rc}), auto-reconnecting…")


def _on_message(client, userdata, msg) -> None:
    # Runs the full diagnosis pipeline synchronously in paho's network thread.
    # Fine at demo fault rates; if messages pile up or keepalive stalls, hand
    # payloads to a worker queue and return here immediately.
    handle_payload(msg.payload)


def build_client() -> mqtt.Client:
    """Create and configure the MQTT client (does not connect yet)."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message
    client.reconnect_delay_set(min_delay=4, max_delay=300)
    return client


def run() -> None:
    """Blocking entry point (for standalone use)."""
    client = build_client()
    try:
        client.connect(settings.mqtt_broker_url, settings.mqtt_port, keepalive=60)
    except Exception as exc:
        print(f"[MQTT] cannot reach broker ({exc}), exiting")
        return
    print(f"[MQTT] listening on {settings.mqtt_broker_url}:{settings.mqtt_port}")
    client.loop_forever()


if __name__ == "__main__":
    run()
