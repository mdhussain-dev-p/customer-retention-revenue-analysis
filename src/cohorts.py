from __future__ import annotations

import pandas as pd


def build_cohort_retention(monthly_activity: pd.DataFrame) -> pd.DataFrame:
    required = {"customer_id", "invoice_date"}
    missing = required.difference(monthly_activity.columns)
    if missing:
        raise ValueError("Missing cohort field(s): " + ", ".join(sorted(missing)))

    data = monthly_activity.loc[:, ["customer_id", "invoice_date"]].copy()
    data = data.dropna(subset=["customer_id", "invoice_date"])
    if data.empty:
        return pd.DataFrame()

    data["invoice_date"] = pd.to_datetime(data["invoice_date"], errors="coerce")
    data = data.dropna(subset=["invoice_date"])
    data["activity_month"] = data["invoice_date"].dt.to_period("M")
    data = data.drop_duplicates(["customer_id", "activity_month"])

    first_month = data.groupby("customer_id")["activity_month"].min()
    data["cohort_month"] = data["customer_id"].map(first_month)
    data["month_number"] = (
        (data["activity_month"].dt.year - data["cohort_month"].dt.year) * 12
        + data["activity_month"].dt.month
        - data["cohort_month"].dt.month
    )

    cohort_sizes = data.groupby("cohort_month")["customer_id"].nunique()
    active = data.groupby(
        ["cohort_month", "month_number"]
    )["customer_id"].nunique()

    retention = (
        active.div(cohort_sizes, level="cohort_month")
        .rename("retention_rate")
        .reset_index()
    )
    retention["cohort_month"] = retention["cohort_month"].astype(str)
    retention["retention_rate"] = retention["retention_rate"].astype(float)
    return retention


def retention_matrix(retention: pd.DataFrame) -> pd.DataFrame:
    if retention.empty:
        return pd.DataFrame()
    return retention.pivot(
        index="cohort_month",
        columns="month_number",
        values="retention_rate",
    ).sort_index()
