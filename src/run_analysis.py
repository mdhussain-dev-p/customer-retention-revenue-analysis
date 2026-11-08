from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.concentration import concentration_summary, top_share
from src.rfm import assign_rfm_segments


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
DOCS = ROOT / "docs"


def read_sql(connection, filename):
    return pd.read_sql_query(
        (ROOT / "sql" / filename).read_text(encoding="utf-8"),
        connection,
    )


def save_csv(data, filename):
    RESULTS.mkdir(parents=True, exist_ok=True)
    data.to_csv(RESULTS / filename, index=False)


def save_charts(monthly, cohort_matrix, rfm, customer_pareto, product_pareto):
    FIGURES.mkdir(parents=True, exist_ok=True)

    monthly_plot = monthly.copy()
    monthly_plot["month"] = pd.to_datetime(monthly_plot["month"])
    figure, axis = plt.subplots(figsize=(11, 5))
    axis.plot(monthly_plot["month"], monthly_plot["net_product_revenue_gbp"], linewidth=1.8)
    axis.set(title="Monthly net product revenue", xlabel="Month", ylabel="Net product revenue (£)")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(FIGURES / "monthly_revenue.png", dpi=160)
    plt.close(figure)

    if not cohort_matrix.empty:
        figure, axis = plt.subplots(figsize=(12, 7))
        image = axis.imshow(cohort_matrix.to_numpy(dtype=float), aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
        axis.set(title="Monthly customer retention by first-purchase cohort",
                 xlabel="Months since first purchase", ylabel="Cohort month")
        axis.set_xticks(range(len(cohort_matrix.columns)))
        axis.set_xticklabels([str(value) for value in cohort_matrix.columns])
        axis.set_yticks(range(len(cohort_matrix.index)))
        axis.set_yticklabels(cohort_matrix.index)
        figure.colorbar(image, ax=axis, label="Share of cohort returning")
        figure.tight_layout()
        figure.savefig(FIGURES / "cohort_retention_heatmap.png", dpi=160)
        plt.close(figure)

    segment_counts = rfm["segment"].value_counts().sort_values()
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.barh(segment_counts.index, segment_counts.values)
    axis.set(title="Customers by RFM segment", xlabel="Number of customers", ylabel="Segment")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    figure.savefig(FIGURES / "rfm_segments.png", dpi=160)
    plt.close(figure)

    for data, name, filename in [
        (customer_pareto, "customers", "customer_pareto.png"),
        (product_pareto, "products", "product_pareto.png"),
    ]:
        if data.empty:
            continue
        display = data.head(20).copy()
        total = data.iloc[:, 1].sum()
        display["cumulative_share"] = display.iloc[:, 1].cumsum() / total
        figure, axis = plt.subplots(figsize=(11, 5))
        positions = range(len(display))
        axis.bar(positions, display.iloc[:, 1])
        axis.set(title=f"Revenue concentration across top {name}",
                 xlabel=name, ylabel="Net revenue (£)")
        axis.set_xticks(list(positions))
        axis.set_xticklabels(display.iloc[:, 0].astype(str), rotation=70, ha="right")
        share_axis = axis.twinx()
        share_axis.plot(positions, display["cumulative_share"] * 100, marker="o", linewidth=1.5)
        share_axis.set_ylabel("Cumulative share of positive revenue (%)")
        share_axis.set_ylim(0, 105)
        figure.tight_layout()
        figure.savefig(FIGURES / filename, dpi=160)
        plt.close(figure)


def write_cleaning_log(counts):
    lines = [
        "# Data cleaning log", "",
        "These row counts are generated from the workbook loaded into SQLite.", "",
        "| Rule | Rows in | Rows removed | Rows flagged | Rows out |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in counts.itertuples(index=False):
        lines.append(
            f"| {row.step} | {row.rows_in:,} | {row.rows_removed:,} "
            f"| {row.rows_flagged:,} | {row.rows_out:,} |"
        )
    lines.extend(["", "## Decisions", ""])
    for row in counts.itertuples(index=False):
        lines.append(f"- **{row.step}:** {row.decision}")
    lines.extend([
        "",
        "Guest purchases remain in revenue summaries and are excluded only from",
        "customer-level metrics. Cancellations are retained as negative adjustments",
        "and do not count as completed orders. Non-product lines remain in the",
        "cleaned audit table but are excluded from product analysis.",
    ])
    (DOCS / "cleaning_log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_findings(monthly, cohort, rfm, customer_pareto, product_pareto, at_risk):
    total_revenue = float(monthly["net_product_revenue_gbp"].sum())
    active_customers = int(rfm["customer_id"].nunique())
    peak = monthly.loc[monthly["net_product_revenue_gbp"].idxmax()]
    customer_share = top_share(customer_pareto)
    product_share = top_share(product_pareto)
    at_risk_count = len(at_risk)
    at_risk_spend = float(at_risk["monetary_gbp"].sum()) if at_risk_count else 0.0
    returning_customers = int(np.ceil(at_risk_count * 0.05))
    average_spend = at_risk_spend / at_risk_count if at_risk_count else 0.0
    scenario_revenue = returning_customers * average_spend
    month_one = cohort.loc[cohort["month_number"] == 1, "retention_rate"]
    retention_text = (
        f"{month_one.mean():.1%}" if not month_one.empty else "not available"
    )

    report = f"""# Findings and business interpretation

This report is generated from the transaction workbook. Each finding points to
a result table or chart in the project.

## Five findings

1. **Revenue over time.** Net product revenue across the complete reporting
   months was £{total_revenue:,.2f}. {peak['month']} was the highest month at
   £{peak['net_product_revenue_gbp']:,.2f}. See `results/monthly_metrics.csv`
   and `figures/monthly_revenue.png`.

2. **Customer activity.** The RFM analysis includes {active_customers:,}
   identified customers with at least one qualifying purchase. Average
   month-one retention across cohorts with an observed month one was
   {retention_text}. See `results/cohort_retention.csv` and
   `figures/cohort_retention_heatmap.png`.

3. **Customer engagement varies.** The At risk segment contains
   {at_risk_count:,} customers with historical net spend of
   £{at_risk_spend:,.2f}. See `results/customer_rfm.csv` and
   `results/rfm_segment_summary.csv`.

4. **Revenue is concentrated.** The top 20% of identified customers account
   for {customer_share:.1%} of positive identified-customer revenue. The top
   20% of product codes account for {product_share:.1%} of positive product
   revenue. See the two Pareto result files and charts.

5. **Illustrative reactivation scenario.** A hypothetical 5% return rate among
   At risk customers represents {returning_customers:,} customers. At their
   average historical net spend of £{average_spend:,.2f}, the simple one-time
   scenario value is £{scenario_revenue:,.2f}. This is not a forecast or
   guaranteed campaign outcome. See `results/recommendation_scenarios.csv`.

## Limitations

- The source describes one UK retailer over approximately two years.
- Rows without Customer IDs remain in revenue summaries but are excluded from
  customer cohorts and RFM analysis.
- December 2011 is incomplete and is excluded from monthly and cohort trends.
- Cancellation rows are negative adjustments; not every cancellation can be
  linked to its original invoice.
- RFM describes past behaviour and does not prove future customer value.
- Revenue is not profit; costs, taxes, fulfilment and marketing expenses are
  not available in this dataset.
- The 5% reactivation calculation is an illustrative scenario, not a causal
  estimate.
"""
    (DOCS / "findings.md").write_text(report, encoding="utf-8")

    scenario = pd.DataFrame([{
        "segment": "At risk",
        "historical_net_spend_gbp": at_risk_spend,
        "customer_count": at_risk_count,
        "assumed_reactivation_rate": 0.05,
        "illustrative_returning_customers": returning_customers,
        "average_historical_net_spend_gbp": average_spend,
        "illustrative_one_time_revenue_gbp": scenario_revenue,
        "note": "Scenario only; not a forecast or guaranteed campaign outcome.",
    }])
    save_csv(scenario, "recommendation_scenarios.csv")


def run_analysis(database_path: str | Path) -> dict[str, int]:
    from src.clean import build_clean_tables
    from src.load import connect_database

    RESULTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    connection = connect_database(database_path)
    try:
        cleaning_counts = build_clean_tables(connection)
        save_csv(cleaning_counts, "cleaning_counts.csv")
        write_cleaning_log(cleaning_counts)

        monthly = read_sql(connection, "02_monthly.sql")
        save_csv(monthly, "monthly_metrics.csv")

        cohort = read_sql(connection, "03_cohorts.sql")
        save_csv(cohort, "cohort_retention.csv")
        cohort_matrix = cohort.pivot(
            index="cohort_month", columns="month_number", values="retention_rate"
        ).sort_index()
        cohort_matrix.to_csv(RESULTS / "cohort_retention_matrix.csv")

        rfm_base = read_sql(connection, "04_rfm.sql")
        last_date = pd.read_sql_query(
            "SELECT MAX(date(invoice_date)) AS last_date FROM raw_transactions",
            connection,
        ).iloc[0, 0]
        reference_date = pd.to_datetime(last_date) + pd.Timedelta(days=1)
        rfm_base["last_purchase_date"] = pd.to_datetime(rfm_base["last_purchase_date"])
        rfm_base["recency_days"] = (
            reference_date - rfm_base["last_purchase_date"]
        ).dt.days
        rfm = assign_rfm_segments(rfm_base)
        rfm["reference_date"] = reference_date.strftime("%Y-%m-%d")
        save_csv(rfm, "customer_rfm.csv")

        segment_summary = (
            rfm.groupby("segment", as_index=False)
            .agg(
                customers=("customer_id", "nunique"),
                historical_net_spend_gbp=("monetary_gbp", "sum"),
                average_recency_days=("recency_days", "mean"),
                average_frequency=("frequency", "mean"),
            )
            .sort_values("customers", ascending=False)
        )
        save_csv(segment_summary, "rfm_segment_summary.csv")

        customer_pareto = concentration_summary(
            rfm[["customer_id", "monetary_gbp"]], "customer_id", "monetary_gbp"
        )
        save_csv(customer_pareto, "customer_pareto.csv")

        product_values = pd.read_sql_query(
            """
            SELECT stock_code, SUM(line_revenue) AS net_revenue_gbp
            FROM product_transactions
            WHERE is_product = 1
            GROUP BY stock_code
            """,
            connection,
        )
        product_pareto = concentration_summary(
            product_values, "stock_code", "net_revenue_gbp"
        )
        save_csv(product_pareto, "product_pareto.csv")

        save_charts(monthly, cohort_matrix, rfm, customer_pareto, product_pareto)
        at_risk = rfm.loc[rfm["segment"] == "At risk"].copy()
        write_findings(monthly, cohort, rfm, customer_pareto, product_pareto, at_risk)

        return {
            "cleaned_rows": int(connection.execute(
                "SELECT COUNT(*) FROM cleaned_transactions"
            ).fetchone()[0]),
            "customers": int(rfm["customer_id"].nunique()),
            "months": int(len(monthly)),
        }
    finally:
        connection.close()
