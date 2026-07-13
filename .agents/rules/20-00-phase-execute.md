# 20 Phase Execute

# OWASP LLM Security Standards (MLSecOps)

This is a Tier 1 Security Rule. AI agents and human developers are fundamentally unreliable at applying conversational security policies. Therefore, this repository enforces security via architectural physical barriers (The Interceptor Pattern).

## 1. The Raw Import Ban (Strictly Enforced)
- **Rule**: You are STRICTLY FORBIDDEN from importing raw LLM provider SDKs (e.g., `import openai`, `import anthropic`, `import google.generativeai`, `from langchain...`) anywhere in the application logic, UI, or API routing layers.
- **Why**: Raw imports allow developers and agents to bypass the security interceptor, exposing the system to Prompt Injection (LLM01).
- **Action**: The ONLY directory permitted to contain raw provider imports is `src/security/`. If you are writing code in `src/ui/` or `src/routers/`, you MUST use the Golden Wrapper.

## 2. The Golden Wrapper Mandate
- **Rule**: All interactions with external Large Language Models MUST be routed through the `SecureLLMClient` interceptor class.
- **Action**: When generating code that requires AI processing, you must import and instantiate `SecureLLMClient`. You will pass the raw user string to this client, and it will handle the secure network execution.

## 3. Bi-Directional Sanitization (Input & Output)
When modifying or extending the `SecureLLMClient`, you must enforce symmetry:
- **Pre-Flight (LLM01 Defense):** The wrapper must intercept the inbound payload and truncate it to a safe maximum length, strip raw HTML, and neutralize injection delimiters before sending it to the API.
- **Post-Flight (LLM06 Defense):** The wrapper must intercept the outbound response and scan it for Sensitive Information Disclosure (PII, leaked system prompts, or API keys) before returning it to the caller.

## 4. CI/CD Preflight Gate
- Before concluding any task involving LLM integration, you MUST verify that no raw SDK imports have leaked into the business logic. If a raw import is found outside of `src/security/`, you must immediately refactor it to use `SecureLLMClient`.


---
### Source: `11-10-MASTER-security-and-mlsecops.md`
---

# 12-Factor App Enforcement

This rule mandates that all code deployed within the Agentic Environment strictly adheres to the 12-Factor App methodology.

## Key Directives

1. **Codebase:** One codebase tracked in revision control, many deploys.
2. **Dependencies:** Explicitly declare and isolate dependencies (e.g., `requirements.txt`).
3. **Config:** Store configuration in the environment. **NEVER hardcode API keys or secrets.** Use `.env` locally or GitHub Secrets in CI/CD.
4. **Backing Services:** Treat backing services (databases, caches) as attached resources.
5. **Build, Release, Run:** Strictly separate build and run stages.
6. **Processes:** Execute the app as one or more stateless processes.
7. **Port Binding:** Export services via port binding (e.g., FastAPI on port 8000).
8. **Concurrency:** Scale out via the process model.
9. **Disposability:** Maximize robustness with fast startup and graceful shutdown.
10. **Dev/Prod Parity:** Keep development, staging, and production as similar as possible.
11. **Logs:** Treat logs as event streams. Do not manage log files directly (output to stdout/stderr), except for designated observability files like `data/error_logs.json`.
12. **Admin Processes:** Run admin/management tasks as one-off processes.


---
### Source: `13-10-MASTER-security-and-mlsecops.md`
---

---
name: 12-Factor Governance
description: Enforces all 12 factors of the 12-Factor App methodology for AI-generated architectural changes.
---

# 12-Factor App Methodology

When generating code, scaffolding architecture, or debugging issues within this repository, you MUST adhere to **all twelve** of the following principles. This repository is not a script; it is a **Production-Ready Agentic Environment**.

## Factor I: Codebase
*One codebase tracked in revision control, many deploys.*
- All architectural logic, including this very rule file, must be tracked in version control.
- Ensure the `.agents` folder is accurately updated when AI behavior needs to change globally.
- There is exactly one canonical repository. Deploys (dev, staging, production, HF Spaces) are all derived from this single codebase.

## Factor II: Dependencies
*Explicitly declare and isolate dependencies.*
- All Python dependencies must be declared in `requirements.txt` with pinned or range-locked versions.
- Never rely on implicit system-level packages. If a skill or workflow requires a library, it must be in `requirements.txt`.
- Use virtual environments (`.venv/`) for local isolation. The `.gitignore` must exclude `.venv/`.

## Factor III: Config
*Store config in the environment.*
- **STRICT PROHIBITION**: You are strictly forbidden from hardcoding API keys, secrets, or environment-specific connection strings into the source code (`src/`).
- Use the **BYOK (Bring Your Own Keys)** strategy. Configuration must be injected dynamically via environment variables (`os.environ`), `.secrets/` text files, or the `.config/antigravity/project_settings.toml` manifest.
- Config that varies between deploys (database URLs, API keys, ports) must never be committed to the repository.

## Factor IV: Backing Services
*Treat backing services as attached resources.*
- DuckDB databases, external APIs, message queues, and any third-party service must be treated as attached resources addressable via a URL or connection string stored in config (Factor III).
- The application must be able to swap a local DuckDB instance for a remote MotherDuck endpoint without code changes — only config changes.
- No backing service MUST be treated as "special." Local and third-party services are interchangeable.

## Factor V: Build, Release, Run
*Strictly separate build and run stages.*
- **Build:** Install dependencies, compile assets, run linting (`ruff check .`) and SAST (`semgrep ci`).
- **Release:** Combine the build with deploy-specific config. Tag with a semantic version via `python-semantic-release`.
- **Run:** Execute the application in the target environment. The run stage must never modify source code.
- These stages are strictly separated. You cannot patch code at runtime.

## Factor VI: Processes
*Execute the app as one or more stateless processes.*
- The application (e.g., FastAPI gateway) must execute **statelessly**.
- The router MUST hold no memory of past requests.
- Stateful persistence must be delegated to backing services (e.g., DuckDB telemetry, Parquet Dead-Letter Queues).
- Never store session state in local memory or the filesystem within `src/`.

## Factor VII: Port Binding
*Export services via port binding.*
- The application must be self-contained and bind to a port to serve requests.
- For Hugging Face Spaces: bind to `0.0.0.0:7860` (see `30-MASTER-compliance-and-deploy.md`).
- For local development: bind to `0.0.0.0:8000` (or as configured via environment variable `PORT`).
- No external web server injection (e.g., Apache, Nginx) MUST be assumed at the application layer.

## Factor VIII: Concurrency
*Scale out via the process model.*
- Design for horizontal scalability. Each process MUST be stateless (Factor VI) and disposable (Factor IX).
- On constrained environments (HF Spaces free tier), run a single worker (`--workers 1`) to avoid OOM kills.
- On production environments, scale by increasing the number of identical worker processes, not by adding threads to a monolith.

## Factor IX: Disposability
*Maximize robustness with fast startup and graceful shutdown.*
- Systems must gracefully handle sudden provider crashes.
- Do not let the main event loop freeze.
- Rely on Circuit Breakers (`error-recovery.md`) and Dead-Letter Queues (`data/quarantine_*.parquet`) to isolate faults and keep the system alive.
- Startup must be fast. Shutdown must flush all pending DuckDB WAL writes before exiting.

## Factor X: Dev/Prod Parity
*Keep development, staging, and production as similar as possible.*
- The same DuckDB schemas, Pydantic models, and FastAPI routes must be used across all environments.
- Avoid "works on my machine" by using the same `requirements.txt`, `ruff.toml`, and `.pre-commit-config.yaml` everywhere.
- Time gap (deploy quickly), personnel gap (developers who wrote it deploy it), and tools gap (same database engine everywhere) must all be minimized.

## Factor XI: Logs
*Treat logs as event streams.*
- Treat logs as continuous event streams. Never write to local log files within `src/`.
- Use lock-free background threadpools to push telemetry directly to the DuckDB metrics plane.
- In production, logs are captured by the runtime environment (Docker, HF Spaces). The application only writes to `stdout`/`stderr`.
- Document immutable architectural decisions natively in ADRs (`.agents/architecture/adrs/`).

### Factor XI Addendum: Lightweight Contexts
When 12-Factor Factor XI conflicts with project constraints that prohibit databases (see `00-MASTER-safety-and-guardrails.md` for priority hierarchy):
- Logs MAY be written to local JSON files as a fallback, but MUST still follow the Pydantic schema validation mandate from `20-MASTER-correctness-and-data.md` Rule 4 and `00-MASTER-safety-and-guardrails.md` Rule 1.
- The JSON log file is treated as a "poor man's event stream" and must be **append-only**. The agent must NEVER truncate, overwrite, or reset existing log entries.
- Before writing, a `.bak` backup must be created per `error-recovery.md` Step 3b.
- After writing, the Pre-Write Verification gate (`error-observability.md` Step 1.5) must confirm data integrity.

## Factor XII: Admin Processes
*Run admin/management tasks as one-off processes.*
- Database migrations, one-time data fixes, and diagnostic scripts must be run as isolated one-off commands, not baked into the application startup.
- Admin scripts MUST live in a dedicated `scripts/` directory (or be invoked via `python -m`) and use the same codebase and config as the running application.
- Never modify production data via ad-hoc SQL. Use versioned migration scripts that are idempotent.
