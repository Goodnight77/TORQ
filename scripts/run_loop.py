"""Loop check: exercise the API end-to-end — fault -> approve -> outcome -> metrics.

Uses FastAPI's in-process TestClient (no server needed).
Run:  uv run python scripts/run_loop.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from fastapi.testclient import TestClient

from torq.api.main import app


def main() -> None:
    with TestClient(app) as client:
        wo = client.post(
            "/api/faults",
            json={"fault_code": "E-471", "machine": "CM-350 Line 2",
                  "context": "Motor tripped after hours running."},
        ).json()
        wid = wo["id"]
        print(f"Reported fault -> work order {wid} ({wo['status']})")

        pending = client.get("/api/work-orders", params={"status": "pending"}).json()
        assert wid in {w["id"] for w in pending}, "not in pending queue"
        print(f"Pending queue: {[w['id'] for w in pending]}")

        appr = client.post(f"/api/work-orders/{wid}/approve").json()
        print(f"Approved -> {appr['work_order']['status']} "
              f"assigned={appr['work_order']['assigned_to']} "
              f"via {appr['delivery']['channel']}")
        assert appr["work_order"]["status"] == "dispatched"

        res = client.post(
            f"/api/work-orders/{wid}/outcome",
            json={"resolved": True, "actual_fix": "Cleaned louvers, replaced AF-12",
                  "notes": "Lint buildup again", "time_to_fix_min": 28},
        ).json()
        print(f"Outcome recorded -> {res['status']} (fed back into knowledge base)")
        assert res["status"] == "resolved"

        m = client.get("/api/metrics").json()
        print("\nMetrics:", m)
        assert m["total_work_orders"] >= 1 and m["resolved"] >= 1

    print("\nLoop ran end-to-end: fault -> approval -> dispatch -> outcome -> metrics. ✅")


if __name__ == "__main__":
    main()
