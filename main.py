"""
Finvestor — Digital Wealth Advisory Avatar
IDBI Bank Hackathon · Track 1 MVP

This module is the thin UI orchestrator for the Streamlit application.
It communicates with the FastAPI backend via HTTP for all data and AI logic.
It contains NO business logic, data generation, or API keys.
"""

import streamlit as st

from src.services.backend_client import get_customer_profile_http
from src.ui.chat import render_chat
from src.ui.dashboard import render_dashboard, render_greeting, render_spending_alerts
from src.ui.sidebar import render_sidebar, render_sidebar_profile
from src.utils import apply_styles


def main() -> None:
    """Application entry point for the Streamlit UI."""
    st.set_page_config(
        page_title="Finvestor | IDBI Digital Wealth Advisor",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_styles()

    # ── Authentication Gate (Bypassed for Bank OAuth) ──
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = True
        st.session_state["customer_id"] = "101"
        st.session_state["customer_name"] = "Rahul Sharma"

    # ── Authenticated Flow ───────────────────────────────────────────
    customer_id = st.session_state["customer_id"]
    customer_name = st.session_state["customer_name"]

    language = render_sidebar(customer_id, customer_name)
    try:
        c360 = get_customer_profile_http(customer_id)
    except Exception as e:
        st.error(f"Failed to connect to API backend. Ensure FastAPI is running on port 8000: {e}")
        return

    render_sidebar_profile(c360, language, customer_name)

    # Narrative greeting (replaces cold "Welcome to Finvestor" banner)
    render_greeting(c360, customer_name)

    # Proactive spending alerts
    render_spending_alerts(c360)

    # KPI dashboard
    render_dashboard(c360)

    # Contextual AI chat
    render_chat(c360, language, customer_id)

if __name__ == "__main__":
    main()
