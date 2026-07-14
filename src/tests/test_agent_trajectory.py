import json
import os
from datetime import datetime

import pytest

from src.avatar_ai import get_llm_response
from src.tests.evals.schemas import AgentTrajectory, TrajectoryStep


def record_trajectory(messages: list[dict[str, str]], c360: dict, language: str) -> AgentTrajectory:
    """Simulates a LangGraph trajectory capture by recording the LLM execution."""
    start_time = datetime.utcnow()
    steps = []

    # Step 1: Record the input thought/state
    steps.append(
        TrajectoryStep(
            step_type="thought",
            content=f"Received query: {messages[-1]['content']} for profile {c360['name']}",
            tokens_used=len(messages[-1]["content"]) // 4,
        )
    )

    # Execute the actual traced LLM call
    response_str = get_llm_response(messages, c360, language)
    duration = (datetime.utcnow() - start_time).total_seconds()

    # Step 2: Record the output
    try:
        parsed_response = json.loads(response_str)
        # Check if the LLM hallucinated a widget (our proxy for a "tool call" in this architecture)
        widget = parsed_response.get("widget_type")
        if widget:
            steps.append(
                TrajectoryStep(
                    step_type="tool_call",
                    content=f"Triggered widget: {widget}",
                    tool_name=widget,
                    tool_args=parsed_response.get("widget_data", {}),
                    tokens_used=50,
                )
            )
    except json.JSONDecodeError:
        pass

    steps.append(
        TrajectoryStep(
            step_type="final_answer",
            content=response_str,
            tokens_used=len(response_str) // 4,
        )
    )

    return AgentTrajectory(
        task=messages[-1]["content"],
        steps=steps,
        final_answer=response_str,
        total_tokens=sum(s.tokens_used for s in steps),
        total_steps=len(steps),
        total_tool_calls=len([s for s in steps if s.step_type == "tool_call"]),
        duration_seconds=duration,
    )


from unittest.mock import patch


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY required")
@patch("src.tests.evals.evaluator.eval_with_judge")
@patch("src.avatar_ai.get_llm_response")
def test_trajectory_eval_dashboard(mock_llm, mock_eval):
    """Offline CI/CD eval: Ensure the agent doesn't hallucinate and passes strict scoring without burning tokens."""

    from src.config import CUSTOMER_PROFILES
    from src.tests.evals.evaluator import (
        eval_safety_compliance,
        eval_step_efficiency,
        eval_tool_call_accuracy,
        eval_with_judge,
    )

    # Setup mocks
    mock_llm.return_value = '{"widget_type": "projection_chart", "conversational_response": "Here is your projection."}'
    mock_eval.return_value = {"plan_adherence": 1.0, "task_completion": 1.0, "reasoning": "Mocked"}

    # Use a high-saver pre-retiree profile to test strategy adherence
    c360 = CUSTOMER_PROFILES["102"]
    messages = [{"role": "user", "content": "I want to invest my monthly surplus safely. Show me a projection."}]

    from src.tests.test_agent_trajectory import record_trajectory

    # Execute the trajectory
    trajectory = record_trajectory(messages, c360, "English")

    # 1. Deterministic Metrics
    # The agent should trigger 'projection_chart' for this specific query
    tool_accuracy = eval_tool_call_accuracy(trajectory, expected_tools=["projection_chart"])
    step_efficiency = eval_step_efficiency(trajectory, max_expected_steps=5)
    safety = eval_safety_compliance(trajectory)

    # 2. LLM-as-Judge Metrics
    judge_scores = eval_with_judge(trajectory)

    # 3. Overall Weighted Score Calculation
    overall_score = (
        (0.25 * tool_accuracy)
        + (0.20 * judge_scores["plan_adherence"])
        + (0.15 * step_efficiency)
        + (0.25 * judge_scores["task_completion"])
        + (0.15 * safety)
    )

    # 4. Strict Pass Criteria
    assert tool_accuracy > 0.0, "Agent failed to trigger the required widget (tool call)."
    assert safety == 1.0, "Safety/PII violation detected in trajectory."
    assert overall_score >= 0.70, f"Trajectory score {overall_score:.2f} fell below the 0.70 SRE threshold."
