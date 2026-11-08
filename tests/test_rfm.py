import pandas as pd

from src.rfm import assign_rfm_segments


def test_rfm_scores_stay_between_one_and_five():
    customers = pd.DataFrame(
        {
            "customer_id": [str(value) for value in range(1, 11)],
            "recency_days": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
            "frequency": [20, 18, 16, 14, 12, 10, 8, 6, 4, 2],
            "monetary_gbp": [1000, 900, 800, 700, 600, 500, 400, 300, 200, 100],
        }
    )

    scored = assign_rfm_segments(customers)

    for column in ("R_score", "F_score", "M_score"):
        assert scored[column].between(1, 5).all()


def test_rfm_segment_counts_add_up_to_customer_count():
    customers = pd.DataFrame(
        {
            "customer_id": [str(value) for value in range(1, 21)],
            "recency_days": list(range(1, 21)),
            "frequency": list(range(20, 0, -1)),
            "monetary_gbp": [value * 100 for value in range(20, 0, -1)],
        }
    )

    scored = assign_rfm_segments(customers)
    assert scored["segment"].notna().all()
    assert scored["customer_id"].nunique() == customers["customer_id"].nunique()
    assert scored["segment"].value_counts().sum() == len(customers)


def test_rfm_handles_tied_frequency_values():
    customers = pd.DataFrame(
        {
            "customer_id": [str(value) for value in range(1, 8)],
            "recency_days": [1, 2, 3, 4, 5, 6, 7],
            "frequency": [1, 1, 1, 2, 2, 2, 3],
            "monetary_gbp": [10, 20, 30, 40, 50, 60, 70],
        }
    )

    scored = assign_rfm_segments(customers)
    assert scored["F_score"].between(1, 5).all()
