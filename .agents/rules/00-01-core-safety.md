# Deterministic Guardrails Protocol

This is a Tier 0 Master Rule. LLMs are probability engines, not human developers. Conversational English, weak modals, and implicit instructions drastically increase the hallucination probability. This rule dictates how all other rules, workflows, and skills MUST be interpreted and written.

## 1. No Weak Modals
- You MUST interpret all instructions as absolute constraints.
- Words like "MUST", "could", "MUST", or "strictly" are strictly forbidden in all agentic documentation. Treat any existing weak modals as "MUST".

## 2. Positive Framing over Negative Banning
- Do NOT use negative framing (e.g., "do not use raw SQL").
- ALWAYS use positive boundary framing (e.g., "ONLY use DuckDB Pydantic models"). Negative framing injects the forbidden concept into the context window, increasing hallucination probability.

## 3. Strict Command Sandboxing
- Workflow files MUST NOT use abstract verbs for tooling (e.g., "Execute the Git tool").
- Every executable action MUST provide the exact CLI string required, sandboxed inside markdown backticks (e.g., `git add . && git commit -m "message" && git push`).
- If a workflow step lacks an exact CLI string, you MUST halt and ask the user for clarification. Do not hallucinate a command to fulfill the abstract intent.

## 4. Architectural Adherence (XML Boundaries)
- Where possible, instructions and constraints MUST be enclosed in strict XML tags (e.g., `<trigger>`, `<action>`, `<constraint>`) to provide explicit semantic boundaries for the LLM context window.

> **Post-Mortem Origin:** This master rule was implemented after an LLM Council analysis identified that conversational English, split instructions, and weak modals were the root cause of multiple agentic IDE hallucinations, including the bypass of the secure checkpoint workflow.


---
### Source: `00-git-ban.md`
---

# Git Version Control Protocol

This rule ensures all version control operations go through the governance checkpoint workflow for observability and consistency.

## 1. Mandatory Checkpoint Workflow
- **Rule**: All Git commit-and-push operations MUST be routed through the `.agents/workflows/secure-checkpoint.md` workflow.
- **Why**: Direct ad-hoc git commands bypass error observability, skip pre-commit hooks, and can result in local checkpoints that fail to synchronize with remote state.

## 2. Acceptable Git Commands
- **Read-only commands** are always permitted: `git status`, `git log`, `git diff`, `git remote -v`, `git branch`.
- **State-changing commands** (`git add`, `git commit`, `git push`, `git reset`, `git rebase`) MUST be executed as part of the `secure-checkpoint.md` workflow, not as one-off ad-hoc commands.
- **Exception**: If the host project provides a custom Git management script (e.g., `src/capabilities/git_manager.py`), use that instead of raw git commands per `secure-checkpoint.md`.

## 3. Workflow Annotations
- If a workflow file contains a `// turbo` flag next to a checkpoint instruction, it authorizes auto-running the checkpoint workflow. It does NOT authorize arbitrary git commands outside the workflow.

> **Post-Mortem Origin:** This rule was enacted after an LLM Council analysis identified that agents were overriding workflow scripts due to pre-training bias when encountering generic terms like "stage, commit, and push".


---
### Source: `00-idempotency-standards.md`
---

# Idempotency Standards

This rule mandates that all database operations, especially those interacting with DuckDB, must be fully idempotent.

## Directives

1. **No Duplicate Records:** Running the same write or insert operation multiple times must yield the exact same database state as running it once.
2. **Use INSERT OR REPLACE:** When writing to DuckDB, always use `INSERT OR REPLACE INTO ...` instead of `INSERT INTO ...` to prevent duplication on retry loops.
3. **Primary Keys:** Ensure every table has a strongly defined primary key or unique constraint to support the `REPLACE` mechanism.
4. **Data Integrity:** Idempotent operations are critical for fault tolerance, allowing Agentic pipelines to safely retry failed runs without corrupting data state.


---
### Source: `00-no-unauthorized-deletions.md`
---

# Rule 00: The No-Deletion Mandate

**Strict Enforcement:** This rule overrides all other workflows, scripts, and instructions.

1. **Never Delete Without Explicit Approval:** Under no circumstances is the AI agent allowed to automatically execute deletion commands (e.g., `Remove-Item`, `rm -rf`) against an existing project directory or file.
2. **Conflict Resolution:** If a file from this Base Environment collides with an existing file in the target project, the incoming file supersedes the existing one *only after* the conflict has been presented to the user and manually approved.
3. **Non-Destructive Enhancer:** This repository acts strictly as a booster/enhancer to existing projects. It must never act destructively.
4. **Semantic Merge Exemption:** The Autonomous Semantic Merge Protocol defined in `.agents/workflows/merge-conflict-resolution.md` (union merges for `.gitignore`, dependency appends for `requirements.txt`, and isolated `AGENT_DOCS.md` linking for `README.md`) does **NOT** constitute deletion or overwriting. These non-destructive, additive operations are explicitly exempt from the manual approval requirement above.


---
### Source: `00-quota-optimization.md`
---

# Quota Optimization & Anti-Drain Rules

These rules are strictly enforced to prevent excessive API quota drain during autonomous agent execution.

## 1. No Unprompted Reconnaissance
Do not perform exhaustive workspace searches (e.g., recursive grepping, digging through unrelated `package.json` or `README.md` files) to find missing subjective data like names, emails, or API keys. If data is missing from the target file, immediately use a placeholder (e.g., `[NAME]`) or stop and ask the user.

## 2. Ban Micro-Execution (REPL Anti-Pattern)
Do not use `python -c` or bash commands for step-by-step, line-by-line debugging of strings, regexes, or variables. If you need to debug data processing, write a single comprehensive script that outputs all necessary diagnostic information at once, run it, and read the output.

## 3. Restrict Browser Subagent Usage
Do not invoke the `browser_subagent` merely for visual verification of intermediate CSS/HTML tweaks unless UI/UX validation is the primary, explicitly stated goal of the task. Rely on structural checks or output files for the user to review.

## 4. Optimistic Execution
Assume standard Python libraries or node modules are available or installable as needed. Do not waste turns running arbitrary "check if X is installed" commands before writing the actual code. Write the code, run it, and catch the `ImportError` or `ModuleNotFoundError` if it fails.


---
### Source: `00-00-MASTER-safety-and-guardrails.md`
---

---
description: Establishes a strict priority hierarchy for resolving conflicts between rules and workflows.
trigger: always_on
priority: tier_0_safety
---

# Rule Conflict Resolution Protocol

When two or more `.agents/rules/` files issue contradictory instructions, the agent MUST NOT silently pick one over the other. This rule establishes a deterministic resolution hierarchy.

> **Post-Mortem Origin:** This rule was created after a root-cause analysis where a "no databases" project constraint (Tier 3) silently overrode `20-MASTER-correctness-and-data.md` (Tier 2), causing the agent to use raw `json.load()` without schema validation. The resulting code silently wiped the error log file. A priority hierarchy would have forced the agent to find a non-database implementation of schema validation (e.g., Pydantic) instead of skipping validation entirely.

## 1. Rule Priority Hierarchy

Rules are organized into 5 tiers. Higher tiers ALWAYS take precedence over lower tiers.

| Tier | Category | Rules | Rationale |
|---|---|---|---|
| **0** | **Safety (Data Integrity)** | `00-MASTER-safety-and-guardrails.md`, `00-MASTER-safety-and-guardrails.md` | Preventing data loss is non-negotiable |
| **1** | **Security** | `10-MASTER-security-and-mlsecops.md` Rule 5 (CWE-74), `10-MASTER-security-and-mlsecops.md` Factor III (secrets) | Security vulnerabilities are career-ending |
| **2** | **Correctness** | `20-MASTER-correctness-and-data.md`, `20-MASTER-correctness-and-data.md`, `20-MASTER-correctness-and-data.md`, `error-observability.md` | Correct behavior trumps style and compliance |
| **3** | **Compliance** | `project-specific-rules.md`, `compliance-standards.md`, `10-MASTER-security-and-mlsecops.md`, `30-MASTER-compliance-and-deploy.md` | Platform rules are important but negotiable in implementation |
| **4** | **Style** | `40-MASTER-style-and-quality.md`, `40-MASTER-style-and-quality.md`, `40-MASTER-style-and-quality.md` | Code style is the least critical dimension |

## 2. Conflict Resolution Protocol

When the agent detects a conflict between two rules from different tiers:

1. **Identify the Conflict:** Explicitly state which two rules conflict and what the contradiction is.
2. **Apply the Higher Tier:** The higher-tier rule wins. The lower-tier rule's intent must be satisfied through an alternative implementation that does not violate the higher-tier rule.
3. **Document the Override:** Add a code comment at the point of conflict: `# RULE OVERRIDE: [higher rule] takes precedence over [lower rule]. See 00-MASTER-safety-and-guardrails.md.`
4. **Log an ADR (if Architectural):** If the conflict resolution changes the system architecture (e.g., swapping DuckDB for Pydantic+JSON), record an ADR in `.agents/architecture/adrs/`.

### Example: "No Database" Constraint vs. Schema Validation

- **Conflict:** `project-specific-rules.md` (Tier 3) says "NEVER use heavy local databases." `00-MASTER-safety-and-guardrails.md` (Tier 0) says "ALL persistent data MUST be validated against a Pydantic schema."
- **Resolution:** Tier 0 wins. The agent MUST implement Pydantic schema validation. Since databases are forbidden, it uses Pydantic models to validate JSON files instead of DuckDB schemas. Both rules are satisfied.
- **Forbidden Resolution:** Skipping schema validation entirely because "we can't use a database."

## 3. Same-Tier Conflicts

When two rules from the SAME tier conflict:

1. The more specific rule takes precedence over the more general rule.
2. If specificity is equal, the agent MUST halt and ask the user for a decision.
3. The resolution must be documented as an ADR.

## 4. Workflow vs. Rule Conflicts

- **Rules** (`.agents/rules/`) define constraints that are ALWAYS active.
- **Workflows** (`.agents/workflows/`) define procedures that are invoked on demand.
- If a workflow step contradicts an always-on rule, the rule wins.
- The workflow step must be adapted to comply with the rule, not the other way around.


---
### Source: `00-git-remote-hallucination-prevention.md`
---
