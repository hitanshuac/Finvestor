# Chat Service Test Plan

This test plan defines the isolated unit testing strategy for the newly extracted `ChatService` domain logic, strictly adhering to `.agents/workflows/test-automation.md`.

## Test Environment
- **Framework:** Pytest
- **Type:** Unit Tests (Isolated)
- **Target File:** `src/tests/test_chat_service.py`

## Test Cases

### 1. test_process_chat_success
- **Test Type:** Unit
- **Setup:** Mock `build_customer_360`, `redact_pii`, and `get_llm_response`. Inject a mock `ChatRequest`.
- **Action:** Call `process_chat_request(request)`.
- **Assertion:** Verify `build_customer_360` is called with the correct ID. Verify `redact_pii` iterates over user messages. Verify `get_llm_response` is called with the truncated list of sanitized messages and returns a successful JSON string.

### 2. test_process_chat_missing_customer
- **Test Type:** Unit
- **Setup:** Mock `build_customer_360` to return `None` (simulating customer not found or engine failure).
- **Action:** Call `process_chat_request(request)`.
- **Assertion:** Ensure a `ValueError` is raised with the message "Failed to build customer profile."

### 3. test_process_chat_truncation_logic
- **Test Type:** Unit
- **Setup:** Mock `build_customer_360` and `get_llm_response`. Create a `ChatRequest` containing 10 messages.
- **Action:** Call `process_chat_request(request)`.
- **Assertion:** Verify `get_llm_response` is called with exactly 4 messages (the truncation boundary), proving that the history is correctly truncated to save LLM tokens.

### 4. test_process_chat_pii_redaction
- **Test Type:** Unit
- **Setup:** Mock `build_customer_360` and `get_llm_response`. Provide a `ChatRequest` where one user message contains PII.
- **Action:** Call `process_chat_request(request)`.
- **Assertion:** Ensure the PII redactor correctly sanitizes the input before passing it to `get_llm_response`.
