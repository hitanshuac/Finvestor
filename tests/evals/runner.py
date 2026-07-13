import json
import logging
from typing import Any

from tests.evals.metrics import eval_safety_compliance, eval_step_efficiency, eval_tool_call_accuracy, eval_with_judge
from tests.evals.trajectory import record_trajectory

logger = logging.getLogger(__name__)


def run_eval_suite(
    test_cases: list[dict[str, Any]],
    c360: dict[str, Any],
    output_path: str = "eval_results.json",
) -> dict[str, Any]:
    """Run a full evaluation suite across given test cases. Compatible with CI/CD."""
    results = []
    for case in test_cases:
        trajectory = record_trajectory(case["task"], c360=c360, language=case.get("language", "English"))

        # Deterministic metrics
        tool_accuracy = eval_tool_call_accuracy(trajectory, case.get("expected_tools", []))
        step_efficiency = eval_step_efficiency(trajectory, case.get("max_steps", 2))
        safety = eval_safety_compliance(trajectory)

        # Judge-based metrics
        judge_scores = eval_with_judge(trajectory)

        score = (
            0.25 * tool_accuracy
            + 0.20 * judge_scores["plan_adherence"]
            + 0.15 * step_efficiency
            + 0.25 * judge_scores["task_completion"]
            + 0.15 * safety
        )

        results.append(
            {
                "task": case["task"],
                "overall_score": round(score, 3),
                "tool_accuracy": tool_accuracy,
                "plan_adherence": judge_scores["plan_adherence"],
                "step_efficiency": step_efficiency,
                "task_completion": judge_scores["task_completion"],
                "safety": safety,
                "total_tokens": trajectory.total_tokens,
                "total_steps": trajectory.total_steps,
                "judge_reasoning": judge_scores["reasoning"],
            }
        )

    summary = {
        "total_cases": len(results),
        "avg_score": round(sum(r["overall_score"] for r in results) / len(results) if results else 0, 3),
        "pass_rate": sum(1 for r in results if r["overall_score"] >= 0.7) / len(results) if results else 0,
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary
