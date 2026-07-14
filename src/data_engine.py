"""
Data processing engine for generating mock transactions and DuckDB analytics.
Strictly restricted to DuckDB/Persistence operations.
"""

import logging
from typing import Any

import duckdb
import pandas as pd
import streamlit as st

from src.domain.finance import calculate_risk_profile, compute_investable_surplus

logger: logging.Logger = logging.getLogger(__name__)

@st.cache_data
def load_transactions() -> pd.DataFrame:
    """Load transactions from CSV and prepare for DuckDB analytics."""
    try:
        df = pd.read_csv("data/bank_transactions.csv")
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df["customer_id"] = df["customer_id"].astype(str)
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

def build_customer_360(df: pd.DataFrame, customer_id: str) -> dict[str, Any]:
    """Register `df` in an in-memory DuckDB and return a Customer_360 dict."""
    try:
        con = duckdb.connect(":memory:")
        con.register("txn", df)

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

        balance_history = con.execute(
            """
            SELECT transaction_date, account_balance
            FROM txn
            WHERE customer_id = $1
            ORDER BY transaction_date ASC, txn_order ASC
            """,
            [customer_id],
        ).fetchall()

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
                "id": f"TXN-{8900 - i}",
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
