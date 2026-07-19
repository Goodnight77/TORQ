import unittest
from unittest.mock import patch, MagicMock
from torq.agent.schemas import Diagnosis
from torq.workorder.generate import build_work_order, _translate

class TranslationFallbackTests(unittest.TestCase):
    @patch("torq.workorder.generate.OpenAI")
    @patch("torq.workorder.generate.settings")
    def test_translate_failure_fallback_empty_dict(self, mock_settings, mock_openai):
        """Verify that when OpenAI API throws an exception, _translate returns an empty dict instead of crashing."""
        mock_settings.llm_api_key = "fake-key"
        mock_settings.llm_base_url = "fake-url"
        mock_settings.llm_model = "fake-model"
        mock_settings.translate_timeout = 10
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API rate limit exceeded")
        mock_openai.return_value = mock_client
        
        result = _translate("WORK ORDER DETAILS")
        self.assertEqual(result, {})

    @patch("torq.workorder.generate.OpenAI")
    @patch("torq.workorder.generate.settings")
    def test_translate_invalid_json_fallback_empty_dict(self, mock_settings, mock_openai):
        """Verify that if OpenAI returns invalid JSON, _translate handles it gracefully."""
        mock_settings.llm_api_key = "fake-key"
        mock_settings.llm_base_url = "fake-url"
        mock_settings.llm_model = "fake-model"
        mock_settings.translate_timeout = 10
        
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="not a json object"))]
        mock_client.chat.completions.create.value = mock_resp
        mock_openai.return_value = mock_client
        
        result = _translate("WORK ORDER DETAILS")
        self.assertEqual(result, {})
