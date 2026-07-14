"""
Pure logic for building UI context strings for the LLM.
"""
from typing import Any


def build_dashboard_context(c360: dict[str, Any]) -> str:
    """Build a brief context string about what the user sees on the dashboard."""
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
