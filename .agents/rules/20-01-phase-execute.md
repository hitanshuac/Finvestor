# DuckDB SQL Standards

This rule strictly governs all DuckDB operations to guarantee idempotent data ingestion and prevent data duplication during pipeline failures or retries.

## 1. Idempotency is Mandatory
- **Never** use raw `INSERT INTO` statements without conflict resolution.
- All ingestion logic MUST be idempotent. A partial failure and subsequent retry must result in the exact same database state as a single successful run.

## 2. Conflict Resolution
- Use `INSERT OR REPLACE` when the primary keys are strictly defined and replacing the entire row is acceptable.
- For more complex logic, use Staging Tables:
  - Load incoming data into a temporary `staging_table`.
  - Use `INSERT ... ON CONFLICT (id) DO UPDATE SET ...` to merge the staging data into the production table.

## 3. Transactions
- Wrap batch operations in explicit `BEGIN TRANSACTION` and `COMMIT` blocks to ensure atomic writes.

## 4. No Duplicates
- Pipeline retries must never result in duplicate rows under any circumstances.


---
### Source: `23-20-MASTER-correctness-and-data.md`
---

# Strict Constraint: No Raw CSV LLM Scans

This rule applies to all ingestion, auditing, and scanning workflows within the Hybrid AI Router Vision pipeline.

## 1. The Core Constraint
- **Rule**: NEVER pass a raw `.csv` or raw `.xlsx` file directly into an LLM context window.
- **Why**: Raw CSVs contain massive amounts of noisy tokens (commas, empty strings, repetitive structural elements). Passing them directly to an LLM causes severe token inflation, hallucinations (where the LLM loses track of column indices), and immediate context window exhaustion, violating the Context Compaction rule.

## 2. Mandatory Abstraction Layers
- Before any LLM operation is performed on tabular or document data, the file **MUST** be processed locally using a structured parsing package.
- **For Tabular Data (CSV/XLSX)**: Use `markitdown` (via `MarkItDown().convert()`) or `pandas` to structure the grid. If an LLM needs to understand the table, pass it the clean Markdown output from `markitdown` or a highly truncated JSON sample of the headers—never the raw comma-separated text.
- **For Unstructured Documents (PDF/Images)**: Use `docling` (via `DocumentConverter`) or the established Vision Cascade to extract bounding boxes and structured JSON representation.

## 3. Implementation of the Shadow Copy / Silver Layer
When building "Shadow Copies" or extracting data to a Silver Layer, do not rely on an LLM to parse the entire grid. Instead:
1. Use `markitdown` or `docling` to extract the document content.
2. If schema mapping is needed, pass *only* the Markdown headers to the LLM to identify the column positions (Schema-on-Read).
3. Perform the actual data extraction, mathematical validations (e.g., `qty * rate`), and anomaly flagging deterministically in Python.


---
### Source: `24-20-MASTER-correctness-and-data.md`
---

# Financial Data Integrity

This rule defines strict standards for data extracted via MarkItDown or any other ingestion pipeline regarding financial figures.

## 1. Zero-Mutation Policy on Financial Data
- **Rule**: You MUST NEVER modify, forward-fill (ffill), back-fill, impute, or attempt to "correct" financial columns, specifically `RATE` and `AMOUNT`.
- **Why**: Financial data must perfectly reflect the raw invoice. Altering this data—even to fix an obvious formatting mistake made by a vendor—introduces untraceable accounting discrepancies and breaks data lineage.
- **Action**:
  - Extract the raw string/float values exactly as they appear in the markdown or tabular source.
  - If a vendor leaves a `RATE` blank but fills an `AMOUNT`, leave the `RATE` blank.
  - Do not calculate missing values (e.g. `QTY * RATE = AMOUNT`). The missing value must remain `null` or `NaN`.

## 2. No Synthetic Data Generation
- **Rule**: When providing snippets or previews of data extractions, agents MUST ONLY show the exact data present in the file. Synthetic data (hallucinations) to "fill out" a table preview is strictly forbidden.

## 3. Exception Handling
- If a value cannot be safely cast to its required schema type (e.g., parsing a string "N/A" as a float), the pipeline MUST raise a `SchemaError` and halt, rather than silently replacing it with `0` or `0.0` (as per `00-MASTER-safety-and-guardrails.md`).


---
### Source: `25-20-MASTER-correctness-and-data.md`
---

# Router Alignment: Ephemeral Context Grounding

This rule permanently enforces inline payload mutation for all outbound text-model requests in the Agentic Application cascade.

## 1. Mandatory System Prompt Injection
- Every outbound `messages` payload sent to any cascade tier **must** include a `role: system` message at **index 0**.
- The canonical system message is defined in `src/capabilities/compaction.py` as the `SYSTEM_PROMPT` constant.
- No cascade tier is exempt. If a provider cannot accept `role: system`, the grounding text must be prepended as a prefix to the first `role: user` message instead.

## 2. Ephemeral Injection Only
- The system message is injected **at request time** inside the `ground_messages()` function. It is never persisted to disk, database, or session state.
- The original inbound `messages` array from the client must not be mutated. The router must operate on a **deep copy**.

## 3. Content Governance
- The `SYSTEM_GROUNDING_PROMPT` must identify the system as the "Agentic Application" and instruct the downstream model to respond helpfully and concisely.
- Any modification to the prompt content requires a corresponding entry in `retrospective.md` and a version bump.

## 4. Observability
- Every grounding injection must emit an `INFO`-level log line containing `[CONTEXT GROUNDING]` for SRE traceability.
- The log must include the number of messages in the grounded payload.

## 5. Relationship to Context Compaction
- After grounding is applied, the payload must pass through the **Context Compaction** layer defined in [`40-MASTER-style-and-quality.md`](./40-MASTER-style-and-quality.md).
- Execution order: **Grounding (this rule)** → **Compaction** → **Admission Control** → **Cascade**.
- The system message injected by this rule is immune to compaction eviction (see `40-MASTER-style-and-quality.md` §3).


---
### Source: `26-quarantine-dlq.md`
---

# Context Compaction: v2.4.0 Specification

This rule enforces strict token conservation on all conversation payloads transiting the Agentic Application cascade. It eliminates wasteful verbosity, caps history depth, and mandates telemetry persistence.

## 1. Processing Pipeline (Mandatory Order)
All operations execute on a **deep copy** of the inbound messages array. The caller's data must never be mutated.

The 5-step sequence within `src/capabilities/compaction.py` is:
1. **Deep Copy** — `copy.deepcopy(messages)` at function entry.
2. **Grounding** — System prompt injected at index 0 (`ground_messages()`). See `20-MASTER-correctness-and-data.md` §1.
3. **Prefix Stripping** — Verbose AI filler removed from `role: assistant` messages (`strip_boilerplate()`).
4. **Sliding Window** — Oldest messages beyond the cap are evicted (`apply_sliding_window()`).
5. **Cascade** — Compacted payload forwarded to `query_cloud()`. Admission Control (PRE-FLIGHT BYPASS) runs inside `llm_cloud.py`.

## 2. Prefix Stripping Rules
- Strip verbose AI conversational filler from `role: assistant` messages **only**.
- The following prefix patterns must be removed if they appear at the start of an assistant message:
  - `"Sure! "`, `"Sure, "`, `"Of course! "`, `"Of course, "`
  - `"Great question! "`, `"That's a great question! "`
  - `"Absolutely! "`, `"Certainly! "`
  - `"I'd be happy to help! "`, `"I'd be happy to help you with that! "`
  - `"Let me help you with that. "`
- Stripping is **prefix-only** and **case-sensitive**. The substantive content after the filler must be preserved verbatim.
- If stripping a prefix would result in an empty string, the original message must be kept intact.
- Multiple matching prefixes on the same message: strip only the **first** (longest) match.

## 3. Sliding Window Limit
- Hard cap: **10 messages** in any outbound payload (including the `role: system` message).
- The `role: system` message at index 0 is **pinned** and never evicted.
- When the payload exceeds 10 messages, retain only the system message + the **most recent 9** conversation messages. All older messages are dropped.

## 4. System Message Immunity
- The `role: system` message injected by `20-MASTER-correctness-and-data.md` is **exempt** from both sliding window eviction and boilerplate stripping.
- It must always occupy index 0 of the outbound payload.

## 5. Observability
- Every compaction event must emit an `INFO`-level log line containing `[CONTEXT COMPACTION]`.
- The log must include:
  - The **before** and **after** message counts (e.g., `"Compacted 24 → 10 messages"`).
  - The number of boilerplate prefixes stripped (e.g., `"Stripped 3 filler prefixes"`).
- If no compaction was necessary (payload already within limits and no boilerplate found), no log line is emitted.

## 6. Telemetry Persistence
- Every request must record compaction metrics to `data/pipeline_metrics.db` (DuckDB).
- Required fields: `raw_tokens`, `compact_tokens`, `tokens_saved`, `savings_pct`, `messages_dropped`, `prefixes_stripped`, `latency_sec`, `tier`.
- The DuckDB connection must follow the DuckDB Optimizer skill directives: WAL mode enabled, memory capped at 256MB.
- Telemetry writes must be non-blocking to the request path — a failed write must not crash the cascade.

---
### Source: `43-40-MASTER-style-and-quality.md`
---
