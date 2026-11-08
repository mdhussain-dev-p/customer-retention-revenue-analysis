from __future__ import annotations

import pandas as pd


def concentration_summary(
    values: pd.DataFrame,
    entity_column: str,
    revenue_column: str,
) -> pd.DataFrame:
    required = {entity_column, revenue_column}
    missing = required.difference(values.columns)
    if missing:
        raise ValueError("Missing concentration field(s): " + ", ".join(sorted(missing)))

    data = values.loc[:, [entity_column, revenue_column]].copy()
    data[revenue_column] = pd.to_numeric(data[revenue_column], errors="coerce")
    data = data.dropna(subset=[entity_column, revenue_column])
    data = data.groupby(entity_column, as_index=False)[revenue_column].sum()
    data = data.sort_values(revenue_column, ascending=False).reset_index(drop=True)
    data = data.loc[data[revenue_column] > 0].copy()

    if data.empty:
        return data.assign(
            rank=pd.Series(dtype="int64"),
            cumulative_revenue_gbp=pd.Series(dtype="float64"),
            cumulative_share=pd.Series(dtype="float64"),
        )

    total = data[revenue_column].sum()
    data["rank"] = range(1, len(data) + 1)
    data["cumulative_revenue_gbp"] = data[revenue_column].cumsum()
    data["cumulative_share"] = data["cumulative_revenue_gbp"] / total
    return data


def top_share(summary: pd.DataFrame, fraction: float = 0.20) -> float:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be greater than 0 and at most 1.")
    if summary.empty:
        return 0.0
    count = max(1, int(len(summary) * fraction))
    denominator = summary.iloc[:, 1].sum()
    if denominator <= 0:
        return 0.0
    return float(summary.iloc[:count, 1].sum() / denominator)
