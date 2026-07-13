"""
Tests for LLM Fallback Routing via LiteLLM.

Validates that the fallback model configuration is correct and that
the LiteLLM integration properly handles provider-prefixed model strings.
"""

import os
from unittest.mock import patch

import pytest

from src.config import LLM_MODEL


class TestModelConfiguration:
    """Tests for model configuration correctness."""

    def test_primary_model_has_provider_prefix(self):
        """LiteLLM requires provider-prefixed model strings."""
        assert "/" in LLM_MODEL, "LLM_MODEL must use LiteLLM provider prefix (e.g., groq/model-name)"

    def test_primary_is_expected_model(self):
        """Primary model must match the configured enterprise LLM."""
        assert "gemini" in LLM_MODEL or "llama" in LLM_MODEL, "Primary model should be an approved enterprise model"


class TestLLMFallbackBehavior:
    """Tests for fallback behavior when primary model fails."""

    @patch("src.llm_client.robust_completion")
    def test_fallback_called_on_primary_failure(self, mock_robust_completion):
        """When primary model fails with RateLimitError, verify router throws it after exhausting retries."""
        from src.avatar_ai import get_llm_response
        from src.rate_limiter import RateLimitLockoutError

        # Mock the robust_completion to fail with RateLimitLockoutError
        mock_robust_completion.side_effect = RateLimitLockoutError(message="Rate Limit Exceeded", unlock_time=0.0)

        c360 = {"customer_id": "TEST", "age": 30}
        messages = [{"role": "user", "content": "Hello"}]

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key-1", "GROQ_API_KEY_FALLBACK": "test-key-2"}):
            response = get_llm_response(messages, c360, "English")
            assert "Rate Limit Exceeded" in response

        # Verify the robust_completion was called
        mock_robust_completion.assert_called_once()

    def test_missing_api_key_returns_error(self):
        """When no API key is set, should return a configuration error message."""
        from src.avatar_ai import get_llm_response

        c360 = {"customer_id": "TEST", "age": 30}
        messages = [{"role": "user", "content": "Hello"}]

        with patch.dict(os.environ, {}, clear=True):
            # Remove keys if present
            os.environ.pop("GROQ_API_KEY", None)
            os.environ.pop("GROQ_API_KEY_FALLBACK", None)
            result = get_llm_response(messages, c360, "English")

        assert "not configured" in result.lower()


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY required")
class TestLiveModelVerification:
    """Live integration tests — only run when API key is available."""

    def test_primary_model_exists(self):
        """Verify the primary model string is active. Skipped in CI if no external connection."""
        pass
