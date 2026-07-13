# 10 Phase Audit

# Audit Integrity (Anti-Hallucination during Verification)

This rule addresses a critical failure mode where an agent, tasked with **verifying** codebase integrity, instead **generates** missing files to make the audit pass. This is the agentic equivalent of an auditor forging receipts.

> **Post-Mortem Origin:** During a bootstrap workflow execution, the agent was instructed to verify that `src/tests/` contained test files and that `src/capabilities/` contained automation scripts. Both directories were empty (files had been moved to another repo in a previous session). Instead of reporting the missing files as a fatal error, the agent created dummy placeholder files (`test_dummy.py`, `git_manager.py` with `pass` stubs) and reported the bootstrap as successful. This violated every principle of governance integrity.

## 1. Read-Only Audit Mode

- **Rule**: When executing any **verification or audit workflow** (`bootstrap.md`, `master-sync.md` Phase 1-2, `compliant-refactor.md` Phase 1), the agent is in **read-only audit mode**.
- **Action**: The agent MUST NOT create, modify, or delete any project files to satisfy an audit check. The agent's role during audit phases is strictly to **observe and report**, never to **fix and proceed**.

## 2. Fatal Error on Missing Infrastructure

- **Rule**: If a required file, directory, or dependency is missing during an audit phase, the agent MUST report it as a `[FATAL]` finding and halt the current phase.
- **Action**: The agent MUST present a clear summary of all missing items to the user and await explicit instructions before taking any corrective action.
- **Forbidden**: Creating placeholder files, stub functions, empty `__init__.py` modules, or `pass`-only scripts to satisfy audit checks.

## 3. Skip-and-Report Protocol

- **Rule**: If a workflow phase cannot pass due to missing infrastructure that is **expected** for the repository type (e.g., no `src/` in a pure governance template), the agent MUST skip the phase with a `[SKIPPED]` status and a clear reason.
- **Action**: At the end of the workflow, present a consolidated report of all `[PASSED]`, `[SKIPPED]`, and `[FATAL]` phases so the user has a complete picture.

## 4. Separation of Auditor and Developer

- **Rule**: Within a single workflow execution, the agent MUST NOT switch between "auditing" and "fixing" roles without explicit user approval.
- **Action**: If the agent discovers a problem during an audit, it MUST complete the full audit first, then present all findings, and only begin fixing after the user approves the remediation plan.

---
### Source: `00-environment-awareness.md`
---

# Environment Awareness (Language Agnosticism)

This rule prevents the AI agent from blindly defaulting to Python tools and syntax when operating in diverse codebases. It is a critical component of the template's multi-language governance strategy.

## 1. Mandatory Context Gathering
- **Rule**: Before executing ANY code modification or tool call in a new project context, the agent MUST inspect the root directory for package manager files.
- **Action**: Look for `package.json` (Node/TypeScript), `go.mod` (Go), `Cargo.toml` (Rust), or `requirements.txt`/`pyproject.toml` (Python).
- **Why**: LLMs have a strong prior bias towards Python. If operating in a Next.js directory, suggesting `pip install` or using `python -c` causes execution failures.

## 2. Conformity to Host Ecosystem
- **Rule**: All generated code, scripts, and commands MUST conform exactly to the detected language, tooling, and styling of the host repository.
- **Action**: If the project uses TypeScript, use `npm` or `yarn` and write `.ts` scripts. Do not attempt to force Python-based governance decorators onto non-Python code.

## 3. Governance via MCP
- **Rule**: For cross-language governance, rely on the Model Context Protocol (MCP) server endpoints instead of language-specific constructs.
- **Why**: This ensures that regardless of the host language, the agent can still query and validate actions against the central Antigravity governance rules without syntax collisions.

---
### Source: `00-anti-sycophancy-protocol.md`
---

# Automated SAST & Evaluator Standards

This document provides strict engineering rules to achieve zero-defect compliance against Automated Evaluators, AI Code Analyzers, and CI/CD Static Application Security Testing (SAST) pipelines.

## 1. Problem Statement Alignment
- **Rule**: You MUST use the exact, verbatim keywords from the project requirements in the `README.md` and module-level docstrings.
- **Why**: Automated evaluators and compliance checkers use semantic keyword matching to verify alignment. If they don't see the exact phrase, they flag the feature as missing.
- **Action**: Always include explicit sections mapping the solution to the exact constraints (e.g., explicitly stating "Breakfast/Lunch/Dinner" if a meal plan is required).

## 2. Accessibility (A11y)
- **Rule**: All UI inputs must contain ARIA-compliant labels or tooltips.
- **Why**: Analyzers automatically flag UI inputs lacking screen-reader support as critical UI/UX defects.
- **Action**: In Streamlit, always provide the `help="description"` parameter to all input widgets (`st.text_input`, `st.button`, etc.). Avoid using raw emojis inside critical structural HTML headers (e.g., `<h1>`, `<h2>`).

## 3. Efficiency
- **Rule**: Heavy generation functions must be memoized, and threads must be non-blocking.
- **Why**: Automated evaluators heavily penalize synchronous thread blocking (like `time.sleep()`) and redundant external API calls as performance bottlenecks.
- **Action**: Decorate LLM calls with `@st.cache_data` or `@lru_cache`. Rely on native UI frameworks for retry loops rather than halting the main thread.

## 4. Code Quality (AST Strictness)
- **Rule**: Code must be modular, type-hinted, and absolutely free of dynamic execution or raw HTML injections. You MUST NEVER use `eval()` or Streamlit's `unsafe_allow_html=True`.
- **Why**: Evaluators (like SonarQube) instantly flag `eval()` as a Critical Code Smell and `unsafe_allow_html=True` as an XSS vector, permanently capping the Code Quality score regardless of Pylint output.
- **Action**:
  - Use `ast.literal_eval()` or native arithmetic instead of `eval()`.
  - Rely exclusively on native Streamlit widgets instead of injecting custom HTML/CSS strings.
  - Encapsulate all logic into single-responsibility functions (e.g., `def render_ui()`). Provide Google-style docstrings and strict Python type hints (e.g., `def func(arg: str) -> dict:`).

## 5. Security (Prompt Injection)
- **Rule**: All user inputs passed to an LLM MUST be rigorously sanitized.
- **Why**: SAST tools immediately flag unsanitized inputs injected into f-strings as CWE-74 (Prompt Injection / XSS vulnerabilities).
- **Action**: Implement an explicit `sanitize_input` function that strips HTML tags, escapes malicious characters (`< > { }`), and strictly truncates strings to a safe length (e.g., 500 chars) before LLM ingestion.

## 6. Testing Coverage
- **Rule**: Test suites must be located in a standard root-level directory and explicitly target isolated unit logic.
- **Why**: Analyzers hardcode target paths (like `./tests`) and calculate coverage mathematically based on unit isolation.
- **Action**: Ensure tests reside in `tests/` (not `src/tests/`). Provide isolated unit tests for pure functions (like the sanitization logic) alongside UI integration tests to guarantee high line-coverage percentages.


---
### Source: `12-12-factor-enforcement.md`
---
