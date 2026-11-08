import pandas as pd
import pytest

from src.concentration import concentration_summary, top_share


def test_top_share_uses_the_highest_revenue_entities():
    data = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C", "D", "E"],
            "revenue": [50, 20, 15, 10, 5],
        }
    )

    summary = concentration_summary(data, "customer_id", "revenue")
    assert top_share(summary, 0.20) == pytest.approx(0.50)


def test_concentration_combines_multiple_rows_for_one_entity():
    data = pd.DataFrame(
        {
            "product": ["A", "A", "B"],
            "revenue": [20, 30, 50],
        }
    )

    summary = concentration_summary(data, "product", "revenue")
    assert summary.iloc[0]["product"] == "A"
    assert summary.iloc[0]["revenue"] == 50


def test_top_share_validates_fraction():
    with pytest.raises(ValueError):
        top_share(pd.DataFrame(), 0)
