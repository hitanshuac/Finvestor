"""
Finvestor — Digital Wealth Advisory Avatar
IDBI Bank Hackathon · Track 1 MVP

This module is the thin UI orchestrator for the Streamlit application.
It communicates with the FastAPI backend via HTTP for all data and AI logic.
It contains NO business logic, data generation, or API keys.

ROADMAP: Streamlit is strictly a visualization vessel for MVP.
Production UI will consume the FastAPI endpoints via IDBI's
React Native mobile app.
"""

import json
import logging
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from src.config import CUSTOMER_PROFILES, LANGUAGES
from src.utils import apply_styles

logger: logging.Logger = logging.getLogger(__name__)

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Backend API configuration
API_BASE_URL = "http://127.0.0.1:8000/v1"

# Configure requests session with robust retries for startup resilience
session = requests.Session()
retry_strategy = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504], allowed_methods=["GET", "POST"])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_customer_profile_http(customer_id: str) -> dict[str, Any]:
    resp = session.get(f"{API_BASE_URL}/customer/{customer_id}/profile", timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Authentication logic bypassed for OAuth integration ──────────────────


def render_sidebar(customer_id: str, customer_name: str) -> str:
    """Draw the sidebar with customer profile and language selector.

    Args:
        customer_id: The authenticated customer's ID.
        customer_name: The authenticated customer's display name.

    Returns:
        str: The selected language.
    """
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
    """Show the customer profile card in the sidebar.

    Args:
        c360: The aggregated Customer 360 profile.
        language: The language preference of the user.
        customer_name: The display name of the customer.
    """
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

        # Investable Surplus card
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

        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.caption("© 2026 IDBI Bank · Finvestor MVP")


# ── Narrative Greeting ───────────────────────────────────────────────


def _get_time_greeting() -> str:
    """Return a time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def render_greeting(c360: dict[str, Any], customer_name: str) -> None:
    """Render the personalized narrative greeting instead of cold metrics.

    Args:
        c360: The Customer 360 profile.
        customer_name: Display name of the customer.
    """
    greeting = _get_time_greeting()
    first_name = customer_name.split()[0]
    balance = c360.get("current_balance", 0.0)
    savings_pct = c360.get("savings_rate_pct", 0.0)
    surplus = c360.get("investable_surplus", 0.0)

    # Build narrative insight based on the customer's actual data
    if savings_pct >= 20:
        insight = (
            f'Your balance is healthy at <span class="greeting-highlight">₹{balance:,.0f}</span>. '
            f"You're saving {savings_pct:.0f}% of your income — excellent discipline. "
            f'You have <span class="greeting-highlight">₹{surplus:,.0f}/month</span> available to invest.'
        )
    elif savings_pct >= 10:
        insight = (
            f'Your balance stands at <span class="greeting-highlight">₹{balance:,.0f}</span>. '
            f"You're saving {savings_pct:.0f}% of your income — there's room to grow. "
            f"Let's explore how to put your surplus to work."
        )
    else:
        insight = (
            f'Your balance is at <span class="greeting-highlight">₹{balance:,.0f}</span>. '
            f"Your spending is running high — let's identify areas to optimise "
            f"and build a savings habit together."
        )

    st.markdown(
        f"""
        <div class="greeting-card">
            <p class="greeting-hello">{greeting},</p>
            <p class="greeting-name">{first_name} 👋</p>
            <p class="greeting-insight">{insight}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Spending Alerts ──────────────────────────────────────────────────


def render_spending_alerts(c360: dict[str, Any]) -> None:
    """Render proactive spending alerts for anomalous categories.

    Args:
        c360: The Customer 360 profile with spending_alerts.
    """
    alerts = c360.get("spending_alerts", [])
    for alert in alerts:
        cat = alert.get("category", "Unknown")
        current = alert.get("current", 0)
        average = alert.get("average", 0)
        pct_increase = ((current - average) / average * 100) if average > 0 else 0

        st.markdown(
            f"""
            <div class="spending-alert">
                <p class="alert-title">⚠️ Spending Alert: {cat}</p>
                <p class="alert-body">
                    Your spending on <strong>{cat}</strong> this month is
                    <strong>₹{current:,.0f}</strong> — that's {pct_increase:.0f}% above your
                    3-month average of ₹{average:,.0f}. Aria can help you optimise.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Dashboard ────────────────────────────────────────────────────────


def render_dashboard(c360: dict[str, Any]) -> None:
    """Render the Customer_360 KPI metrics and top categories.

    Args:
        c360: The aggregated Customer 360 profile.
    """
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Customer Age", f"{c360.get('age', 0)} yrs")
    k2.metric(
        "Current Balance",
        f"₹{c360.get('current_balance', 0.0):,.0f}",
    )
    k3.metric(
        "90-Day Inflow",
        f"₹{c360.get('total_inflow_90d', 0.0):,.0f}",
    )
    k4.metric(
        "90-Day Outflow",
        f"₹{c360.get('total_outflow_90d', 0.0):,.0f}",
    )

    st.markdown("")

    # Savings Rate Progress Bar
    savings_pct = c360.get("savings_rate_pct", 0.0)
    savings_ratio = max(0.0, min(1.0, savings_pct / 100.0))
    st.markdown(f"**Savings Rate (90 Days): {savings_pct:.1f}%**")
    st.progress(savings_ratio)

    st.markdown("<br>", unsafe_allow_html=True)

    # Advanced Data Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("90-Day Expense Distribution")
        expense_data: list[dict[str, Any]] = c360.get("expense_breakdown", [])
        if expense_data:
            df_expenses: pd.DataFrame = pd.DataFrame(expense_data)
            fig1 = px.pie(
                df_expenses,
                values="amount",
                names="category",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Greens_r,
            )
            fig1.update_layout(
                margin={"t": 20, "b": 20, "l": 20, "r": 20},
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No expense data available.")

    with col2:
        st.subheader("6-Month Balance Trajectory")
        balance_data: list[dict[str, Any]] = c360.get("balance_history", [])
        if balance_data:
            df_balance: pd.DataFrame = pd.DataFrame(balance_data)
            df_balance.set_index("date", inplace=True)
            df_balance["balance"] = pd.to_numeric(df_balance["balance"])
            st.area_chart(df_balance["balance"], color="#43a047")
        else:
            st.info("No balance history available.")

    st.markdown("---")


# ── Chat Interface ───────────────────────────────────────────────────


def _get_llm_response_http(messages: list[dict[str, str]], customer_id: str, language: str) -> str:
    """Call the FastAPI backend."""
    payload = {"customer_id": customer_id, "language": language, "messages": messages}
    resp = session.post(f"{API_BASE_URL}/chat", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json().get("raw_response", "")


def _render_widget(data: dict) -> None:
    """Check for and render a Generative UI widget if requested by the LLM.

    Args:
        data: The JSON payload from the LLM containing optional widget keys.
    """
    widget_type = data.get("widget_type")
    widget_data = data.get("widget_data")
    if not widget_type or not widget_data:
        return

    from src.widgets import WIDGET_REGISTRY

    render_fn = WIDGET_REGISTRY.get(widget_type)
    if render_fn:
        try:
            fig = render_fn(widget_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except (KeyError, TypeError, ValueError) as exc:
            logger.error("Widget rendering failed for type=%s: %s", widget_type, exc)
            st.error(f"Failed to render chart: {exc}")


def _build_dashboard_context(c360: dict[str, Any]) -> str:
    """Build a brief context string about what the user sees on the dashboard.

    This enables Aria to reference visible data when answering questions,
    creating a contextually-aware embedded AI experience.

    Args:
        c360: The Customer 360 profile.

    Returns:
        str: A brief context paragraph for injection into the chat.
    """
    top_cats = c360.get("top_3_categories", [])
    alerts = c360.get("spending_alerts", [])
    surplus = c360.get("investable_surplus", 0.0)

    context_parts = [
        "[DASHBOARD CONTEXT — The user can currently see these on their screen:]",
        f"- Balance: ₹{c360.get('current_balance', 0):,.0f}",
        f"- 90-day inflow: ₹{c360.get('total_inflow_90d', 0):,.0f}, outflow: ₹{c360.get('total_outflow_90d', 0):,.0f}",
        f"- Savings rate: {c360.get('savings_rate_pct', 0):.1f}%",
        f"- Monthly investable surplus: ₹{surplus:,.0f}",
    ]

    if top_cats:
        cats_str = ", ".join(f"{c['category']} (₹{c['amount']:,.0f})" for c in top_cats)
        context_parts.append(f"- Top spending: {cats_str}")

    if alerts:
        alert_str = ", ".join(f"{a['category']} (₹{a['current']:,.0f} vs avg ₹{a['average']:,.0f})" for a in alerts)
        context_parts.append(f"- ⚠️ Spending alerts visible: {alert_str}")

    context_parts.append("Reference this data naturally when relevant. Do not repeat it verbatim.")

    return "\n".join(context_parts)


def render_chat(c360: dict[str, Any], language: str, customer_id: str) -> None:
    """Render the conversational AI chat interface.

    Args:
        c360: The aggregated Customer 360 profile.
        language: The language preference of the user.
        customer_id: The active customer ID to scope history.
    """
    st.subheader("💬 Chat with Aria")

    history_key = f"messages_{customer_id}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    messages: list[dict[str, str]] = st.session_state[history_key]

    user_input = None

    for i, msg in enumerate(messages):
        avatar = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg["role"] == "assistant":
                try:
                    data = json.loads(msg["content"])
                    conv_resp = data.get("conversational_response", "")
                    if conv_resp:
                        st.write(conv_resp)
                    else:
                        # Fallback if LLM generated JSON but missed the key
                        st.write(data.get("response", data))

                    # Check and render inline Generative UI widget
                    _render_widget(data)

                    follow_up = data.get("follow_up_question", "")
                    if follow_up:
                        st.markdown(f"**{follow_up}**")

                    tips = data.get("recommended_tips", [])
                    for j, tip in enumerate(tips):
                        if st.button(tip, key=f"tip_{i}_{j}"):
                            user_input = tip
                except json.JSONDecodeError:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])

    st.markdown("**Suggested Actions:**")
    col1, col2, col3 = st.columns(3)

    surplus = c360.get("investable_surplus", 0.0)

    if col1.button("📊 Analyze spending"):
        user_input = "What are my top expenses and how can I cut back to invest?"
    if col2.button("📈 What-If Simulator"):
        user_input = (
            f"I have ₹{surplus:,.0f} investable surplus per month. "
            "What if I invest 70% of it in a SIP? Show me a 10-year projection chart."
        )
    if col3.button("🤝 Connect with RM"):
        user_input = (
            "I am interested in complex market-linked insurance products. "
            "Please connect me to a Relationship Manager."
        )

    if prompt := st.chat_input("Ask Aria anything about your finances..."):
        user_input = prompt

    if user_input:
        # PII Redaction is now handled by the FastAPI backend

        # Inject dashboard context into the conversation so Aria knows what the user sees
        dashboard_context = _build_dashboard_context(c360)

        # Prepend context to the user's message (invisible to chat display)
        contextual_message = f"{dashboard_context}\n\nUser question: {user_input}"

        messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="user"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="assistant"):
            # Send the contextual message to the LLM but display the clean user message
            # Slide window to last 4 messages to prevent token limits
            sliced_messages = messages[-5:-1] if len(messages) > 4 else messages[:-1]
            context_messages = sliced_messages + [{"role": "user", "content": contextual_message}]

            raw_response = _get_llm_response_http(context_messages, customer_id, language)

            try:
                # JSONDecodeError fix for LLM Markdown
                cleaned_str = raw_response.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_str)
                conv_resp = data.get("conversational_response", "")
                if conv_resp:
                    st.write(conv_resp)
                else:
                    # Fallback if LLM generated JSON but missed the key
                    st.write(data.get("response", data))

                # Check and render inline Generative UI widget
                _render_widget(data)

                follow_up = data.get("follow_up_question", "")
                if follow_up:
                    st.markdown(f"**{follow_up}**")

                tips = data.get("recommended_tips", [])
                for j, tip in enumerate(tips):
                    st.button(tip, key=f"tip_{len(messages)}_{j}")

                messages.append({"role": "assistant", "content": json.dumps(data)})
            except json.JSONDecodeError:
                import re

                # Attempt to rescue the response via regex if the LLM breaks the JSON schema
                match = re.search(
                    r'"conversational_response"\s*:\s*"(.*?)"\s*(?:,\s*"follow_up_question"|$)',
                    raw_response,
                    re.IGNORECASE | re.DOTALL,
                )
                if match:
                    clean_text = match.group(1).replace("\\n", "\n").replace('\\"', '"')
                else:
                    clean_text = (
                        raw_response.replace("```json", "").replace("```", "").replace("{", "").replace("}", "").strip()
                    )
                st.write(clean_text)
                messages.append({"role": "assistant", "content": clean_text})


# ── Main Entry Point ─────────────────────────────────────────────────


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
