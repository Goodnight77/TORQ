"""Tests that diagnose.py routes through MCP and falls back to direct retrieval."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from torq.agent.diagnose import _fetch_history, _fetch_manuals


# ── _fetch_manuals ───────────────────────────────────────────────────────────


class TestFetchManuals:
    """Verify MCP-first retrieval with direct fallback for manuals."""

    @pytest.fixture(autouse=True)
    def _enable_mcp(self):
        # These tests exercise the MCP path, so pretend a networked Qdrant is set.
        with patch("torq.agent.diagnose.mcp_available", return_value=True):
            yield

    MCP_HITS = [
        {"source": "pump_manual.pdf", "text": "Check impeller for cavitation"},
    ]

    DIRECT_HITS = [
        {"source": "pump_manual.pdf", "document": "Check impeller for cavitation"},
    ]

    @patch("torq.agent.diagnose.mcp_search_manuals")
    def test_mcp_success(self, mock_mcp):
        """When MCP returns results, use them directly (no fallback)."""
        mock_mcp.return_value = self.MCP_HITS

        result = _fetch_manuals("E-201 cavitation")

        mock_mcp.assert_called_once()
        assert result == self.MCP_HITS

    @patch("torq.agent.diagnose.search")
    @patch("torq.agent.diagnose.mcp_search_manuals")
    def test_mcp_failure_falls_back(self, mock_mcp, mock_search):
        """When MCP returns None, fall back to direct ingest.search."""
        mock_mcp.return_value = None
        mock_search.return_value = self.DIRECT_HITS

        result = _fetch_manuals("E-201 cavitation")

        mock_mcp.assert_called_once()
        mock_search.assert_called_once()
        # Result is re-shaped to MCP schema
        assert result[0]["text"] == "Check impeller for cavitation"

    @patch("torq.agent.diagnose.mcp_search_manuals")
    def test_mcp_empty_is_not_failure(self, mock_mcp):
        """An empty list from MCP is a valid result (no fallback)."""
        mock_mcp.return_value = []

        result = _fetch_manuals("nonexistent fault")

        mock_mcp.assert_called_once()
        assert result == []


# ── _fetch_history ───────────────────────────────────────────────────────────


class TestFetchHistory:
    """Verify MCP-first retrieval with direct fallback for history."""

    @pytest.fixture(autouse=True)
    def _enable_mcp(self):
        with patch("torq.agent.diagnose.mcp_available", return_value=True):
            yield

    MCP_HITS = [
        {
            "id": "REP-042",
            "machine": "CNC-LatheA",
            "fault_code": "E-201",
            "root_cause": "worn seal",
            "fix": "replaced seal",
            "notes": "recurring issue",
        },
    ]

    DIRECT_HITS = [
        {
            "id": "REP-042",
            "machine": "CNC-LatheA",
            "fault_code": "E-201",
            "root_cause": "worn seal",
            "fix": "replaced seal",
            "technician_notes": "recurring issue",
        },
    ]

    @patch("torq.agent.diagnose.mcp_search_history")
    def test_mcp_success(self, mock_mcp):
        """When MCP returns results, use them directly."""
        mock_mcp.return_value = self.MCP_HITS

        result = _fetch_history("E-201", machine="CNC-LatheA")

        assert mock_mcp.call_count >= 1
        assert result == self.MCP_HITS

    @patch("torq.agent.diagnose.search")
    @patch("torq.agent.diagnose.mcp_search_history")
    def test_mcp_failure_falls_back(self, mock_mcp, mock_search):
        """When MCP returns None, fall back to direct search."""
        mock_mcp.return_value = None
        mock_search.return_value = self.DIRECT_HITS

        result = _fetch_history("E-201", machine="CNC-LatheA")

        mock_mcp.assert_called_once()
        assert mock_search.call_count >= 1
        # Result is re-shaped to MCP schema (technician_notes → notes)
        assert result[0]["notes"] == "recurring issue"

    @patch("torq.agent.diagnose.mcp_search_history")
    def test_mcp_machine_empty_retries_without_filter(self, mock_mcp):
        """Machine-specific MCP search returns [], should retry without machine."""
        mock_mcp.side_effect = [[], self.MCP_HITS]

        result = _fetch_history("E-201", machine="CNC-LatheA")

        assert mock_mcp.call_count == 2
        assert result == self.MCP_HITS

    @patch("torq.agent.diagnose.search")
    @patch("torq.agent.diagnose.mcp_search_history")
    def test_fallback_machine_empty_retries(self, mock_mcp, mock_search):
        """Direct fallback also retries without machine filter on empty results."""
        mock_mcp.return_value = None
        mock_search.side_effect = [[], self.DIRECT_HITS]

        result = _fetch_history("E-201", machine="CNC-LatheA")

        assert mock_search.call_count == 2

    @patch("torq.agent.diagnose.mcp_search_history")
    def test_mcp_machine_empty_retry_fails_returns_list(self, mock_mcp):
        """Machine search empty, then retry fails (None): must return [], never None."""
        mock_mcp.side_effect = [[], None]

        result = _fetch_history("E-201", machine="CNC-LatheA")

        assert result == []  # not None -> _join_history won't crash


# ── MCP gating: embedded Qdrant must not attempt MCP ─────────────────────────


class TestMcpGating:
    """When MCP is unavailable (embedded Qdrant), skip it and go direct."""

    @patch("torq.agent.diagnose.search", return_value=[])
    @patch("torq.agent.diagnose.mcp_search_manuals")
    @patch("torq.agent.diagnose.mcp_available", return_value=False)
    def test_manuals_skips_mcp_when_unavailable(self, _avail, mock_mcp, mock_search):
        _fetch_manuals("E-201")
        mock_mcp.assert_not_called()
        mock_search.assert_called_once()

    @patch("torq.agent.diagnose.search", return_value=[])
    @patch("torq.agent.diagnose.mcp_search_history")
    @patch("torq.agent.diagnose.mcp_available", return_value=False)
    def test_history_skips_mcp_when_unavailable(self, _avail, mock_mcp, mock_search):
        _fetch_history("E-201", machine="CNC-LatheA")
        mock_mcp.assert_not_called()
        assert mock_search.call_count >= 1


# ── _extract_list: FastMCP result parsing ────────────────────────────────────


class TestExtractList:
    """Whole list must be recovered, not just content[0]."""

    def test_prefers_structured_content(self):
        from torq.mcp.client import _extract_list

        items = [{"id": "A"}, {"id": "B"}]
        # content is one block PER item; structuredContent holds the full list.
        result = SimpleNamespace(
            structuredContent={"result": items},
            content=[SimpleNamespace(text='{"id": "A"}'), SimpleNamespace(text='{"id": "B"}')],
        )
        assert _extract_list(result) == items

    def test_rebuilds_from_content_blocks(self):
        from torq.mcp.client import _extract_list

        # No structured payload (older server): rebuild from per-item blocks.
        result = SimpleNamespace(
            structuredContent=None,
            content=[SimpleNamespace(text='{"id": "A"}'), SimpleNamespace(text='{"id": "B"}')],
        )
        assert _extract_list(result) == [{"id": "A"}, {"id": "B"}]

    def test_empty_list(self):
        from torq.mcp.client import _extract_list

        result = SimpleNamespace(structuredContent={"result": []}, content=[])
        assert _extract_list(result) == []
