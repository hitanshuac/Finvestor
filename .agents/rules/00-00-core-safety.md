# 00 Core Safety

# 00-MASTER-safety-and-guardrails



---
### Source: `00-00-MASTER-safety-and-guardrails.md`
---

# Agent Terminal Execution Constraint (Anti-Hallucination Protocol)

This rule defines the strict operational boundaries for the AI Agent when executing terminal commands, specifically targeting the prevention of synthetic data hallucination caused by asynchronous race conditions or failed executions.

## 1. Zero-Tolerance for Hallucinated Output
- **Rule**: If an exploratory or ad-hoc terminal command (e.g., `run_command`) fails with a non-zero exit code or encounters a missing dependency, the agent **MUST NEVER** attempt to answer the user's prompt based on anticipated success or pre-training priors.
- **Why**: Providing synthetic snippets when actual data is unavailable corrupts the user's trust and violates the core principles of data engineering.

## 2. Explicit Failure Reporting
- **Rule**: Upon a failed command execution, the agent MUST explicitly state to the user: "The command failed with [Error Message]."
- **Action**: Do not hide Python tracebacks, module not found errors, or syntax errors behind conversational apologies. Surface the exact exception.

## 3. Mandatory Re-Execution Loop
- **Rule**: If the agent attempts to autonomously fix the error (e.g., by running `pip install` or fixing a syntax error), it MUST explicitly re-run the original extraction/analysis command and successfully read the output BEFORE formulating a response about the data.
- **Action**: You must verify the exit code of the final command is `0` and wait for the `command_status` to return the real textual output before parsing it for the user.

## 4. Interaction with Other Rules
- This rule is considered Tier 0 (Safety & Truthfulness) under `00-MASTER-safety-and-guardrails.md`. It overrides any conversational bias to "be helpful" or "keep the chat moving." The truthfulness of the terminal output is absolute.

## 5. Meta-Agent SOP: Building New Rules
Because the Antigravity repository relies heavily on autonomous execution, any future AI Agent tasked with creating or modifying a rule in `.agents/rules/` MUST adhere strictly to the **Rule Entry Template** defined in `30-MASTER-compliance-and-deploy.md`.

If an agent builds a rule without following the exact `Scope`, `Stability`, `Directive`, `Rationale`, and `Conflict handling` structure, it is considered invalid.

### Checkpoints and Deliverables
When generating proposals, orchestrating council peer-reviews, or pausing for human intervention, the agent MUST use the precise formatting templates defined in `30-MASTER-compliance-and-deploy.md`.

### Hierarchy Checks
Before saving a new rule, the agent MUST run `grep_search` across `.agents/rules/` or view `00-MASTER-safety-and-guardrails.md` to ensure the new rule does not conflict with existing Tier 0 or Tier 1 safety constraints.


---
### Source: `00-agent-execution-standards.md`
---

# Agent Execution Standards

This rule governs the fundamental operational behaviors of any AI agent operating within or pulling from this environment.

## 1. Assert State Currency (Anti-Staleness Protocol)
AI agents have a tendency to hallucinate templates or operate blindly on stale local clones.
- **Rule:** You MUST always assert state currency by running `git pull origin main` immediately prior to executing read/scaffold workflows on any cloned reference repository.
- Ensure your context is 100% current before reading architectural workflows or applying templates.


---
### Source: `00-00-MASTER-safety-and-guardrails.md`
---

---
description: Defensive programming standards to prevent silent data corruption, schema mismatches, and error swallowing across all SDLC phases.
trigger: always_on
priority: tier_0_safety
---

# Defensive Programming Standards

This rule codifies senior-engineer defensive programming SOPs that prevent silent data loss, schema drift, and error obfuscation. It applies to ALL code generation, regardless of project constraints (e.g., strict rules, MVP, production).

> **Post-Mortem Origin:** This rule was created after a root-cause analysis where an agent silently wiped a JSON error log because it assumed a flat `[]` list schema while the existing file used a `{"session_errors": [...]}` dictionary. Unit tests passed because they ran against empty temp directories, never touching the real file.

## 1. Schema-First Data Contracts (Mandatory for All I/O)

- **Rule**: Before writing ANY code that reads or writes a persistent file (JSON, TOML, YAML, CSV, Parquet), the agent MUST first read the existing file (if it exists) and document its exact schema.
- **Why**: LLMs lose file-schema context after 100+ conversation steps. Without an explicit contract, the agent will make statistically probable assumptions about file structure that may silently destroy data.
- **Action**:
  - Define a Pydantic model or `TypedDict` at module level for every persistent data structure. Raw `json.load()` followed by `isinstance()` type-guessing is **strictly forbidden**.
  - The Pydantic model is the **single source of truth**. If the existing file does not match the model, the code must raise a descriptive `ValueError` or `SchemaError` and halt. It must **NEVER** silently overwrite or reset the file.
  - When Pydantic is unavailable (e.g., dependency constraints), use Python `TypedDict` with explicit runtime validation using `assert` or `if not` guard clauses.

### Example (Correct):
```python
from pydantic import BaseModel

class ErrorLogEntry(BaseModel):
    timestamp: str
    error_type: str
    component: str
    message: str
    status: str  # "UNRESOLVED" | "RESOLVED"

# Module-level schema: the log file is a JSON array of ErrorLogEntry
ErrorLogSchema = list[ErrorLogEntry]
```

### Example (Forbidden):
```python

# FORBIDDEN: guessing the schema at runtime
logs = json.load(f)
if not isinstance(logs, list):
    logs = []  # THIS SILENTLY DESTROYS DATA
```

## 2. Fail Fast, Never Fail Silent

- **Rule**: Functions that interact with external services (APIs, file I/O, databases) MUST surface the actual error to the caller. Generic fallback strings without logging are forbidden.
- **Why**: Generic messages like "Something went wrong" or "I'm having trouble connecting" make debugging impossible and waste significant developer time.
- **Action**:
  - Every `except` block MUST log `type(e).__name__` and `str(e)` to the observability layer (see `error-observability.md`) BEFORE returning any user-facing message.
  - The user-facing message MAY be friendly and generic, but the log entry MUST contain the real exception class, message, and the component where it occurred.
  - Replace bare `except:` and `except Exception:` with specific exception types. If a catch-all is truly necessary, it must be the LAST handler and must log at ERROR level with full context.

### Example (Correct):
```python
except google.api_core.exceptions.ResourceExhausted as e:
    log_error_to_json("ResourceExhausted", "llm_engine", str(e))
    return fallback_message
except Exception as e:
    log_error_to_json(type(e).__name__, "llm_engine", str(e))
    return fallback_message
```

### Example (Forbidden):
```python
except Exception:
    return "I'm having trouble connecting right now."
```

## 3. Idempotent File Operations

- **Rule**: All file append operations MUST be idempotent. Running the same write operation twice must not corrupt, duplicate, or lose data.
- **Why**: Agentic pipelines frequently retry operations after crashes. Without idempotency, retries cause data duplication or loss.
- **Action**:
  - For JSON append operations: Read the file, deserialize, validate the schema, append the new entry, serialize, and write back atomically.
  - Use atomic write patterns where possible: write to a `.tmp` file first, then rename to the production path. This prevents partial writes from corrupting the file if the process crashes mid-write.
  - After every write, perform a post-write verification: re-read the file and assert `len(after) >= len(before)`. If the assertion fails, the write corrupted data and the agent must halt immediately.

## 4. Guard Clauses and Input Validation at Boundaries

- **Rule**: Every public function must validate its inputs in the first 3 lines using guard clauses.
- **Why**: Invalid inputs propagating deep into call stacks produce confusing, hard-to-trace errors.
- **Action**:
  - Validate type, nullability, and range at function entry.
  - Invalid inputs must raise `ValueError` or `TypeError` with a descriptive message including the parameter name and the invalid value.
  - Never trust data from disk, network, or user input. Always validate after deserialization.

### Example (Correct):
```python
def log_error_to_json(error_type: str, component: str, message: str) -> bool:
    if not error_type or not isinstance(error_type, str):
        raise ValueError(f"error_type must be a non-empty string, got: {error_type!r}")
    if not component or not isinstance(component, str):
        raise ValueError(f"component must be a non-empty string, got: {component!r}")
    # ... proceed with validated inputs
```

## 5. Relationship to Other Rules

- This rule is **Tier 0 (Safety)** in the rule priority hierarchy defined in `00-MASTER-safety-and-guardrails.md`.
- When project constraints (e.g., a "no databases" rule) conflict with this rule, the agent must find an alternative implementation that satisfies BOTH rules, not silently skip data integrity.
- Example: If DuckDB is forbidden, use Pydantic + JSON files instead of raw `json.load()` guessing. The schema validation mandate is non-negotiable.


---
### Source: `00-deterministic-guardrails.md`
---
