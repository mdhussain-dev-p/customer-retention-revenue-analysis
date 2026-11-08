# Findings and business interpretation

This report is generated from the transaction workbook. Each finding points to
a result table or chart in the project.

## Five findings

1. **Revenue over time.** Net product revenue across the complete reporting
   months was £18,507,343.72. 2011-11 was the highest month at
   £1,427,124.54. See `results/monthly_metrics.csv`
   and `figures/monthly_revenue.png`.

2. **Customer activity.** The RFM analysis includes 5,861
   identified customers with at least one qualifying purchase. Average
   month-one retention across cohorts with an observed month one was
   21.3%. See `results/cohort_retention.csv` and
   `figures/cohort_retention_heatmap.png`.

3. **Customer engagement varies.** The At risk segment contains
   821 customers with historical net spend of
   £1,333,062.78. See `results/customer_rfm.csv` and
   `results/rfm_segment_summary.csv`.

4. **Revenue is concentrated.** The top 20% of identified customers account
   for 76.7% of positive identified-customer revenue. The top
   20% of product codes account for 78.4% of positive product
   revenue. See the two Pareto result files and charts.

5. **Illustrative reactivation scenario.** A hypothetical 5% return rate among
   At risk customers represents 42 customers. At their
   average historical net spend of £1,623.71, the simple one-time
   scenario value is £68,195.66. This is not a forecast or
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
