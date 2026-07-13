"""
Data processing engine for generating mock transactions and DuckDB analytics.

ROADMAP: Current batch CSV ingestion via DuckDB is built for MVP.
Production architecture will replace this with real-time Apache Kafka
streaming from IDBI Core Banking (Finacle/Flexcube).
"""

import logging
from typing import Any

import duckdb
import pandas as pd
import streamlit as st

logger: logging.Logger = logging.getLogger(__name__)


@st.cache_data
def load_transactions() -> pd.DataFrame:
    """Load transactions from CSV and prepare for DuckDB analytics.

    Returns:
        pd.DataFrame: A DataFrame with the transaction history.
    """
    try:
        df = pd.read_csv("data/bank_transactions.csv")
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        # Cast customer_id to string to match our Streamlit selectbox
        df["customer_id"] = df["customer_id"].astype(str)
        # Ensure we sort by date appropriately and add txn_order for window functions
        df.sort_values(["customer_id", "transaction_date"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["txn_order"] = range(len(df))
        return df
    except FileNotFoundError:
        logger.error("Transaction CSV file not found at data/bank_transactions.csv")
        return pd.DataFrame()
    except pd.errors.ParserError as e:
        logger.error("Failed to parse CSV data: %s", e)
        return pd.DataFrame()
    except ValueError as e:
        logger.error("Data type conversion error during CSV load: %s", e)
        return pd.DataFrame()


def calculate_risk_profile(age: int, credit_score: int, savings_rate: float) -> str:
    """Calculate a deterministic risk profile based on financial metrics.

    Args:
        age (int): Customer age.
        credit_score (int): Customer credit score.
        savings_rate (float): Calculated savings rate percentage.

    Returns:
        str: Risk profile category ("Aggressive", "Moderate", or "Conservative").
    """
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
    """Compute monthly investable surplus from actual transaction data.

    Investable surplus = (total inflow - total outflow) / months
    This gives the average monthly amount the customer could invest
    based on their real spending patterns.

    Args:
        total_inflow: Total credits over the period.
        total_outflow: Total debits over the period.
        months: Number of months in the data window (default 3 for 90-day).

    Returns:
        float: Monthly investable surplus (floored at 0).
    """
    if months <= 0:
        return 0.0
    monthly_net = (total_inflow - total_outflow) / months
    return max(0.0, round(monthly_net, 2))


def project_compound_growth(monthly_sip: float, annual_rate: float, years: int) -> list[float]:
    """Calculate year-by-year SIP compound growth projections.

    Uses the standard SIP future value formula:
    FV = P * (((1 + r)^n - 1) / r) * (1 + r)
    where P = monthly investment, r = monthly rate, n = total months.

    Args:
        monthly_sip: Monthly SIP amount in rupees.
        annual_rate: Expected annual return rate (e.g., 12.0 for 12%).
        years: Investment horizon in years.

    Returns:
        list[float]: Projected portfolio value at the end of each year.
    """
    if monthly_sip <= 0 or annual_rate <= 0 or years <= 0:
        return []

    monthly_rate = annual_rate / 100 / 12
    projections: list[float] = []

    for year in range(1, years + 1):
        n = year * 12
        fv = monthly_sip * (((1 + monthly_rate) ** n - 1) / monthly_rate) * (1 + monthly_rate)
        projections.append(round(fv, 2))

    return projections


def build_customer_360(df: pd.DataFrame, customer_id: str) -> dict[str, Any]:
    """Register `df` in an in-memory DuckDB and return a Customer_360 dict.

    Args:
        df (pd.DataFrame): The transaction history DataFrame.
        customer_id (str): The ID of the customer to aggregate.

    Returns:
        Dict[str, Any]: A dictionary containing summary metrics. Returns an
        empty dictionary gracefully if an error occurs.
    """
    try:
        con = duckdb.connect(":memory:")
        con.register("txn", df)

        # Summary metrics
        summary = con.execute(
            """
            SELECT
                MAX(age)                                                   AS age,
                (SELECT account_balance
                   FROM txn
                  WHERE customer_id = $1
                  ORDER BY transaction_date DESC, txn_order DESC
                  LIMIT 1)                                                 AS current_balance,
                SUM(CASE WHEN transaction_direction = 'CR' THEN transaction_amount ELSE 0 END) AS total_inflow,
                SUM(CASE WHEN transaction_direction = 'DR' THEN transaction_amount ELSE 0 END) AS total_outflow,
                MAX(emi_amount)                                            AS emi_amount,
                MAX(credit_score)                                          AS credit_score
            FROM txn
            WHERE customer_id = $1
            """,
            [customer_id],
        ).fetchone()

        # Top 3 spending categories
        top_cats = con.execute(
            """
            SELECT merchant_category, ROUND(SUM(transaction_amount), 2) AS total
            FROM txn
            WHERE customer_id = $1 AND transaction_direction = 'DR'
            GROUP BY merchant_category
            ORDER BY total DESC
            LIMIT 3
            """,
            [customer_id],
        ).fetchall()

        # All spending categories for Donut Chart
        expense_breakdown = con.execute(
            """
            SELECT merchant_category, ROUND(SUM(transaction_amount), 2) AS total
            FROM txn
            WHERE customer_id = $1 AND transaction_direction = 'DR'
            GROUP BY merchant_category
            ORDER BY total DESC
            """,
            [customer_id],
        ).fetchall()

        # Balance history for Area Chart
        balance_history = con.execute(
            """
            SELECT transaction_date, account_balance
            FROM txn
            WHERE customer_id = $1
            ORDER BY transaction_date ASC, txn_order ASC
            """,
            [customer_id],
        ).fetchall()

        # Spending anomalies — categories where current month spend exceeds 3-month average by >50%
        spending_alerts = con.execute(
            """
            WITH monthly AS (
                SELECT merchant_category,
                       EXTRACT(MONTH FROM CAST(transaction_date AS TIMESTAMP)) AS mth,
                       SUM(transaction_amount) AS monthly_total
                FROM txn
                WHERE customer_id = $1 AND transaction_direction = 'DR'
                GROUP BY merchant_category, EXTRACT(MONTH FROM CAST(transaction_date AS TIMESTAMP))
            ),
            avg_spend AS (
                SELECT merchant_category,
                       AVG(monthly_total) AS avg_monthly,
                       MAX(CASE WHEN mth = EXTRACT(MONTH FROM CURRENT_DATE) THEN monthly_total END) AS current_month
                FROM monthly
                GROUP BY merchant_category
            )
            SELECT merchant_category, ROUND(current_month, 0) AS current, ROUND(avg_monthly, 0) AS average
            FROM avg_spend
            WHERE current_month > avg_monthly * 1.5
              AND avg_monthly > 0
            ORDER BY (current_month - avg_monthly) DESC
            LIMIT 3
            """,
            [customer_id],
        ).fetchall()

        # Recent transactions for Dashboard drill-down
        recent_transactions_raw = con.execute(
            """
            SELECT
                transaction_date,
                merchant_category || ' - ' || transaction_direction AS transaction_description,
                merchant_category,
                transaction_direction,
                transaction_amount
            FROM txn
            WHERE customer_id = $1
            ORDER BY transaction_date DESC, txn_order DESC
            LIMIT 50
            """,
            [customer_id],
        ).fetchall()

        recent_txns = [
            {
                "id": f"TXN-{8900 - i}",  # Simulated ID format to match frontend expectation
                "date": str(row[0].date()) if hasattr(row[0], "date") else str(row[0])[:10],
                "description": str(row[1]),
                "category": str(row[2]),
                "type": "Credit" if row[3] == "CR" else "Debit",
                "amount": f"₹{row[4]:,.2f}",
            }
            for i, row in enumerate(recent_transactions_raw)
        ]

        con.close()

        age_val = summary[0] if summary else 0
        total_inflow_val = round(summary[2], 2) if summary and summary[2] else 0.0
        total_outflow_val = round(summary[3], 2) if summary and summary[3] else 0.0
        emi_val = summary[4] if summary and summary[4] else 0.0
        credit_score_val = summary[5] if summary else 0

        savings_rate_pct = 0.0
        if total_inflow_val > 0:
            savings_rate_pct = ((total_inflow_val - total_outflow_val) / total_inflow_val) * 100

        risk_profile = calculate_risk_profile(age_val, credit_score_val, savings_rate_pct)

        # Compute investable surplus from real data
        investable_surplus = compute_investable_surplus(total_inflow_val, total_outflow_val)

        return {
            "customer_id": customer_id,
            "age": age_val,
            "current_balance": round(summary[1], 2) if summary and summary[1] else 0.0,
            "total_inflow_90d": total_inflow_val,
            "total_outflow_90d": total_outflow_val,
            "emi_amount": emi_val,
            "credit_score": credit_score_val,
            "top_3_categories": [{"category": row[0], "amount": row[1]} for row in top_cats] if top_cats else [],
            "risk_profile": risk_profile,
            "savings_rate_pct": savings_rate_pct,
            "investable_surplus": investable_surplus,
            "expense_breakdown": (
                [{"category": row[0], "amount": row[1]} for row in expense_breakdown] if expense_breakdown else []
            ),
            "balance_history": (
                [{"date": row[0], "balance": row[1]} for row in balance_history] if balance_history else []
            ),
            "spending_alerts": (
                [{"category": row[0], "current": row[1], "average": row[2]} for row in spending_alerts]
                if spending_alerts
                else []
            ),
            "recent_transactions": recent_txns,
        }
    except duckdb.Error as e:
        logger.error("DuckDB query failed for customer %s: %s", customer_id, e)
        return {}
    except (TypeError, IndexError) as e:
        logger.error("Data extraction error for customer %s: %s", customer_id, e)
        return {}
