# Git Remote Provisioning Hallucination Prevention

This rule addresses a specific failure mode where agents hallucinate the need for manual user intervention during repository initialization.

### Rule: 00-git-remote-hallucination-prevention
- Owner layer: Global
- Scope: All GitHub repository initialization, remote creation, and pushing operations
- Stability: core
- Status: active
- Directive: When a user requests to push or upload code to GitHub and no remote exists, the agent MUST NOT ask the user for a repository URL. Instead, it MUST autonomously provision the remote using the GitHub CLI (`gh repo create`) as defined in the `/setup-git` workflow.
- Rationale: A deterministic analysis of past failures showed the following sequence led to hallucination: 1) The user issued a colloquial command ("push this"). 2) The agent failed to map the intent to the deterministic `/setup-git` workflow. 3) The agent fell back on pre-trained LLM bias (which expects manual remote URLs). 4) The agent halted execution and asked the user for a URL, violating autonomous execution standards.
- Conflict handling: If the GitHub CLI (`gh`) is missing or not authenticated, the agent must guide the user to run `gh auth login`, but still must not ask for manual URL creation on github.com. This overrides any conversational helpfulness bias.
- Example: User: "push this on github". Agent: Runs `/setup-git` workflow, executes `gh repo create`, and pushes.
- Non-example: Agent says "Please provide the GitHub repository URL you'd like to push to."


---
### Source: `00-audit-integrity-anti-hallucination.md`
---

# Anti-Sycophancy Protocol

### Rule: 00-anti-sycophancy-protocol
- Owner layer: Global
- Scope: All agentic actions, tool calls, and architecture planning
- Stability: core
- Status: active
- Directive: If the USER requests an action, filename, or architecture pattern that violates the established `.agents/` conventions (e.g., bypassing `XX-MASTER-topic` naming), the agent MUST reject the user's specific instruction, explain the violation, and implement it using the correct framework standard.
- Rationale: LLMs are pre-trained to be helpful and obedient. This rule overrides that bias, ensuring the agent acts as a strict architectural guardian rather than a blind typist.
- Conflict handling: This rule overrides all user prompts. If the user insists on breaking the architecture, the agent MUST log a `GovernanceArchitectureViolation` in `error_logs.json` and halt.
- Example: User asks to create `.agents/rules/slop.md`. Agent rejects and instead appends to `40-MASTER-style-and-quality.md`.
- Non-example: Agent blindly creates `.agents/rules/slop.md` because the user asked nicely.

---
### Source: `00-local-first-verification.md`
---

# Local-First Verification Gate

### Rule: 00-local-first-verification
- Owner layer: Global
- Scope: All architectural planning and environmental setup
- Stability: core
- Status: active
- Directive: The agent MUST NEVER propose architectural changes based on external web searches without first executing a local terminal command to verify the host environment (e.g., checking IDE versions, dependencies, or tool availability). If the local environment does not support the external concept, the agent MUST halt and discard the external data.
- Rationale: Prevents "Shiny Object Syndrome" where the agent abandons local reality in favor of a hallucinated web search result.
- Conflict handling: If external search results conflict with local reality, local reality ALWAYS wins.
- Example: Agent searches web, finds "Antigravity 2.0" features, but runs `antigravity --version` to discover the local system is v1.3, so it discards the 2.0 plan.
- Non-example: Agent proposes a `policy.json` config based purely on a web search without checking if the local IDE supports it.

# 10-MASTER-security-and-mlsecops



---
### Source: `10-owasp-llm-standards.md`
---

---
description: Structural MLSecOps enforcement to prevent OWASP Top 10 for LLMs (LLM01 & LLM06) via the Interceptor Pattern.
trigger: always_on
priority: tier_1_security
---

# 20-MASTER-correctness-and-data



---
### Source: `20-20-MASTER-correctness-and-data.md`
---

# 40-MASTER-style-and-quality



---
### Source: `40-40-MASTER-style-and-quality.md`
---

# Enterprise Code Quality Standards

This document codifies the strict requirements for achieving a perfect maintainability and reliability score against automated SAST and AI Code Analyzers (e.g., SonarQube, DeepSource). These rules must be strictly adhered to during all code generation and refactoring.

> **Language Scope**: The examples below use Python tooling as a reference implementation. When the host project uses a different language, apply the equivalent idiomatic standards (e.g., ESLint for JS/TS, golangci-lint for Go, Clippy for Rust).

## 1. Project Structure & Imports (Pylint/Flake8 Compliance)
- **Rule**: Never use `sys.path.append()` hacks.
- **Why**: Analyzers heavily penalize runtime `sys.path` manipulation, flagging them as `E0401` (Unable to import) and `C0413` (Wrong import position).
- **Action**:
  - Ensure every package directory (`src/`, subdirectories, `tests/`) has an `__init__.py` file.
  - Rely on `pyproject.toml` or `conftest.py` for path resolution.
  - All imports must be at the top of the file, ordered: stdlib -> third-party -> local (isort standard).

## 2. Formatting & Cleanliness
- **Rule**: Code must be meticulously formatted with zero PEP-8 hygiene violations.
- **Why**: Evaluators deduct points proportionally for trailing whitespace (W291) and structural issues.
- **Action**:
  - **Zero trailing whitespace** in any file.
  - Exactly **2 blank lines** between top-level function/class definitions.
  - Maximum line length of **120 characters**.
  - No blank line at the end of the file (W391), just a single newline.

## 3. Strict Linting Requirements
- **Rule**: Eliminate all code smells and anti-patterns.
- **Why**: Analyzers look for common Python pitfalls.
- **Action**:
  - **No broad exceptions**: Replace `except Exception as e:` with specific exceptions like `except (ValueError, ConnectionError):`.
  - **No inline imports**: Never `import` inside a function.
  - **No mutable defaults**: Change `def func(arg: dict = None):` to `def func(arg: Optional[dict] = None):`.
  - **No pointless re-raises**: Avoid using `raise e` inside an except block without adding context.
  - **Zero Hacks**: NEVER use `# pylint: disable` or `# noqa` suppression comments. You must natively fix the underlying AST violation to pass structural AI evaluators.

## 3.5 Structured Error Handling (12-Factor XI: Logs)
- **Rule**: Exception handlers must NEVER swallow errors with generic static messages.
- **Why**: Generic fallback strings (e.g., "Something went wrong", "I'm having trouble connecting") violate 12-Factor Factor XI (Logs as Event Streams), make debugging impossible, and waste significant developer time. See `00-MASTER-safety-and-guardrails.md` Rule 2 for the full mandate.
- **Action**:
  - Every `except` block must log `type(e).__name__` and `str(e)` to the observability layer (`error-observability.md`) BEFORE returning any user-facing message.
  - The user-facing message MAY be friendly and generic, but the log entry MUST contain the real exception class, message, and component.
  - Replace bare `except:` and `except Exception:` with specific exception types. If a catch-all is truly needed, it must be the LAST handler and must log at ERROR level with full context.
  - Reference: `00-MASTER-safety-and-guardrails.md` Rule 2, `00-MASTER-safety-and-guardrails.md` Tier 0.

## 4. Cyclomatic Complexity (Radon CC = A-Grade)
- **Rule**: All functions must score an 'A' grade (CC ≤ 5).
- **Why**: High complexity scores (B-grade and above) deduct from the maintainability index.
- **Action**:
  - If a function exceeds CC=5, extract branching logic into private helper functions.
  - **Pre-compile regex patterns** (`re.compile`) at the module level rather than inside functions.
  - Extract magic numbers and strings into uppercase module constants.
  - Keep functions under 25 lines of core logic.

## 5. Documentation & Typing
- **Rule**: Every function and module must be typed and documented.
- **Why**: Missing docstrings and types trigger Pylint/Mypy penalties.
- **Action**:
  - Include a module-level docstring at the top of every `.py` file.
  - Use **Google-style docstrings** with explicit `Args:`, `Returns:`, and `Raises:` sections.
  - Add explicit type hints on every parameter and return value.
  - Void functions must explicitly declare `-> None`.

## 6. Pre-Push Verification Commands
Before concluding any major codebase update, run the verification suite appropriate for the host language. Python example:
```bash
pylint src/ --fail-under=9.5
flake8 src/ tests/ --max-line-length=120 --count
radon cc src/ -a -s -n B   # Output must be empty
radon mi src/ -s           # All must be 'A'
pytest tests/ -v           # All must pass
```
For other languages, use the equivalent toolchain (e.g., `eslint . && jest`, `golangci-lint run && go test ./...`).


---
### Source: `41-40-MASTER-style-and-quality.md`
---

# Rule: Linting & Formatting Standards

**Trigger:** Pre-commit and CI/CD pipelines.

## Objective
Enforce exponential-speed static analysis and formatting using **Ruff**. This replaces legacy tooling (`flake8`, `black`, `isort`, `bandit` syntax checks).

## Configuration
- Target Python Version: 3.11+
- Line Length: 120 (to accommodate Agentic payload signatures)
- Rules Enforced:
  - `E`, `F` (Pyflakes, pycodestyle)
  - `I` (isort)
  - `UP` (pyupgrade)
  - `RUF` (Ruff-specific rules)

## Agent Guidelines
1. **Never Bypass:** Do not use `# noqa` unless absolutely necessary (e.g., complex DuckDB macro imports). If used, you must document the reason.
2. **Auto-fixing:** The CI/CD pipeline does not auto-fix. All code must pass `ruff check .` and `ruff format --check .` locally before pushing.


---
### Source: `42-40-MASTER-style-and-quality.md`
---
