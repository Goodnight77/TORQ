"""Loop check: exercise the API end-to-end - fault -> approve -> outcome -> metrics.

Uses FastAPI's in-process TestClient (no server needed).
When LLM_API_KEY is unset, the diagnosis step is mocked so the script works
in CI without external services.
Run:  uv run python scripts/run_loop.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from unittest.mock import patch

from fastapi.testclient import TestClient

from torq.agent.schemas import Diagnosis
from torq.api.main import app
from torq.config import settings

_MOCK_DIAGNOSIS = Diagnosis(
    fault_code="E-471",
    machine="CM-350 Line 2",
    root_cause="Clogged intake louvers restricting cooling airflow.",
    repair_steps=["Lockout/tagout the drive.", "Clean intake louvers.", "Reset and monitor."],
    parts=["Intake filter mat AF-12"],
    required_skill="electromechanical",
)


def main() -> None:
    needs_mock = not settings.llm_api_key
    ctx = patch("torq.pipeline.diagnose", return_value=_MOCK_DIAGNOSIS) if needs_mock else _noop()

    with ctx:
        with TestClient(app) as client:
            payload: dict = {
                "fault_code": "E-471",
                "machine": "CM-350 Line 2",
                "context": "Motor tripped after hours running.",
            }
            if needs_mock:
                payload["translate"] = False

            wo = client.post("/api/faults", json=payload).json()
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


def _noop():
    class _Noop:
        def __enter__(self):
            return None
        def __exit__(self, *args):
            pass
    return _Noop()


if __name__ == "__main__":
    main()
