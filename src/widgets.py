"""
Generative UI Widget Registry.

Contains 5 hardcoded, compliance-approved chart components that the LLM
can trigger via structured JSON outputs. The LLM never writes charting code —
it only returns a widget_type enum and a widget_data dict. This module
renders the appropriate Plotly figure.

Usage:
    from src.widgets import WIDGET_REGISTRY

    render_fn = WIDGET_REGISTRY.get(widget_type)
    if render_fn:
        fig = render_fn(widget_data)
        st.plotly_chart(fig, use_container_width=True)
"""

from collections.abc import Callable
from typing import Any

import plotly.graph_objects as go

# ── Color Palette (IDBI Brand) ─────────────────────────────────────
_BRAND_GREEN = "#43a047"
_BRAND_DARK = "#1a2332"
_BRAND_LIGHT = "#e8f5e9"
_PALETTE = [
    "#43a047",
    "#66bb6a",
    "#81c784",
    "#a5d6a7",
    "#c8e6c9",
    "#2e7d32",
    "#388e3c",
    "#4caf50",
    "#1b5e20",
    "#00c853",
]

_LAYOUT_DEFAULTS = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, system-ui, sans-serif", "color": "#e0e0e0"},
    "margin": {"t": 40, "b": 40, "l": 40, "r": 40},
    "height": 350,
}


def render_expense_breakdown(data: dict[str, Any]) -> go.Figure | None:
    """Render a donut chart of expense categories.

    Expected data:
        {"categories": ["Food", "Rent", ...], "amounts": [5000, 15000, ...]}
    """
    categories = data.get("categories", [])
    amounts = data.get("amounts", [])
    if not categories or not amounts or len(categories) != len(amounts):
        return None

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=amounts,
                hole=0.45,
                marker={"colors": _PALETTE[: len(categories)]},
                textinfo="label+percent",
                textposition="outside",
                textfont={"size": 11},
            )
        ]
    )
    fig.update_layout(
        **_LAYOUT_DEFAULTS,
        title={"text": "Expense Breakdown", "font": {"size": 16}},
        showlegend=False,
    )
    return fig


def render_projection_chart(data: dict[str, Any]) -> go.Figure | None:
    """Render a line chart showing investment growth projection.

    Expected data:
        {
            "years": 10,
            "monthly_investment": 5000,
            "expected_rate": 12.0,
            "projected_values": [60000, 127200, ...]
        }
    """
    years = int(data.get("years", 0))
    monthly_raw = str(data.get("monthly_investment", 0)).replace(",", "").replace("₹", "").replace("$", "")
    monthly = float(monthly_raw) if monthly_raw else 0
    rate = float(data.get("expected_rate", 0))

    raw_projected = data.get("projected_values", [])
    projected = []
    for v in raw_projected:
        clean_v = str(v).replace(",", "").replace("₹", "").replace("$", "")
        try:
            projected.append(float(clean_v))
        except ValueError:
            projected.append(0.0)

    if not projected or years <= 0:
        return None

    year_labels = list(range(1, len(projected) + 1))
    invested = [monthly * 12 * y for y in year_labels]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=year_labels,
            y=projected,
            mode="lines+markers",
            name="Projected Value",
            line={"color": _BRAND_GREEN, "width": 3},
            marker={"size": 6},
            fill="tozeroy",
            fillcolor="rgba(67, 160, 71, 0.15)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=year_labels,
            y=invested,
            mode="lines",
            name="Total Invested",
            line={"color": "#78909c", "width": 2, "dash": "dash"},
        )
    )
    fig.update_layout(
        **_LAYOUT_DEFAULTS,
        title={
            "text": f"SIP Projection — ₹{monthly:,.0f}/mo @ {rate}% for {years} yrs",
            "font": {"size": 14},
        },
        xaxis={"title": "Year", "dtick": 1, "gridcolor": "rgba(255,255,255,0.08)"},
        yaxis={"title": "Value (₹)", "gridcolor": "rgba(255,255,255,0.08)"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    )
    return fig


def render_savings_gauge(data: dict[str, Any]) -> go.Figure | None:
    """Render a gauge chart showing savings rate vs target.

    Expected data:
        {"current_rate": 22.5, "target_rate": 30.0}
    """
    current = data.get("current_rate", 0)
    target = data.get("target_rate", 30)

    if current is None:
        return None

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=current,
            delta={"reference": target, "valueformat": ".1f", "suffix": "%"},
            number={"suffix": "%", "font": {"size": 36}},
            title={"text": f"Savings Rate (Target: {target}%)", "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 50], "ticksuffix": "%"},
                "bar": {"color": _BRAND_GREEN},
                "bgcolor": "rgba(255,255,255,0.05)",
                "steps": [
                    {"range": [0, 10], "color": "rgba(244,67,54,0.3)"},
                    {"range": [10, 20], "color": "rgba(255,152,0,0.3)"},
                    {"range": [20, 35], "color": "rgba(76,175,80,0.3)"},
                    {"range": [35, 50], "color": "rgba(33,150,243,0.3)"},
                ],
                "threshold": {"line": {"color": "#ffffff", "width": 2}, "thickness": 0.75, "value": target},
            },
        )
    )
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


def render_balance_trend(data: dict[str, Any]) -> go.Figure | None:
    """Render an area chart showing account balance over time.

    Expected data:
        {"dates": ["2026-01-01", "2026-02-01", ...], "balances": [50000, 52000, ...]}
    """
    dates = data.get("dates", [])
    balances = data.get("balances", [])
    if not dates or not balances or len(dates) != len(balances):
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=balances,
            mode="lines",
            name="Balance",
            line={"color": _BRAND_GREEN, "width": 2},
            fill="tozeroy",
            fillcolor="rgba(67, 160, 71, 0.15)",
        )
    )
    fig.update_layout(
        **_LAYOUT_DEFAULTS,
        title={"text": "Account Balance Trend", "font": {"size": 14}},
        xaxis={"title": "Date", "gridcolor": "rgba(255,255,255,0.08)"},
        yaxis={"title": "Balance (₹)", "gridcolor": "rgba(255,255,255,0.08)"},
        showlegend=False,
    )
    return fig


def render_category_comparison(data: dict[str, Any]) -> go.Figure | None:
    """Render a horizontal bar chart comparing spending categories.

    Expected data:
        {"categories": ["Food", "Travel", "Shopping"], "amounts": [8000, 5000, 12000]}
    """
    categories = data.get("categories", [])
    amounts = data.get("amounts", [])
    if not categories or not amounts or len(categories) != len(amounts):
        return None

    # Sort by amount descending for visual clarity
    paired = sorted(zip(amounts, categories, strict=False), reverse=True)
    amounts_sorted = [p[0] for p in paired]
    categories_sorted = [p[1] for p in paired]

    colors = _PALETTE[: len(categories_sorted)]

    fig = go.Figure(
        go.Bar(
            x=amounts_sorted,
            y=categories_sorted,
            orientation="h",
            marker={"color": colors},
            text=[f"₹{a:,.0f}" for a in amounts_sorted],
            textposition="outside",
        )
    )
    fig.update_layout(
        **_LAYOUT_DEFAULTS,
        title={"text": "Spending by Category", "font": {"size": 14}},
        xaxis={"title": "Amount (₹)", "gridcolor": "rgba(255,255,255,0.08)"},
        yaxis={"autorange": "reversed"},
    )
    return fig


# ── Widget Registry ────────────────────────────────────────────────
# The LLM can ONLY trigger widgets in this registry. No dynamic dispatch.
WIDGET_REGISTRY: dict[str, Callable[[dict[str, Any]], go.Figure | None]] = {
    "expense_breakdown": render_expense_breakdown,
    "projection_chart": render_projection_chart,
    "savings_gauge": render_savings_gauge,
    "balance_trend": render_balance_trend,
    "category_comparison": render_category_comparison,
}

# Allowed widget types as a set for prompt injection
ALLOWED_WIDGET_TYPES: set[str] = set(WIDGET_REGISTRY.keys())
