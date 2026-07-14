"""
Configuration variables and constants for the Finvestor MVP.
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()

# ── Mock Login Credentials ────────────────────────────────────────
# In production, this would be replaced by IDBI's OAuth2/OIDC provider.
# Credentials are now securely loaded from the environment to satisfy DPDP/SEBI rules.
_mock_creds_json = os.getenv("MOCK_CREDENTIALS")

if not _mock_creds_json:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: 'MOCK_CREDENTIALS' environment variable is missing. "
        "The application cannot start without secure configuration. "
        "Please inject the credentials JSON into your environment."
    )

try:
    CREDENTIALS: dict[str, dict[str, str]] = json.loads(_mock_creds_json)
except json.JSONDecodeError as e:
    raise RuntimeError(f"CRITICAL SECURITY ERROR: 'MOCK_CREDENTIALS' is not valid JSON. {e}")

# Customer profiles available in the MVP (used in sidebar profile card)
CUSTOMER_PROFILES: dict[str, dict[str, str]] = {
    "101": {"name": "Rahul Sharma", "persona": "Young Professional, High Spender"},
    "102": {"name": "Anil Deshmukh", "persona": "Pre-Retiree, High Saver"},
    "103": {"name": "Priya Kapoor", "persona": "Mid-Career, Balanced Investor"},
    "107": {"name": "Meera Iyer", "persona": "Young Professional, Growth-Oriented"},
    "105": {"name": "Suresh Patil", "persona": "Senior Manager, Family Planner"},
}

# Available languages for the AI Avatar
LANGUAGES: list[str] = ["English", "Hindi", "Marathi"]

# LLM model identifiers (LiteLLM provider-prefixed format)
LLM_MODEL: str = "groq/llama-3.3-70b-versatile"
FALLBACK_MODEL: str = "openrouter/meta-llama/llama-3.3-70b-instruct"

# Allowed widget types for Generative UI (frontend expects these exact strings)
ALLOWED_WIDGET_TYPES: set[str] = {
    "expense_breakdown",
    "projection_chart",
    "savings_gauge",
    "balance_trend",
    "category_comparison",
}

