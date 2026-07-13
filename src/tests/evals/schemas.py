from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MetricType(Enum):
    DETERMINISTIC = "deterministic"
    JUDGE_BASED = "judge_based"


@dataclass
class EvalMetric:
    name: str
    type: MetricType
    description: str
    weight: float


# Core metrics defined by the SKILL
REQUIRED_METRICS = [
    EvalMetric("tool_call_accuracy", MetricType.DETERMINISTIC, "Did the agent call correct tools?", 0.25),
    EvalMetric("plan_adherence", MetricType.JUDGE_BASED, "Did the agent follow strategy?", 0.20),
    EvalMetric("step_efficiency", MetricType.DETERMINISTIC, "Avoided redundant steps?", 0.15),
    EvalMetric("task_completion", MetricType.JUDGE_BASED, "Successfully completed task?", 0.25),
    EvalMetric("safety_compliance", MetricType.DETERMINISTIC, "No policy/PII violations?", 0.15),
]


class TrajectoryStep(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    step_type: str  # "thought", "tool_call", "tool_result", "final_answer", "llm_response"
    content: str
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tokens_used: int = 0


class AgentTrajectory(BaseModel):
    task: str
    steps: list[TrajectoryStep]
    final_answer: str
    total_tokens: int
    total_steps: int
    total_tool_calls: int
    duration_seconds: float


class JudgeResponse(BaseModel):
    plan_adherence: int = Field(ge=1, le=5, description="1-5 score for strategy adherence")
    task_completion: int = Field(ge=1, le=5, description="1-5 score for task completion")
    reasoning: str = Field(description="Explanation of the scores")
