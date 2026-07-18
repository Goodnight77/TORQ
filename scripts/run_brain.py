"""Core-brain check: ingest manuals + history, then diagnose the seeded scenarios.

Run:  uv run python scripts/run_brain.py
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from torq.agent.diagnose import diagnose
from torq.config import settings
from torq.ingest.history import ingest_history
from torq.ingest.manuals import ingest_manuals


def main() -> None:
    print(f"Ingesting manuals... {ingest_manuals()} chunks")
    print(f"Ingesting history... {ingest_history()} records")

    scenarios = json.loads(settings.scenarios_file.read_text(encoding="utf-8"))
    for s in scenarios:
        d = diagnose(s["fault_code"], s.get("machine", ""), s.get("context", ""))
        print("\n" + "=" * 70)
        print(f"{s['id']}  {d.machine}  fault {d.fault_code}  (conf {d.confidence})")
        print(f"  root cause : {d.root_cause}")
        print(f"  steps      : {len(d.repair_steps)} -> {d.repair_steps[:2]}...")
        print(f"  parts      : {d.parts}")
        print(f"  sources    : {d.sources}")
        # check: a usable diagnosis must have a cause and at least one step
        assert d.root_cause and d.repair_steps, f"empty diagnosis for {s['id']}"

    print("\nAll scenarios produced a grounded diagnosis. ✅")


if __name__ == "__main__":
    main()
