"""
Pydantic models for the Finvestor API.
Strict input validation to prevent injection and malformed requests.
"""

from pydantic import BaseModel, Field, field_validator

from src.config import CUSTOMER_PROFILES, LANGUAGES

# Pre-compute allowed customer IDs from the config
_ALLOWED_CUSTOMER_IDS: set[str] = set(CUSTOMER_PROFILES.keys())
_ALLOWED_LANGUAGES: set[str] = set(LANGUAGES)


class ChatMessage(BaseModel):
    """A single chat message in the conversation history."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    """Incoming chat request from the Streamlit frontend."""

    customer_id: str
    language: str
    messages: list[ChatMessage]

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        if v not in _ALLOWED_CUSTOMER_IDS:
            raise ValueError(f"Invalid customer_id: {v}. Must be one of {_ALLOWED_CUSTOMER_IDS}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in _ALLOWED_LANGUAGES:
            raise ValueError(f"Invalid language: {v}. Must be one of {_ALLOWED_LANGUAGES}")
        return v


class ChatResponse(BaseModel):
    """Response from the AI advisory endpoint."""

    raw_response: str
    pii_redacted: bool = False


class CustomerProfileResponse(BaseModel):
    """Customer 360 profile returned by the data engine."""

    customer_id: str
    age: int = 0
    current_balance: float = 0.0
    total_inflow_90d: float = 0.0
    total_outflow_90d: float = 0.0
    emi_amount: float = 0.0
    credit_score: int = 0
    top_3_categories: list[dict] = []
    risk_profile: str = "Moderate"
    savings_rate_pct: float = 0.0
    expense_breakdown: list[dict] = []
    balance_history: list[dict] = []
    investable_surplus: float = 0.0
    spending_alerts: list[dict] = []
    recent_transactions: list[dict] = []


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    model: str = ""
    fallback_model: str = ""
    pii_redaction: bool = False
    observability: bool = False
