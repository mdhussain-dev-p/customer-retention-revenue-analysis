from __future__ import annotations

import numpy as np
import pandas as pd


def _quintile_score(values: pd.Series, higher_is_better: bool) -> pd.Series:
    ranks = values.rank(method="first", ascending=True)
    if not higher_is_better:
        ranks = values.rank(method="first", ascending=False)
    if len(values) == 1:
        return pd.Series([3], index=values.index, dtype="int64")
    scaled = (ranks - 1) / (len(values) - 1) * 4
    scores = np.rint(scaled).astype(int) + 1
    return scores.clip(1, 5)


def assign_rfm_segments(customers: pd.DataFrame) -> pd.DataFrame:
    required = {"customer_id", "recency_days", "frequency", "monetary_gbp"}
    missing = required.difference(customers.columns)
    if missing:
        raise ValueError("Missing RFM field(s): " + ", ".join(sorted(missing)))
    if customers.empty:
        return customers.copy()

    data = customers.copy()
    data = data.sort_values("customer_id").reset_index(drop=True)

    data["R_score"] = _quintile_score(data["recency_days"], higher_is_better=False)
    data["F_score"] = _quintile_score(data["frequency"], higher_is_better=True)
    data["M_score"] = _quintile_score(data["monetary_gbp"], higher_is_better=True)
    data["RFM_score"] = (
        data["R_score"].astype(str)
        + data["F_score"].astype(str)
        + data["M_score"].astype(str)
    )

    conditions = [
        (data["R_score"] >= 4) & (data["F_score"] >= 4) & (data["M_score"] >= 4),
        (data["F_score"] >= 4) & (data["R_score"] >= 3),
        (data["R_score"] >= 4) & (data["F_score"] >= 2),
        (data["R_score"] <= 2) & (data["F_score"] >= 3),
        (data["R_score"] <= 2) & (data["F_score"] <= 2),
    ]
    labels = [
        "Champions",
        "Loyal customers",
        "Potential loyalists",
        "At risk",
        "Lost",
    ]
    data["segment"] = np.select(conditions, labels, default="Needs attention")
    return data
