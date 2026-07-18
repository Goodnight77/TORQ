"""Tests for the diagnosis cache: repeat faults skip recomputation within the TTL."""

import time
import unittest
from unittest.mock import patch

from torq.agent import diagnose as diag_mod
from torq.agent.schemas import Diagnosis
from torq.config import settings


def _diag() -> Diagnosis:
    # Fresh object per computation so cache copy-isolation is exercised.
    return Diagnosis(fault_code="E-201", root_cause="seized bearing", repair_steps=["swap bearing"])


class DiagnoseCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        diag_mod._CACHE.clear()
        # Mock the whole diagnosis computation (ReAct path) so the cache is tested
        # in isolation with no vector DB or network. call_count == cache misses.
        self._patcher = patch(
            "torq.agent.diagnose._diagnose_react", side_effect=lambda *a, **k: _diag()
        )
        self.mock_diag = self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        diag_mod._CACHE.clear()

    def test_repeat_fault_served_from_cache(self) -> None:
        d1 = diag_mod.diagnose("E-201", "CM-350")
        d2 = diag_mod.diagnose("E-201", "CM-350")
        self.assertEqual(self.mock_diag.call_count, 1)  # second call reused
        self.assertEqual(d1.root_cause, d2.root_cause)

    def test_distinct_keys_not_shared(self) -> None:
        diag_mod.diagnose("E-201", "CM-350")
        diag_mod.diagnose("J-108", "CM-350")  # different fault_code
        diag_mod.diagnose("E-201", "PK-9")  # different machine
        self.assertEqual(self.mock_diag.call_count, 3)

    def test_ttl_zero_disables_cache(self) -> None:
        with patch.object(settings, "diagnose_cache_ttl", 0):
            diag_mod.diagnose("E-201", "CM-350")
            diag_mod.diagnose("E-201", "CM-350")
        self.assertEqual(self.mock_diag.call_count, 2)

    def test_different_context_not_shared(self) -> None:
        diag_mod.diagnose("E-471", "CM-350", "overtemp after 6h runtime")
        diag_mod.diagnose("E-471", "CM-350", "recurring overtemp, lint buildup")
        self.assertEqual(self.mock_diag.call_count, 2)  # context busts the cache

    def test_expired_entry_recomputes(self) -> None:
        diag_mod.diagnose("E-201", "CM-350")
        # Force the cached entry to look expired.
        key = ("CM-350", "E-201", "")
        _exp, diag = diag_mod._CACHE[key]
        diag_mod._CACHE[key] = (time.monotonic() - 1, diag)
        diag_mod.diagnose("E-201", "CM-350")
        self.assertEqual(self.mock_diag.call_count, 2)

    def test_cache_copy_isolation(self) -> None:
        d1 = diag_mod.diagnose("E-201", "CM-350")
        d1.repair_steps.append("MUTATED")  # mutate the returned object
        d2 = diag_mod.diagnose("E-201", "CM-350")  # cache hit
        self.assertNotIn("MUTATED", d2.repair_steps)  # cache not poisoned


if __name__ == "__main__":
    unittest.main()
