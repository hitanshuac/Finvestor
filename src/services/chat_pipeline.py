"""
Orchestrates the chat pipeline, abstracting business logic away from the API router.
"""
from typing import Any

from fastapi import HTTPException

from api.schemas import ChatRequest, ChatResponse
from src.avatar_ai import get_llm_response
from src.data_engine import build_customer_360
from src.pii_redactor import redact_pii


def process_chat_request(request: ChatRequest, df: Any) -> ChatResponse:
    """Process a chat request with PII redaction and LLM advisory.

    Pipeline:
        1. Build Customer_360 profile from data engine.
        2. Redact PII from the latest user message.
        3. Call the LLM via LiteLLM (with automatic fallback).
        4. Return the response.
    """
    # Step 1: Build customer context
    c360 = build_customer_360(df, request.customer_id)
    if not c360:
        raise HTTPException(status_code=500, detail="Failed to build customer profile.")

    # Step 2: Redact PII from messages before sending to LLM
    sanitized_messages = []
    pii_found = False
    for msg in request.messages:
        if msg.role == "user":
            redacted_content, had_pii = redact_pii(msg.content)
            if had_pii:
                pii_found = True
            sanitized_messages.append({"role": msg.role, "content": redacted_content})
        else:
            sanitized_messages.append({"role": msg.role, "content": msg.content})

    # Step 3: Truncate to last 4 messages (guardrail)
    max_history = 4
    truncated = sanitized_messages[-max_history:] if len(sanitized_messages) > max_history else sanitized_messages

    # Step 4: Call LLM
    raw_response = get_llm_response(truncated, c360, request.language)

    return ChatResponse(raw_response=raw_response, pii_redacted=pii_found)
