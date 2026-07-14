"""
Sidebar UI components.
"""
from typing import Any

import streamlit as st

from src.config import CUSTOMER_PROFILES, LANGUAGES


def render_sidebar(customer_id: str, customer_name: str) -> str:
    """Draw the sidebar with customer profile and language selector."""
    with st.sidebar:
        st.markdown(
            """
            <div class="logo-card">
                <p class="bank-name">IDBI</p>
                <p class="bank-sub">Industrial Development Bank of India</p>
                <p class="app-name">Finvestor</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        language = st.selectbox(
            "Language Preference",
            options=LANGUAGES,
            index=0,
        )

    return str(language)

def render_sidebar_profile(c360: dict[str, Any], language: str, customer_name: str) -> None:
    """Show the customer profile card in the sidebar."""
    age = c360.get("age", 0)
    risk_val = c360.get("risk_profile", "Moderate")
    risk = (
        "Aggressive (Growth)"
        if risk_val == "Aggressive"
        else ("Moderate (Balanced)" if risk_val == "Moderate" else "Conservative (Capital Safety)")
    )
    profile = CUSTOMER_PROFILES.get(c360.get("customer_id", ""), {})
    persona = profile.get("persona", "")

    with st.sidebar:
        st.markdown(
            f"""
            <div class="profile-card">
                <h4>Customer Profile</h4>
                <p><strong>{customer_name}</strong></p>
                <p><strong>Age:</strong> {age} · <strong>Risk:</strong> {risk}</p>
                <p><strong>Persona:</strong> {persona}</p>
                <p><strong>Language:</strong> {language}</p>
                <p><strong>Credit Score:</strong> {c360.get('credit_score', 'N/A')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        surplus = c360.get("investable_surplus", 0.0)
        st.markdown(
            f"""
            <div class="surplus-card">
                <p class="surplus-label">Monthly Investable Surplus</p>
                <p class="surplus-value">₹{surplus:,.0f}</p>
                <p class="surplus-sub">Based on your 90-day transaction history</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("")
        st.caption("© 2026 IDBI Bank · Finvestor MVP")
