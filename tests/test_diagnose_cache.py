"""Tests for the diagnosis cache: repeat faults skip the LLM within the TTL."""

import time
import unittest
from unittest.mock import MagicMock, patch

from torq.agent import diagnose as diag_mod
from torq.config import settings


def _resp(content: str) -> MagicMock:
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


CANNED = '{"root_cause": "seized bearing", "repair_steps": ["swap bearing"]}'


class DiagnoseCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        diag_mod._CACHE.clear()
        # Patch retrieval + LLM so no vector DB or network is touched.
        self._patchers = {
            "man": patch("torq.agent.diagnose._fetch_manuals", return_value=[]),
            "hist": patch("torq.agent.diagnose._fetch_history", return_value=[]),
            "oai": patch("torq.agent.diagnose.OpenAI", return_value=MagicMock()),
            "chat": patch("torq.agent.diagnose._chat", return_value=_resp(CANNED)),
        }
        started = {name: p.start() for name, p in self._patchers.items()}
        self.mock_chat = started["chat"]

    def tearDown(self) -> None:
        for p in self._patchers.values():
            p.stop()
        diag_mod._CACHE.clear()

    def test_repeat_fault_served_from_cache(self) -> None:
        d1 = diag_mod.diagnose("E-201", "CM-350")
        d2 = diag_mod.diagnose("E-201", "CM-350")
        self.assertEqual(self.mock_chat.call_count, 1)  # second call reused
        self.assertEqual(d1.root_cause, d2.root_cause)

    def test_distinct_keys_not_shared(self) -> None:
        diag_mod.diagnose("E-201", "CM-350")
        diag_mod.diagnose("J-108", "CM-350")  # different fault_code
        diag_mod.diagnose("E-201", "PK-9")  # different machine
        self.assertEqual(self.mock_chat.call_count, 3)

    def test_ttl_zero_disables_cache(self) -> None:
        with patch.object(settings, "diagnose_cache_ttl", 0):
            diag_mod.diagnose("E-201", "CM-350")
            diag_mod.diagnose("E-201", "CM-350")
        self.assertEqual(self.mock_chat.call_count, 2)

    def test_expired_entry_recomputes(self) -> None:
        diag_mod.diagnose("E-201", "CM-350")
        # Force the cached entry to look expired.
        _exp, diag = diag_mod._CACHE[("CM-350", "E-201")]
        diag_mod._CACHE[("CM-350", "E-201")] = (time.monotonic() - 1, diag)
        diag_mod.diagnose("E-201", "CM-350")
        self.assertEqual(self.mock_chat.call_count, 2)

    def test_cache_copy_isolation(self) -> None:
        d1 = diag_mod.diagnose("E-201", "CM-350")
        d1.repair_steps.append("MUTATED")  # mutate the returned object
        d2 = diag_mod.diagnose("E-201", "CM-350")  # cache hit
        self.assertNotIn("MUTATED", d2.repair_steps)  # cache not poisoned


if __name__ == "__main__":
    unittest.main()
