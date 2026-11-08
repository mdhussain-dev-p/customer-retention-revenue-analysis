import pandas as pd

from src.cohorts import build_cohort_retention, retention_matrix


def test_cohort_retention_uses_months_since_first_purchase():
    activity = pd.DataFrame(
        {
            "customer_id": ["A", "A", "B", "B", "C"],
            "invoice_date": [
                "2010-01-10", "2010-02-10", "2010-01-15",
                "2010-03-10", "2010-02-15",
            ],
        }
    )

    retention = build_cohort_retention(activity)
    matrix = retention_matrix(retention)

    assert matrix.loc["2010-01", 0] == 1.0
    assert matrix.loc["2010-01", 1] == 0.5
    assert matrix.loc["2010-01", 2] == 0.5
    assert matrix.loc["2010-02", 0] == 1.0


def test_cohort_retention_deduplicates_multiple_orders_in_same_month():
    activity = pd.DataFrame(
        {
            "customer_id": ["A", "A", "A"],
            "invoice_date": ["2010-01-01", "2010-01-10", "2010-02-01"],
        }
    )

    retention = build_cohort_retention(activity)
    assert retention.loc[retention["month_number"] == 0, "retention_rate"].iloc[0] == 1.0
    assert retention.loc[retention["month_number"] == 1, "retention_rate"].iloc[0] == 1.0


def test_empty_cohort_data_returns_empty_result():
    result = build_cohort_retention(
        pd.DataFrame(columns=["customer_id", "invoice_date"])
    )
    assert result.empty
