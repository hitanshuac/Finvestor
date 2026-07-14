"""
Dashboard UI components.
"""
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


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
    """Render the personalized narrative greeting instead of cold metrics."""
    greeting = _get_time_greeting()
    first_name = customer_name.split()[0]
    balance = c360.get("current_balance", 0.0)
    savings_pct = c360.get("savings_rate_pct", 0.0)
    surplus = c360.get("investable_surplus", 0.0)

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

def render_spending_alerts(c360: dict[str, Any]) -> None:
    """Render proactive spending alerts for anomalous categories."""
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

def render_dashboard(c360: dict[str, Any]) -> None:
    """Render the Customer_360 KPI metrics and top categories."""
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Customer Age", f"{c360.get('age', 0)} yrs")
    k2.metric("Current Balance", f"₹{c360.get('current_balance', 0.0):,.0f}")
    k3.metric("90-Day Inflow", f"₹{c360.get('total_inflow_90d', 0.0):,.0f}")
    k4.metric("90-Day Outflow", f"₹{c360.get('total_outflow_90d', 0.0):,.0f}")

    st.markdown("")

    savings_pct = c360.get("savings_rate_pct", 0.0)
    savings_ratio = max(0.0, min(1.0, savings_pct / 100.0))
    st.markdown(f"**Savings Rate (90 Days): {savings_pct:.1f}%**")
    st.progress(savings_ratio)

    st.markdown("<br>", unsafe_allow_html=True)

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
            fig1.update_layout(margin={"t": 20, "b": 20, "l": 20, "r": 20})
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
