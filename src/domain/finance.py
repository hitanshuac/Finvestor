"""
Pure financial domain logic functions.
No side effects, no database connections, no UI dependencies.
"""

def calculate_risk_profile(age: int, credit_score: int, savings_rate: float) -> str:
    """Calculate a deterministic risk profile based on financial metrics."""
    score = 0

    if age < 35:
        score += 4
    elif age <= 50:
        score += 2

    if credit_score >= 750:
        score += 3
    elif credit_score >= 650:
        score += 1
    else:
        score -= 2

    if savings_rate >= 20.0:
        score += 3
    elif savings_rate >= 10.0:
        score += 1

    if score >= 8:
        return "Aggressive"
    elif score >= 5:
        return "Moderate"
    else:
        return "Conservative"

def compute_investable_surplus(total_inflow: float, total_outflow: float, months: int = 3) -> float:
    """Compute monthly investable surplus from actual transaction data."""
    if months <= 0:
        return 0.0
    monthly_net = (total_inflow - total_outflow) / months
    return max(0.0, round(monthly_net, 2))

def project_compound_growth(monthly_sip: float, annual_rate: float, years: int) -> list[float]:
    """Calculate year-by-year SIP compound growth projections."""
    if monthly_sip <= 0 or annual_rate <= 0 or years <= 0:
        return []

    monthly_rate = annual_rate / 100 / 12
    projections: list[float] = []

    for year in range(1, years + 1):
        n = year * 12
        fv = monthly_sip * (((1 + monthly_rate) ** n - 1) / monthly_rate) * (1 + monthly_rate)
        projections.append(round(fv, 2))

    return projections
