"""Action-layer check: fault -> work order -> approval queue -> dispatch.

Assumes manuals/history are already indexed (run scripts/run_brain.py first).
Run:  uv run python scripts/run_action.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from torq.dispatch import approval
from torq.pipeline import handle_fault


def main() -> None:
    # 1. A fault arrives -> pipeline diagnoses and queues a work order for approval.
    wo = handle_fault("E-471", "CM-350 Line 2", "Night shift, motor tripped after hours running.")
    print(f"Queued work order {wo.id}  status={wo.status}  skill={wo.required_skill}")
    print(f"  languages: {sorted(wo.content)}")

    # 2. Supervisor sees the pending queue.
    q = approval.pending()
    print(f"Pending queue: {[w.id for w in q]}")
    assert wo.id in {w.id for w in q}, "work order missing from pending queue"

    # 3. Supervisor approves -> routed + dispatched.
    result = approval.approve(wo.id)
    assert result, "approve returned None"
    approved, delivery = result
    print(f"Approved {approved.id}  status={approved.status}  assigned={approved.assigned_to}")
    print(f"  delivery: channel={delivery.get('channel')} to={delivery.get('to')}")

    ar = wo.content.get("ar", "")
    print("\n--- Arabic work order (dispatched text) ---")
    print(ar[:400] if ar else "(no Arabic translation)")

    assert approved.status == "dispatched", "work order was not dispatched"
    assert approved.assigned_to, "no technician assigned"
    print("\nAction layer ran end-to-end: fault -> approval -> dispatch. ✅")


if __name__ == "__main__":
    main()
