import json
from unittest.mock import patch

import litellm
import pytest

from src.avatar_ai import get_llm_response
from src.config import CUSTOMER_PROFILES
from src.rate_limiter import RateLimitLockoutError


@pytest.fixture
def dummy_c360():
    return CUSTOMER_PROFILES["102"]

@pytest.fixture
def dummy_messages():
    return [{"role": "user", "content": "Test."}]

@patch("src.llm_client.robust_completion")
def test_avatar_rate_limit_lockout(mock_completion, dummy_messages, dummy_c360):
    """Ensure RateLimitLockoutError safely degrades to a friendly conversational response."""
    mock_completion.side_effect = RateLimitLockoutError("Locked out", unlock_time=0.0)

    response_str = get_llm_response(dummy_messages, dummy_c360, "English")
    response = json.loads(response_str)

    assert "Rate Limit Exceeded" in response["conversational_response"]
    assert response["follow_up_question"] == ""
    assert response["recommended_tips"] == []

@patch("src.llm_client.robust_completion")
def test_avatar_api_connection_error(mock_completion, dummy_messages, dummy_c360):
    """Ensure APIConnectionError safely degrades."""
    mock_completion.side_effect = litellm.APIConnectionError(message="Network down", llm_provider="groq", model="llama-3")

    response_str = get_llm_response(dummy_messages, dummy_c360, "English")
    response = json.loads(response_str)

    assert "Unable to connect" in response["conversational_response"]

@patch("src.llm_client.robust_completion")
def test_avatar_authentication_error(mock_completion, dummy_messages, dummy_c360):
    """Ensure AuthenticationError safely degrades."""
    mock_completion.side_effect = litellm.AuthenticationError(message="Invalid API Key", llm_provider="groq", model="llama-3")

    response_str = get_llm_response(dummy_messages, dummy_c360, "English")
    response = json.loads(response_str)

    assert "API authentication failed" in response["conversational_response"]

@patch("src.llm_client.robust_completion")
def test_avatar_generic_exception(mock_completion, dummy_messages, dummy_c360):
    """Ensure generic Exceptions safely degrade."""
    mock_completion.side_effect = ValueError("Some weird error")

    response_str = get_llm_response(dummy_messages, dummy_c360, "English")
    response = json.loads(response_str)

    assert "unexpected error" in response["conversational_response"]
