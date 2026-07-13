---
description: A mandatory tripwire workflow that triggers upon API/Frontend failure to fetch remote logs via MCP and prevent agent hallucination.
---

# MCP Error Trigger & Log Retrieval Workflow

This workflow addresses a critical gap in agentic governance: preventing an LLM agent from hallucinating bug fixes by forcing it to fetch empirical evidence (logs) from production environments via the Model Context Protocol (MCP) before taking any action.

## Step 1: The Tripwire Rule
Whenever an agent observes an API failure, 500 Internal Server Error, or a frontend "Network Error / Unreachable" state, the agent MUST:
1. **Immediately halt** all code generation or speculative debugging.
2. Acknowledge the error explicitly: "Error detected. Halting generation to fetch production logs via MCP."
3. Proceed directly to Step 2.

## Step 2: MCP Log Retrieval
The agent MUST retrieve the actual error stack trace from the deployed environment.
1. Use the configured `Render MCP Server` (or similar infrastructure MCP) to fetch the most recent 100 lines of server logs.
2. If the logs are too large, pipe them through the `jCodeMunch` tool to extract only the relevant stack trace.

## Step 3: Anti-Hallucination Clause
Under no circumstances is the agent allowed to propose a fix based solely on the frontend symptom (e.g., "Method Not Allowed").
- **Strict Prohibition**: If the agent attempts to write a fix without first quoting the exact `Exception` from the backend logs, the fix is considered invalid and must be discarded.

## Step 4: Workflow Chaining
Once the logs have been retrieved and the root cause extracted:
1. The agent MUST autonomously trigger the `/error-observability` workflow.
2. The agent MUST format the extracted log according to the canonical schema required by `/error-observability` and append it to `data/error_logs.json`.
3. Only after the error is logged structurally may the agent proceed to formulate a remediation plan.

## Step 5: Circuit Breaker
If the MCP server is unresponsive, missing, or fails to fetch the logs:
1. The agent MUST NOT attempt to guess the bug.
2. The agent MUST output: `[CIRCUIT BREAKER ACTIVATED] MCP Log Retrieval Failed.`
3. The agent MUST halt and wait for human intervention to manually provide the logs or restore the MCP connection.
