import json
from pathlib import Path

import pandas as pd

from src.data_engine import build_customer_360, load_transactions


def test_load_transactions_schema():
    # Setup
    customer_id = "101"

    # Action (takes no arguments)
    df = load_transactions()

    # Assertion
    assert not df.empty, "DataFrame should not be empty"
    expected_columns = [
        "customer_id",
        "age",
        "transaction_date",
        "transaction_amount",
        "transaction_direction",
        "merchant_category",
        "account_balance",
        "emi_amount",
        "credit_score",
        "txn_order",
    ]
    assert all(col in df.columns for col in expected_columns), "DataFrame is missing expected columns"
    assert customer_id in df["customer_id"].values, "Generated data is missing required customer IDs"


def test_build_customer_360_aggregation():
    # Setup - Load deterministic fixture
    fixture_path = Path(__file__).parent / "fixtures" / "mock_transactions.json"
    with open(fixture_path) as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    # Action
    c360 = build_customer_360(df, "TEST-ID")

    # Assertion
    assert c360["customer_id"] == "TEST-ID"
    assert c360["total_inflow_90d"] == 1000.0
    assert c360["total_outflow_90d"] == 500.0
