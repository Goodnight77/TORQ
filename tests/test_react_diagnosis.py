"""Tests for the multi-step (ReAct) diagnosis agent and its single-shot fallback."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from torq.agent.diagnose import (
    _diagnose_oneshot,
    _diagnose_react,
    _merge_sources,
    diagnose,
)
from torq.agent.schemas import Diagnosis


def _msg(content: str) -> SimpleNamespace:
    return SimpleNamespace(content=content)


class TestMergeSources:
    def test_dedupes_and_skips_empty(self):
        data = {"sources": ["A"]}
        _merge_sources(data, ["A", "B", "", None, "B"])
        assert data["sources"] == ["A", "B"]

    def test_creates_field_when_missing(self):
        data: dict = {}
        _merge_sources(data, ["X"])
        assert data["sources"] == ["X"]


class TestDiagnoseReact:
    @patch("langchain_openai.ChatOpenAI")
    @patch("langgraph.prebuilt.create_react_agent")
    def test_returns_diagnosis_with_injected_ids(self, mock_create, _mock_chat):
        """Final agent message is parsed; fault_code/machine come from the caller."""
        agent = MagicMock()
        agent.invoke.return_value = {
            "messages": [
                _msg('{"root_cause": "worn seal", "confidence": 0.8, "sources": ["REP-1"]}')
            ]
        }
        mock_create.return_value = agent

        result = _diagnose_react("E-201", "CNC-LatheA", "")

        assert isinstance(result, Diagnosis)
        assert result.root_cause == "worn seal"
        assert result.fault_code == "E-201"
        assert result.machine == "CNC-LatheA"
        assert "REP-1" in result.sources

    @patch("langchain_openai.ChatOpenAI")
    @patch("langgraph.prebuilt.create_react_agent")
    def test_parses_fenced_json(self, mock_create, _mock_chat):
        agent = MagicMock()
        agent.invoke.return_value = {
            "messages": [_msg('```json\n{"root_cause": "cavitation"}\n```')]
        }
        mock_create.return_value = agent

        result = _diagnose_react("P-260", "Pump 3", "")

        assert result.root_cause == "cavitation"


class TestFallback:
    @patch("torq.agent.diagnose._diagnose_oneshot")
    @patch("torq.agent.diagnose._diagnose_react")
    def test_react_failure_falls_back(self, mock_react, mock_oneshot):
        mock_react.side_effect = RuntimeError("model has no tool support")
        sentinel = Diagnosis(fault_code="E-201", root_cause="fallback")
        mock_oneshot.return_value = sentinel

        result = diagnose("E-201", "CNC-LatheA")

        mock_react.assert_called_once()
        mock_oneshot.assert_called_once_with("E-201", "CNC-LatheA", "")
        assert result is sentinel

    @patch("torq.agent.diagnose._diagnose_react")
    def test_react_success_skips_fallback(self, mock_react):
        sentinel = Diagnosis(fault_code="E-201", root_cause="react")
        mock_react.return_value = sentinel

        assert diagnose("E-201") is sentinel


class TestOneshot:
    @patch("torq.agent.diagnose._fetch_history", return_value=[])
    @patch("torq.agent.diagnose._fetch_manuals", return_value=[])
    @patch("torq.agent.diagnose._chat")
    def test_parses_and_returns_diagnosis(self, mock_chat, _m, _h):
        mock_chat.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=_msg('{"root_cause": "worn seal"}'))]
        )

        result = _diagnose_oneshot("E-201", "CNC-LatheA", "")

        assert result.root_cause == "worn seal"
        assert result.fault_code == "E-201"
