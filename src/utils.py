"""
Utility functions and custom styling for the Finvestor MVP.
"""

import streamlit as st


def get_custom_css() -> str:
    """Return the premium dark theme CSS for the application.

    Returns:
        str: A string containing HTML/CSS style definitions.
    """
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body {
    font-family: 'Inter', sans-serif;
}

/* ── Container Compaction for Large Monitors ────── */
.block-container {
    max-width: 1200px !important;
    padding-top: 2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    margin: 0 auto !important;
}

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #001a12 0%, #00382a 50%, #004d3a 100%);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label {
    color: #c8e6c9 !important;
}

/* ── Metric Cards ────────────────────────────────── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d1f17 0%, #112b1f 100%);
    border: 1px solid rgba(0,86,63,0.35);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}
div[data-testid="stMetric"] label {
    color: #81c784 !important;
    font-weight: 500;
    letter-spacing: 0.03em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #e8f5e9 !important;
    font-weight: 700;
}

/* ── Chat Messages ───────────────────────────────── */
div[data-testid="stChatMessage"] {
    border-radius: 14px;
    border: 1px solid rgba(0,86,63,0.12);
    margin-bottom: 0.5rem;
}

/* ── Divider ─────────────────────────────────────── */
hr {
    border-color: rgba(0,86,63,0.2) !important;
}

/* ── Category Pills ──────────────────────────────── */
.category-pill {
    display: inline-block;
    background: linear-gradient(135deg, #00563f 0%, #007a57 100%);
    color: #e8f5e9;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    margin: 0.2rem;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}

/* ── Welcome Banner ──────────────────────────────── */
.welcome-banner {
    background: linear-gradient(135deg, #00563f 0%, #00805e 60%, #43a047 100%);
    border-radius: 16px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    color: #ffffff;
    box-shadow: 0 6px 24px rgba(0,86,63,0.25);
}
.welcome-banner h2 {
    margin: 0 0 0.3rem 0;
    font-weight: 700;
    font-size: 1.5rem;
}
.welcome-banner p {
    margin: 0;
    opacity: 0.9;
    font-size: 0.95rem;
}

/* ── Narrative Greeting ──────────────────────────── */
.greeting-card {
    background: linear-gradient(135deg, #00563f 0%, #00805e 60%, #43a047 100%);
    border-radius: 18px;
    padding: 2rem 2.4rem;
    margin-bottom: 1.5rem;
    color: #ffffff;
    box-shadow: 0 8px 32px rgba(0,86,63,0.3);
    position: relative;
    overflow: hidden;
}
.greeting-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.greeting-card .greeting-hello {
    font-size: 1.1rem;
    font-weight: 400;
    opacity: 0.85;
    margin: 0 0 0.2rem 0;
}
.greeting-card .greeting-name {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0 0 0.8rem 0;
    letter-spacing: -0.02em;
}
.greeting-card .greeting-insight {
    font-size: 1rem;
    line-height: 1.5;
    opacity: 0.92;
    margin: 0;
}
.greeting-card .greeting-highlight {
    color: #ffd54f;
    font-weight: 600;
}

/* ── Spending Alert ──────────────────────────────── */
.spending-alert {
    background: linear-gradient(135deg, rgba(255,152,0,0.12) 0%, rgba(255,87,34,0.08) 100%);
    border: 1px solid rgba(255,152,0,0.3);
    border-left: 4px solid #ff9800;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
    color: #ffe0b2;
}
.spending-alert .alert-title {
    font-weight: 600;
    font-size: 0.9rem;
    color: #ffb74d;
    margin: 0 0 0.3rem 0;
}
.spending-alert .alert-body {
    font-size: 0.88rem;
    margin: 0;
    line-height: 1.4;
}

/* ── Logo Card ───────────────────────────────────── */
.logo-card {
    background: linear-gradient(135deg, #00563f 0%, #008060 100%);
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.08);
}
.logo-card .bank-name {
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.12em;
    margin: 0;
}
.logo-card .bank-sub {
    font-size: 0.7rem;
    color: #c8e6c9;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin: 0;
}
.logo-card .app-name {
    font-size: 1rem;
    font-weight: 600;
    color: #ffd54f;
    margin: 0.6rem 0 0 0;
    letter-spacing: 0.05em;
}

/* ── Profile Card ────────────────────────────────── */
.profile-card {
    background: rgba(0,86,63,0.15);
    border: 1px solid rgba(0,86,63,0.25);
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
}
.profile-card h4 {
    color: #81c784 !important;
    margin: 0 0 0.5rem 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.profile-card p {
    margin: 0.2rem 0;
    font-size: 0.88rem;
}

/* ── Login Screen ────────────────────────────────── */
.login-container {
    max-width: 420px;
    margin: 3rem auto;
    padding: 2.5rem;
    background: linear-gradient(145deg, #0d1f17 0%, #112b1f 100%);
    border-radius: 20px;
    border: 1px solid rgba(0,86,63,0.3);
    box-shadow: 0 12px 48px rgba(0,0,0,0.4);
}
.login-header {
    text-align: center;
    margin-bottom: 2rem;
}
.login-header .bank-logo {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.15em;
    margin: 0;
}
.login-header .bank-tagline {
    font-size: 0.7rem;
    color: #81c784;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 0.2rem 0 1rem 0;
}
.login-header .app-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #ffd54f;
    margin: 0;
}
.login-header .app-subtitle {
    font-size: 0.85rem;
    color: #a5d6a7;
    margin: 0.3rem 0 0 0;
}
.login-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.75rem;
    color: rgba(200, 230, 201, 0.5);
}

/* ── Investable Surplus Card ─────────────────────── */
.surplus-card {
    background: linear-gradient(135deg, #1a2332 0%, #0d2818 100%);
    border: 1px solid rgba(67,160,71,0.25);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin: 0.5rem 0 1rem 0;
    text-align: center;
}
.surplus-card .surplus-label {
    font-size: 0.8rem;
    color: #81c784;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 0.3rem 0;
}
.surplus-card .surplus-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #43a047;
    margin: 0;
}
.surplus-card .surplus-sub {
    font-size: 0.78rem;
    color: #a5d6a7;
    margin: 0.3rem 0 0 0;
}
</style>
"""


def apply_styles() -> None:
    """Inject the custom CSS into the Streamlit application."""
    # RULE OVERRIDE: 10-MASTER-security §4 (unsafe_allow_html)
    # Rationale: Streamlit does not support injecting global CSS variables
    # without raw HTML. This is required for the premium IDBI dark theme.
    # The payload is entirely hardcoded CSS, with zero user-supplied input.
    st.markdown(get_custom_css(), unsafe_allow_html=True)
