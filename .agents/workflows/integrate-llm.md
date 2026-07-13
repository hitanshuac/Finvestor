---
description: A mandatory workflow for integrating LLM providers to prevent decommissioned model hallucination.
---

# LLM Integration & Deployment Workflow

**Trigger:** Invoked when setting up a new LLM provider, migrating models, or configuring `LLM_MODEL` in configuration files.

## Objective
Prevent the AI from hallucinating decommissioned or deprecated model names (e.g., assuming `llama3-8b-8192` or `llama-3.1-70b-versatile` are still active based on outdated training data). This workflow forces a strict **Zero-Trust Discovery Protocol**.

## Execution Steps

### Phase 1: Live Discovery (No Guessing)
1. The agent MUST NOT hardcode or guess a model string based on its internal knowledge.
2. The agent MUST write and execute a temporary script or `curl` command to query the target provider's live `GET /v1/models` endpoint (e.g., `https://api.groq.com/openai/v1/models`).
3. If an API key is required for discovery, the agent must ensure it is loaded from the `.env` or `st.secrets` file before querying.

### Phase 2: Deterministic Selection
1. The agent MUST parse the JSON response from Phase 1.
2. Filter out deprecated models or models scheduled for decommissioning.
3. Select the exact string of the active, non-deprecated model that fits the user's requirements (e.g., selecting `llama-3.3-70b-versatile` instead of `llama-3.1-70b-versatile`).

### Phase 3: Live Verification Gate
1. The agent MUST write a temporary Python script to execute a real, unmocked ChatCompletion request against the provider using the exact model string selected in Phase 2.
2. **Mocking is strictly forbidden** for this validation step.
3. The script must assert a `200 OK` response from the provider.
4. The agent CANNOT proceed to integrate the model string into the core source code (`src/config.py`, etc.) until this live script successfully completes.

### Phase 4: Integration
1. Hardcode the validated model string into the configuration file.
2. Standardize on the official `openai` Python SDK for multi-provider compatibility (using `base_url` for Groq, Together, etc.).
3. Delete any temporary discovery or verification scripts created in Phases 1 and 3.

### Phase 5: Error Observability
1. If the live verification gate (Phase 3) fails with a 400 Bad Request or model decommissioned error during future updates, the agent MUST log the failure using the `.agents/workflows/error-observability.md` workflow to prevent future hallucination loops.
