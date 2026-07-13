"""
Finvestor Enterprise API Server.

Headless FastAPI backend that wraps the AI advisory logic, PII redaction,
and data engine behind authenticated HTTP endpoints.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ChatRequest,
    ChatResponse,
    CustomerProfileResponse,
    HealthResponse,
)
from src.avatar_ai import get_llm_response
from src.config import CUSTOMER_PROFILES, LLM_MODEL
from src.data_engine import build_customer_360, load_transactions
from src.pii_redactor import redact_pii

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Finvestor Enterprise API",
    description="AI-powered Digital Wealth Advisory — Enterprise Backend",
    version="2.0.0",
)

# CORS — allow Streamlit frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-load transaction data at startup
_df = load_transactions()


@app.get("/v1/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint for monitoring and CI/CD readiness probes."""
    has_langfuse = bool(os.environ.get("LANGFUSE_PUBLIC_KEY"))

    return HealthResponse(
        status="ok",
        model=LLM_MODEL,
        fallback_model=getattr(__import__("src.config", fromlist=["FALLBACK_MODEL"]), "FALLBACK_MODEL", "none"),
        pii_redaction=True,
        observability=has_langfuse,
    )


@app.get("/v1/customer/{customer_id}/profile", response_model=CustomerProfileResponse)
def get_customer_profile(customer_id: str) -> CustomerProfileResponse:
    """Return the Customer_360 profile for a given customer ID.

    Args:
        customer_id: The customer identifier (e.g., "101", "102").

    Returns:
        CustomerProfileResponse: Aggregated financial metrics.
    """
    allowed_ids = set(CUSTOMER_PROFILES.keys())
    if customer_id not in allowed_ids:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")

    c360 = build_customer_360(_df, customer_id)
    if not c360:
        raise HTTPException(status_code=500, detail="Failed to build customer profile.")

    return CustomerProfileResponse(**c360)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat request with PII redaction and LLM advisory.

    Pipeline:
        1. Build Customer_360 profile from data engine.
        2. Redact PII from the latest user message.
        3. Call the LLM via LiteLLM (with automatic fallback).
        4. Return the response.

    Args:
        request: Validated ChatRequest with customer_id, language, and messages.

    Returns:
        ChatResponse: The AI advisory response.
    """
    # Step 1: Build customer context
    c360 = build_customer_360(_df, request.customer_id)
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
