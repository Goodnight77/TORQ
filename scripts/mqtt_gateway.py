"""MQTT edge gateway: bridge plant control systems to TORQ.

In a real deployment this script runs on an edge device at the plant and
reads fault codes from the machine PLC over **Modbus TCP** or **OPC-UA**,
then republishes them as ``MachineFaultEvent`` JSON to the TORQ MQTT topic.

Without a real PLC (e.g., during demos) it reads from a JSON data source.

Usage::

    # Demo mode — reads from JSON file
    uv run python scripts/mqtt_gateway.py

    # Production — uncomment the Modbus section below and comment out
    # the JSON file reader.

Expected JSON payloads published by this script::

    {
        "machine_id": "CM-350 Line 2",
        "fault_code": "E-471",
        "timestamp": "2026-07-18T12:00:00+00:00",
        "severity": 4,
        "context": "Motor overtemperature PTC trip"
    }

Plant SCADA can publish the same schema directly to ``MQTT_TOPIC``
without this gateway — just emit the JSON above.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

from torq.config import settings
from torq.events.schemas import MachineFaultEvent

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "gateway_source.json"


def _read_source(path: Path) -> list[dict]:
    """Read fault entries from a JSON source file (gateway_source.json)."""
    if not path.exists():
        print(f"[gateway] source not found: {path}")
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[gateway] bad source file: {exc}")
        return []


def _read_modbus() -> list[dict]:
    """Read fault codes from a PLC via Modbus TCP.

    Production stub — replace with real Modbus/OPC-UA driver.
    Requires ``pymodbus`` or ``opcua-asyncio`` installed on the edge device.

    .. code-block:: python

        from pymodbus.client import ModbusTcpClient

        client = ModbusTcpClient("192.168.1.100", port=502)
        client.connect()
        # read holding registers where the PLC writes fault codes
        registers = client.read_holding_registers(0, 10)
        client.close()

        # transform register values into MachineFaultEvent dicts
        ...
    """
    print("[gateway] Modbus not connected — using JSON source fallback")
    return _read_source(DEFAULT_SOURCE)


def run(source: Path, interval: float = 10.0) -> None:
    """Read fault entries and publish each as MachineFaultEvent.

    Parameters
    ----------
    source:
        Path to a JSON file with fault entries (see ``data/gateway_source.json``).
    interval:
        Seconds to wait between publish cycles.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(settings.mqtt_broker_url, settings.mqtt_port, keepalive=60)
    except Exception as exc:
        print(f"[gateway] cannot connect to broker: {exc}")
        return

    client.loop_start()
    print(f"[gateway] publishing from {source} to {settings.mqtt_topic}")

    try:
        sent: set[str] = set()
        while True:
            entries = _read_modbus() if str(source) == "modbus" else _read_source(source)
            for entry in entries:
                # Fingerprint the full entry, not just machine+code: two rows
                # with the same machine and code but different context/severity
                # are distinct faults (e.g. a recurring overtemp) and must both
                # publish. Bounded by the number of distinct rows in the source.
                fingerprint = json.dumps(entry, sort_keys=True)
                if fingerprint in sent:
                    continue  # skip rows already published this run
                event = MachineFaultEvent(
                    machine_id=entry["machine_id"],
                    fault_code=entry["fault_code"],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    severity=entry.get("severity", 3),
                    context=entry.get("context", ""),
                )
                payload = event.model_dump_json()
                client.publish(settings.mqtt_topic, payload, qos=0)
                print(f"[gateway] published {event.machine_id} {event.fault_code}")
                sent.add(fingerprint)
                time.sleep(1.0)  # gentle publishing rate
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[gateway] stopped")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TORQ MQTT edge gateway — bridge PLC/SCADA to TORQ"
    )
    parser.add_argument(
        "--source", type=str, default=str(DEFAULT_SOURCE),
        help="JSON source file with fault entries (or 'modbus' for real PLC)",
    )
    parser.add_argument(
        "--interval", type=float, default=10.0,
        help="Seconds between publish cycles (default 10)",
    )
    args = parser.parse_args()
    run(Path(args.source), interval=args.interval)
