# 40 Phase Deploy

# 30-MASTER-compliance-and-deploy




---
### Source: `31-30-MASTER-compliance-and-deploy.md`
---

---
description: Critical constraints and requirements for deploying applications to Hugging Face Spaces.
---

# Hugging Face Spaces Deployment Standards

To ensure zero-cost, permanent offsite availability, applications are deployed to Hugging Face (HF) Spaces. Any changes to the architecture, dependencies, or deployment pipeline MUST adhere to the following constraints to prevent regressions or build failures.

## 1. Network & Container Constraints
* **Port Binding:** HF Spaces routes external traffic strictly to port `7860`. The application server must bind to `0.0.0.0:7860`.
* **Privilege Level:** The Docker container must run as a non-root user (uid `1000`).
* **Workers:** Free tier Spaces only allocate 2 vCPUs and 16GB RAM. Run the ASGI server with a single worker (`--workers 1`) to prevent OOM kills and CPU starvation.

## 2. Dependency Locking
* **Pin All Dependencies:** Always use pinned or range-locked versions in `requirements.txt` to prevent Docker build failures caused by upstream breaking changes.
* **Known Conflict:** If using `python-telegram-bot`, it strictly requires `httpx~=0.26.0`. Never upgrade `httpx` to `>=0.27.0` alongside it.

## 3. Deployment Mechanism (CI/CD ONLY)
* **No Git Push:** Do NOT use `git push` directly to the Hugging Face remote to avoid large file issues (LFS) and credential complexities.
* **Use the SDK:** Always deploy using the custom `upload_to_hf.py` script via the Hugging Face Hub SDK.
* **CRITICAL:** Do NOT run `upload_to_hf.py` locally. It must ONLY be executed by the `.github/workflows/deploy_hf.yml` GitHub Action runner which securely accesses the `HF_TOKEN`. All deployment triggers must happen via `git push origin main`.

## 4. UI Integration
* **Single Endpoint:** The Space exposes a single web port. If the application requires multiple interfaces (e.g., a dashboard and a chat console), they must be served on `/` via a unified, tabbed interface to maximize utility without requiring multi-container setups (which HF free tier does not support).


---
### Source: `32-30-MASTER-compliance-and-deploy.md`
---

---
name: Sync Upstream (Backport)
description: Safely backports locally hardened rules and workflows to the upstream Antigravity template repository without raising conflicts.
---

# Sync Upstream Workflow

This workflow automates the backporting of newly hardened rules and workflows from the local project to the master `Antigravity_Environment_Max` template repository. It solves the issue of keeping the upstream template expanded without triggering painful Git merge conflicts.

## Strategy: Local as Source of Truth
When an agent hardens a rule locally (e.g., after a post-mortem), the local `.agents/` folder becomes the most advanced version of the framework. Therefore, the upstream repository should simply **adopt** the local changes entirely.

## Execution Steps

1. **Identify Hardened Rules via Git**
   - The agent MUST use Git to programmatically identify modified framework files. Run commands like `git diff --name-status origin/main...HEAD .agents/` or check `git log` to find all newly created or modified rules, workflows, and skills inside the `.agents/` directory.
   - Rely entirely on Git as the index. There is no need to maintain a manual tracking file.

2. **Generate the Handover Template**
   - DO NOT pollute the main repository `HANDOVER.md` (which is reserved for LLM context switching).
   - Create or overwrite `docs/handover-template.md`.
   - Document the exact file paths of the modified `.agents/` files that need to be upstreamed, alongside a brief summary of the diff/changes (e.g., "Added Pydantic validation to prevent data loss").

3. **Human-in-the-Loop Sync**
   - DO NOT attempt to run automated `git clone` or aggressive `rm -rf` operations to force-copy the files. This strictly adheres to `.agents/rules/00-MASTER-safety-and-guardrails.md`.
   - Inform the user that `docs/handover-template.md` has been generated. The developer will use this isolated checklist to manually copy-paste the modified files into the `Antigravity_Environment_Max` template repository.


---
### Source: `33-30-MASTER-compliance-and-deploy.md`
---

# Meta-Agent Formats and Templates

This file acts as the ultimate structural template repository for all AI Agents operating within this workspace. When instructed to produce rules, proposals, reviews, or summaries, agents MUST strictly adhere to the formats defined below.

## 1. Rule Entry Template
Use this template when adding or refactoring reusable rules in the `.agents/rules/` directory.

```markdown
### Rule: <RULE_ID>
- Owner layer: Global | Domain | Project
- Scope: [where this rule applies]
- Stability: core | behavior | experimental
- Status: active | superseded | draft
- Directive: [clear imperative rule]
- Rationale: [why this rule exists]
- Conflict handling: [what overrides this rule or when to escalate]
- Example: [positive example]
- Non-example: [what this rule forbids or does not cover]
```
*Requirement: `Directive`, `Rationale`, and `Conflict handling` must never be omitted.*

## 2. Deliverable / Proposal Template
Use this template when an agent acts as a planner, architect, or the "Generator" phase of an LLM Council.

```markdown
## Deliverable: [title]

### Proposal
[What is being proposed — the solution, plan, or finding]

### Alternatives considered
[At least one alternative approach and why it was not chosen]

### Pros / Cons
| Pros | Cons |
|------|------|
| ...  | ...  |

### Risks
[Each risk with likelihood, impact, and mitigation — or "None identified"]

### Recommendation
[Clear, actionable recommendation for the user or the next agent]
```

## 3. Review / Audit Output Template
Use this template for review-first roles (like `risk-reviewer` or the "Peer Review" phase of the LLM Council).

```markdown
## Review: [title]

### Findings
- [severity] [file:line] [issue]

### Open questions / assumptions
- [question or assumption]

### Residual risks
- [remaining risk after review, or "None"]

### Summary
[Short conclusion: Accept / Accept with changes / Reject with reason.]
```

## 4. Execution Checkpoint Template
Use this template when an agent encounters ambiguity, high-risk operations, or requires human approval before proceeding.

```markdown
## Checkpoint: [gate name]

**Current state**: [what has been done so far]
**Proposal**: [what will happen next]
**Risks**: [what could go wrong]
**Decision needed**: [specific yes/no or choice the user must make]

Waiting for approval before proceeding.
```
