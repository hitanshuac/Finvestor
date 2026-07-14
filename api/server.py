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
from src.config import CUSTOMER_PROFILES, LLM_MODEL
from src.data_engine import build_customer_360, load_transactions
from src.services.chat_pipeline import process_chat_request

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
    """Return the Customer_360 profile for a given customer ID."""
    allowed_ids = set(CUSTOMER_PROFILES.keys())
    if customer_id not in allowed_ids:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")

    c360 = build_customer_360(_df, customer_id)
    if not c360:
        raise HTTPException(status_code=500, detail="Failed to build customer profile.")

    return CustomerProfileResponse(**c360)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat request by delegating to the chat pipeline."""
    return process_chat_request(request, _df)
