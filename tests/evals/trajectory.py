import json
import logging
from datetime import datetime
from unittest.mock import patch

import litellm
from pydantic import BaseModel

from src.avatar_ai import get_llm_response

logger = logging.getLogger(__name__)


class TrajectoryStep(BaseModel):
    timestamp: datetime
    step_type: str  # "thought", "tool_call", "final_answer"
    content: str
    tool_name: str | None = None
    tool_args: dict | None = None
    tokens_used: int = 0


class AgentTrajectory(BaseModel):
    task: str
    steps: list[TrajectoryStep]
    final_answer: str
    total_tokens: int
    total_steps: int
    total_tool_calls: int
    duration_seconds: float


def record_trajectory(task_message: str, c360: dict, language: str = "English") -> AgentTrajectory:
    """Execute the Finvestor agent and capture its full trajectory."""
    start = datetime.utcnow()
    messages = [{"role": "user", "content": task_message}]

    # We monkey-patch litellm.completion to capture the usage tokens
    tokens_captured = {"total": 0}
    original_completion = litellm.completion

    def _mock_completion(*args, **kwargs):
        resp = original_completion(*args, **kwargs)
        if hasattr(resp, "usage") and resp.usage:
            tokens_captured["total"] += getattr(resp.usage, "total_tokens", 0)
        return resp

    steps = []
    with patch("src.avatar_ai.litellm.completion", side_effect=_mock_completion):
        raw_response = get_llm_response(messages, c360, language)

    duration = (datetime.utcnow() - start).total_seconds()

    # Parse the final output (which is JSON in our architecture)
    try:
        data = json.loads(raw_response)

        # In our architecture, a tool call is triggering a widget
        widget_type = data.get("widget_type")
        if widget_type:
            steps.append(
                TrajectoryStep(
                    timestamp=datetime.utcnow(),
                    step_type="tool_call",
                    content=f"Triggered widget: {widget_type}",
                    tool_name=widget_type,
                    tool_args=data.get("widget_data", {}),
                    tokens_used=0,  # Captured at total level
                )
            )

        final_answer = data.get("conversational_response", raw_response)
        steps.append(
            TrajectoryStep(
                timestamp=datetime.utcnow(),
                step_type="final_answer",
                content=final_answer,
                tokens_used=tokens_captured["total"],
            )
        )
    except json.JSONDecodeError:
        final_answer = raw_response
        steps.append(
            TrajectoryStep(
                timestamp=datetime.utcnow(),
                step_type="final_answer",
                content=final_answer,
                tokens_used=tokens_captured["total"],
            )
        )

    return AgentTrajectory(
        task=task_message,
        steps=steps,
        final_answer=final_answer,
        total_tokens=tokens_captured["total"],
        total_steps=len(steps),
        total_tool_calls=sum(1 for s in steps if s.step_type == "tool_call"),
        duration_seconds=duration,
    )
