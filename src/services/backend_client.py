"""
External HTTP client service for communicating with the FastAPI backend.
Encapsulates all network side-effects away from the UI.
"""
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_BASE_URL = "http://127.0.0.1:8000/v1"

# Configure requests session with robust retries for startup resilience
session = requests.Session()
retry_strategy = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504], allowed_methods=["GET", "POST"])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

def get_customer_profile_http(customer_id: str) -> dict[str, Any]:
    """Fetch the Customer 360 profile from the backend."""
    resp = session.get(f"{API_BASE_URL}/customer/{customer_id}/profile", timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_llm_response_http(messages: list[dict[str, str]], customer_id: str, language: str) -> str:
    """Call the FastAPI backend chat endpoint."""
    payload = {"customer_id": customer_id, "language": language, "messages": messages}
    resp = session.post(f"{API_BASE_URL}/chat", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json().get("raw_response", "")
