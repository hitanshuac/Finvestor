# 30 Phase Test

# Testing Standards

This rule governs all testing practices across the Agentic Environment. It enforces industry-standard test structure, naming, and the strict prohibition of shipping untested code.

## 1. Never Ship Untested Code
- Every function, route, and pipeline component that is part of a ticket in `05_TICKETS.md` MUST have at least one corresponding test.
- If a ticket has no acceptance criteria, the agent must ask the user to define them before proceeding.
- Pull Requests with zero test coverage on new code MUST be rejected by CI.

## 2. Test Pyramid Enforcement
- **Unit Tests** must form the majority (~70%) of the test suite. They test pure logic in isolation with mocked dependencies.
- **Integration Tests** (~20%) test boundaries between components (e.g., API → database, validator → DLQ).
- **End-to-End Tests** (~10%) test the full user-facing flow. These are the most expensive and MUST be used sparingly.

## 2.5 State-Aware Integration Tests (Mandatory for I/O)

> **Post-Mortem Origin:** This rule was added after unit tests using Pytest `tmpdir` (clean-slate isolation) passed 100% but missed a critical schema mismatch with a real production file. The bug silently wiped `data/error_logs.json`.

- **Rule**: Any module that reads or writes persistent files (JSON, DB, Parquet) MUST have at least one integration test that operates on pre-populated fixture data matching the REAL production schema.
- **Why**: Unit tests with `tmpdir` only verify that code works on a clean slate. They cannot catch schema mismatches between what the code expects and what the data actually looks like.
- **Action**:
  - Create test fixtures in `tests/fixtures/` containing representative samples of real production data (e.g., `tests/fixtures/error_logs_sample.json`).
  - Integration tests must read from these fixtures, perform the operation (e.g., append a log entry), and verify no data was lost or corrupted.
  - At minimum, assert: `len(after) >= len(before)` for all append operations.
  - Fixtures must include edge cases: empty files, files with the canonical schema, and files with legacy schemas (e.g., the old dictionary format) to verify migration logic.
  - Reference: `00-MASTER-safety-and-guardrails.md` Rule 1 (Schema-First Data Contracts).

- Test files: Language-idiomatic naming (e.g., `test_<module>.py`, `<module>.test.ts`, `<module>_test.go`)
- Test functions: Descriptive names following the pattern `test_<feature>_<behavior>_<expected>` or framework equivalent
- Test classes (when grouping): `TestCompaction`, `TestDLQRouting`, or framework equivalent

## 4. Fixture & Setup Standards
- Shared fixtures must be defined using the framework's standard mechanism (e.g., `conftest.py` for pytest, `beforeEach` for Jest, `TestMain` for Go).
- Database tests must use in-memory instances (e.g., DuckDB `:memory:`) unless testing persistence specifically.
- API tests must use the framework's test client — never make real HTTP calls in unit tests.
- External API dependencies must be mocked using the language's standard mocking library.

## 5. Test Execution Protocol
- Tests must be run after **every** code change, not just at the end of a feature.
- Use the framework-appropriate test command (e.g., `python -m pytest src/tests/ -v --tb=short`, `npm test`, `go test ./...`).
- The CI/CD pipeline (`.github/workflows/main.yml`) must run the full test suite on every push.

## 5.5 Contract Tests for Data Schemas

- **Rule**: Every Pydantic model or `TypedDict` used for file I/O MUST have a corresponding contract test that validates a known-good fixture file against the model.
- **Why**: Contract tests catch schema drift between what the code expects and what the data actually looks like. They are the bridge between unit tests (which test logic) and integration tests (which test boundaries).
- **Action**:
  - Test file: `tests/test_contracts.py`
  - Each test loads a fixture file from `tests/fixtures/` and asserts it deserializes successfully through the Pydantic model without validation errors.
  - If a fixture fails validation, the TEST fails (not the app). This ensures schema changes are intentional and documented, not accidental.
  - Contract tests must run BEFORE integration tests in the test suite execution order.
  - Reference: `20-MASTER-correctness-and-data.md` Rule 4, `00-MASTER-safety-and-guardrails.md` Rule 1.

## 6. Failure Handling
- If a test fails, the agent must first check `.agents/workflows/error-observability.md` for historical context.
- The agent must fix the **implementation code**, not weaken the test, unless the test itself contains a genuine error.
- After 3 failed debugging iterations on the same test, the agent must flag it for manual user review and move on.

## 7. Anti-Solipsism Verification (Human Testing)
- **Rule:** Never rely solely on internal, solipsistic verification (reading your own terminal outputs).
- Always explicitly provide the human user with the exact, step-by-step UI and CLI testing commands required to run and test the full-stack system locally (e.g., how to start the backend, how to start the frontend, what URL to open) upon completion of any task.


---
### Source: `21-20-MASTER-correctness-and-data.md`
---

# Pydantic Data Validation Standards

This rule governs the data validation layer using Pydantic, focusing on fault tolerance and isolating bad records without halting the entire pipeline.

## 1. Non-Blocking Validation
- If incoming data violates the defined Pydantic schema, it must **NOT** crash the pipeline or raise an uncaught `ValidationError`.
- The pipeline must continue processing healthy records while safely isolating the malformed data.

## 2. Quarantine Protocol
- Any record that fails Pydantic validation must be caught and routed to a quarantine file.
- Save the bad records in a `.parquet` file located within the `data/` directory (e.g., `data/quarantine_YYYYMMDD.parquet`).
- Include the original payload and the specific validation error message in the quarantine record for manual review.

## 3. Graceful Degradation
- Allow partial batch successes. If a batch contains 90% valid data and 10% invalid data, the 90% must be ingested into DuckDB while the 10% is quarantined.
- Log a warning for SRE teams to review the quarantine file, but do not exit the pipeline with a non-zero status code solely due to validation failures.

## 4. File-Based Data Validation (Non-Database Contexts)

> **Post-Mortem Origin:** This rule was added after an incident where a JSON error log was silently wiped because the agent used raw `json.load()` + `isinstance()` instead of schema validation. The existing Rules 1-3 only covered DuckDB/pipeline contexts, leaving JSON files unprotected.

- **Rule**: When project constraints prohibit databases (e.g., strict client lightweight rules), the Pydantic validation mandate still applies to ALL persistent data files.
- **Why**: A JSON file is a schema-less database. Without validation, any code that reads it must guess the structure, and guesses can silently destroy data.
- **Action**:
  - Define a Pydantic model (or `TypedDict` with explicit validation) for every JSON/YAML/TOML file the application reads or writes.
  - Deserialize file content THROUGH the Pydantic model. If validation fails, route the error to the observability layer (`error-observability.md`) using the same quarantine pattern as Rule 2.
  - This rule applies even when the persistence layer is "just a JSON file." Treat it with the same rigor as DuckDB.
  - Reference: `00-MASTER-safety-and-guardrails.md` Rule 1, `00-MASTER-safety-and-guardrails.md` (Tier 0 Safety overrides Tier 3 Compliance).

## 5. Source Baseline Verification vs. Hallucinated Precision
- **Rule**: Never build highly specific tracking logic (e.g., splitting "Transit" into "CNG Bus", "Electric Bus", "AC Metro") unless the underlying reference dataset contains explicit, verified baseline KPIs for those exact sub-categories.
- **Why**: An idempotent system with mathematically robust logic is still generating a hallucination if the source baseline is unverified. Pretending to track carbon at a highly granular level using estimated or averaged baseline data destroys the integrity of the tracking application.
- **Action**:
  - Before expanding data models or Pydantic schemas to track granular habits, verify the source of truth (`data/emissions_factors.csv`, etc.).
  - If the dataset only contains generic `bus_km` (0.06 kg/km), do NOT split the UI/schema into `cng_bus` and `electric_bus` until verified metrics are obtained.
  - Grouping variables is acceptable if their baseline variance is minimal (< 10-20%). If variance is high but verified data is absent, flag it as a data dependency blocker rather than hallucinating an average.


---
### Source: `22-20-MASTER-correctness-and-data.md`
---

# Quarantine & Dead-Letter Queue (DLQ)

This rule establishes the standard operating procedure for handling malformed data and Pydantic validation failures.

## Directives

1. **Never Crash the Loop:** When an ingestion pipeline encounters data that fails Pydantic schema validation, it MUST NOT crash the main application process or event loop.
2. **Isolate Failures:** Malformed data must be safely caught and isolated to prevent upstream and downstream corruption.
3. **Route to DLQ:** All validation failures must be routed to the Dead-Letter Queue (DLQ). The required location for this is `data/quarantine_log.parquet`.
4. **Observability:** Ensure that the original payload, the validation error message, and a timestamp are logged alongside the quarantined record so that agents can autonomously diagnose and retry the processing later.


---
### Source: `27-20-MASTER-correctness-and-data.md`
---

---
description: Unified standard operating procedure defining the "Inner Loop" and "Outer Loop" rhythm that all AI agents must follow.
trigger: always_on
priority: tier_2_correctness
---
