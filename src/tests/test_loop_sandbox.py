from dataclasses import dataclass
from pathlib import Path

import pytest

# ─── MOCKED LOOP ORCHESTRATOR ──────────────────────────────────────────────

@dataclass
class LoopReport:
    signal: str | None = None
    files: list[str] = None
    notes: str = ""

class SecurityViolation(Exception):
    pass

class LoopOrchestrator:
    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = Path(sandbox_dir).resolve()
        self.max_retries = 1

    def execute_agent_loop(self, agent_function, initial_context: str):
        """Simulates a cron-triggered loop evaluating an agent function."""
        retries = 0
        state = initial_context

        while True:
            # Agent does work and returns a report
            report = agent_function(state)

            # Security Check: Verify Path Constraints
            if report.files:
                for file_path in report.files:
                    target_path = (self.sandbox_dir / file_path).resolve()
                    if not str(target_path).startswith(str(self.sandbox_dir)):
                        raise SecurityViolation(f"Unauthorized path traversal detected: {file_path}")

            # Verification Gate: Strict Signal Contract
            if report.signal == "done":
                return "SUCCESS"

            if report.signal in ["stuck", "plan-assumption-broken"] or not report.signal:
                if retries < self.max_retries:
                    retries += 1
                    state = f"RETRY_CONTEXT: Previous loop failed with signal {report.signal}"
                    continue
                else:
                    return "ESCALATED_TO_HUMAN"

            # If signal is completely invalid, treat as stuck
            if retries < self.max_retries:
                retries += 1
                state = "RETRY_CONTEXT: Invalid signal"
                continue
            else:
                return "ESCALATED_TO_HUMAN"

# ─── TEST SUITE ────────────────────────────────────────────────────────────

def test_verification_gate_contract(tmp_path):
    """Asserts that if the report lacks the mandatory signal, it halts."""
    orchestrator = LoopOrchestrator(sandbox_dir=str(tmp_path))

    # Agent that never returns a valid signal
    def bad_agent(state):
        return LoopReport(signal=None)

    result = orchestrator.execute_agent_loop(bad_agent, "START")
    assert result == "ESCALATED_TO_HUMAN"

    # Agent that succeeds immediately
    def good_agent(state):
        return LoopReport(signal="done")

    result = orchestrator.execute_agent_loop(good_agent, "START")
    assert result == "SUCCESS"

def test_single_retry_escalation(tmp_path):
    """Asserts the orchestrator grants exactly 1 retry loop before escalating."""
    orchestrator = LoopOrchestrator(sandbox_dir=str(tmp_path))
    attempts = 0

    def stuck_agent(state):
        nonlocal attempts
        attempts += 1
        return LoopReport(signal="stuck")

    result = orchestrator.execute_agent_loop(stuck_agent, "START")

    assert result == "ESCALATED_TO_HUMAN"
    assert attempts == 2  # 1 initial try + 1 targeted retry

def test_sandbox_path_constraints(tmp_path):
    """Asserts that the file-memory is sandboxed to a specific directory."""
    orchestrator = LoopOrchestrator(sandbox_dir=str(tmp_path))

    # Agent attempts to traverse upwards
    def malicious_agent(state):
        return LoopReport(signal="done", files=["../../../etc/passwd"])

    with pytest.raises(SecurityViolation) as exc:
        orchestrator.execute_agent_loop(malicious_agent, "START")

    assert "Unauthorized path traversal detected" in str(exc.value)

def test_successful_retry_recovery(tmp_path):
    """Asserts that an agent can recover on its targeted retry."""
    orchestrator = LoopOrchestrator(sandbox_dir=str(tmp_path))
    attempts = 0

    def learning_agent(state):
        nonlocal attempts
        attempts += 1
        if "RETRY_CONTEXT" in state:
            # Agent fixes the issue based on retry context
            return LoopReport(signal="done", files=["LOG.md"])
        return LoopReport(signal="stuck", files=["LOG.md"])

    result = orchestrator.execute_agent_loop(learning_agent, "START")

    assert result == "SUCCESS"
    assert attempts == 2
