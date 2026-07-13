"""
Unit tests for the Finvestor data engine module.

Tests cover:
    - calculate_risk_profile: deterministic risk bucketing logic.
    - build_customer_360: DuckDB-based aggregation pipeline.
"""

import pandas as pd
import pytest

from src.data_engine import build_customer_360, calculate_risk_profile

# ═══════════════════════════════════════════════════════════════════
# calculate_risk_profile
# ═══════════════════════════════════════════════════════════════════


class TestCalculateRiskProfile:
    """Verifies the deterministic risk profiling logic."""

    def test_aggressive_young_high_credit_high_savings(self) -> None:
        """Young customer with excellent credit and high savings → Aggressive."""
        result: str = calculate_risk_profile(age=28, credit_score=780, savings_rate=25.0)
        assert result == "Aggressive", f"Expected 'Aggressive' but got '{result}'"

    def test_moderate_middle_aged_good_credit(self) -> None:
        """Middle-aged customer with excellent credit and moderate savings → Moderate."""
        # age=45 → +2, credit_score=750 → +3, savings_rate=15 → +1 = 6 → Moderate
        result: str = calculate_risk_profile(age=45, credit_score=750, savings_rate=15.0)
        assert result == "Moderate", f"Expected 'Moderate' but got '{result}'"

    def test_conservative_older_low_credit(self) -> None:
        """Older customer with poor credit and low savings → Conservative."""
        result: str = calculate_risk_profile(age=60, credit_score=580, savings_rate=5.0)
        assert result == "Conservative", f"Expected 'Conservative' but got '{result}'"

    def test_boundary_scores(self) -> None:
        """Boundary condition: exactly at score threshold boundaries."""
        # age < 35 → +4, credit_score >= 650 → +1, savings_rate >= 10 → +1 = 6 → Moderate
        result: str = calculate_risk_profile(age=34, credit_score=650, savings_rate=10.0)
        assert result == "Moderate", f"Expected 'Moderate' at boundary but got '{result}'"


# ═══════════════════════════════════════════════════════════════════
# build_customer_360
# ═══════════════════════════════════════════════════════════════════


class TestBuildCustomer360:
    """Verifies the DuckDB-backed Customer_360 aggregation pipeline."""

    @pytest.fixture()
    def sample_transactions(self) -> pd.DataFrame:
        """Generate a minimal synthetic transaction DataFrame for testing.

        Returns:
            pd.DataFrame: A two-row DataFrame simulating credit and debit txns.
        """
        data: dict = {
            "customer_id": ["101", "101"],
            "transaction_date": pd.to_datetime(["2026-01-15", "2026-02-10"]),
            "transaction_amount": [50000.0, 12000.0],
            "transaction_direction": ["CR", "DR"],
            "account_balance": [150000.0, 138000.0],
            "merchant_category": ["Salary", "Groceries"],
            "age": [30, 30],
            "credit_score": [750, 750],
            "emi_amount": [5000.0, 5000.0],
            "txn_order": [0, 1],
        }
        return pd.DataFrame(data)

    def test_returns_non_empty_dict(self, sample_transactions: pd.DataFrame) -> None:
        """Customer_360 must return a non-empty dict for a valid customer."""
        result: dict = build_customer_360(sample_transactions, "101")
        assert isinstance(result, dict)
        assert len(result) > 0, "Expected non-empty Customer_360 dict"

    def test_correct_customer_id(self, sample_transactions: pd.DataFrame) -> None:
        """Returned profile must contain the correct customer_id."""
        result: dict = build_customer_360(sample_transactions, "101")
        assert result["customer_id"] == "101"

    def test_financial_aggregation_accuracy(self, sample_transactions: pd.DataFrame) -> None:
        """Verify inflow/outflow aggregation is numerically correct."""
        result: dict = build_customer_360(sample_transactions, "101")
        assert result["total_inflow_90d"] == 50000.0, "Inflow should be sum of CR transactions"
        assert result["total_outflow_90d"] == 12000.0, "Outflow should be sum of DR transactions"

    def test_unknown_customer_returns_empty(self, sample_transactions: pd.DataFrame) -> None:
        """Querying a non-existent customer should return an empty dict gracefully."""
        result: dict = build_customer_360(sample_transactions, "UNKNOWN_999")
        assert result == {} or result.get("total_inflow_90d", 0) == 0
