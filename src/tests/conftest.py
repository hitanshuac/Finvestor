
import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Ensure tests never hit real APIs by mocking environment variables if not set,
    but also intercepting actual calls globally if possible."""
    monkeypatch.setenv("GROQ_API_KEY", "mock-groq-key-for-tests")
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock-openrouter-key-for-tests")


@pytest.fixture
def mock_llm_trajectory(monkeypatch):
    """Mocks the direct get_llm_response call specifically for the trajectory tests."""
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    mock_llm.return_value = '{"widget_type": "projection_chart", "conversational_response": "Here is your projection."}'
    monkeypatch.setattr("src.tests.test_agent_trajectory.get_llm_response", mock_llm)
    return mock_llm


@pytest.fixture
def mock_judge_eval(monkeypatch):
    """Mocks the LLM-as-a-judge evaluator."""
    from unittest.mock import MagicMock
    mock_eval = MagicMock()
    mock_eval.return_value = {"plan_adherence": 1.0, "task_completion": 1.0, "reasoning": "Mocked"}
    monkeypatch.setattr("src.tests.test_agent_trajectory.eval_with_judge", mock_eval)
    return mock_eval
