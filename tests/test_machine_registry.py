"""Tests for the machine registry and per-machine dashboard metrics."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from torq.agent.schemas import WorkOrder
from torq.api.main import app
from torq.config import settings
from torq.db import models


class MachineRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(
            settings, "db_path", Path(self.temporary_directory.name) / "torq.db"
        )
        self.url_patch = patch.object(settings, "database_url", "")
        self.db_patch.start()
        self.url_patch.start()
        models.init_db()

    def tearDown(self) -> None:
        self.url_patch.stop()
        self.db_patch.stop()
        self.temporary_directory.cleanup()

    def test_demo_machines_are_seeded_from_scenarios(self) -> None:
        self.assertEqual(
            models.list_machines(),
            [
                {"id": "CM-350 Line 1", "model": "CM-350", "location": "Line 1"},
                {"id": "CM-350 Line 2", "model": "CM-350", "location": "Line 2"},
                {"id": "PK-9 Line 3", "model": "PK-9", "location": "Line 3"},
            ],
        )

    def test_create_machine_rejects_duplicate_ids(self) -> None:
        self.assertTrue(models.create_machine("P-100 Bay 4", "P-100", "Bay 4"))
        self.assertFalse(models.create_machine("P-100 Bay 4", "Other", "Elsewhere"))
        self.assertEqual(
            models.get_machine("P-100 Bay 4"),
            {"id": "P-100 Bay 4", "model": "P-100", "location": "Bay 4"},
        )

    def test_metrics_group_completed_downtime_by_machine(self) -> None:
        models.save(
            WorkOrder(
                id="wo-recorded",
                fault_code="E-471",
                machine="CM-350 Line 2",
                root_cause="overheating",
                status="resolved",
                created_at="2026-01-01T10:00:00+00:00",
                resolved_at="2026-01-01T11:00:00+00:00",
                outcome={"time_to_fix_min": 25},
            )
        )
        models.save(
            WorkOrder(
                id="wo-derived",
                fault_code="E-201",
                machine="CM-350 Line 2",
                root_cause="bearing",
                status="failed",
                created_at="2026-01-02T10:00:00+00:00",
                resolved_at="2026-01-02T10:15:00+00:00",
            )
        )
        models.save(
            WorkOrder(
                id="wo-open",
                fault_code="J-108",
                machine="PK-9 Line 3",
                root_cause="jam",
            )
        )

        metrics = models.metrics()
        by_machine = {
            row["machine_id"]: row for row in metrics["machine_downtime"]
        }

        self.assertEqual(by_machine["CM-350 Line 2"]["work_orders"], 2)
        self.assertEqual(by_machine["CM-350 Line 2"]["downtime_min"], 40.0)
        self.assertEqual(by_machine["PK-9 Line 3"]["work_orders"], 1)
        self.assertEqual(by_machine["PK-9 Line 3"]["downtime_min"], 0.0)
        self.assertEqual(by_machine["CM-350 Line 1"]["downtime_min"], 0.0)

    def test_machine_endpoints_list_create_and_get(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/machines")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 3)

            response = client.post(
                "/api/machines",
                json={"id": "AHU-4", "model": "AHU", "location": "Roof"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["id"], "AHU-4")

            response = client.get("/api/machines/AHU-4")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["location"], "Roof")

            duplicate = client.post(
                "/api/machines",
                json={"id": "AHU-4", "model": "AHU", "location": "Roof"},
            )
            self.assertEqual(duplicate.status_code, 409)

            self.assertEqual(client.get("/api/machines/missing").status_code, 404)

    def test_health_check_endpoint(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "healthy")
            self.assertTrue(data["database"]["connected"])
            self.assertEqual(data["database"]["type"], "sqlite")
            self.assertIn("integrations", data)


if __name__ == "__main__":
    unittest.main()
