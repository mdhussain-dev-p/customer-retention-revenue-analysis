# Data cleaning log

These row counts are generated from the workbook loaded into SQLite.

| Rule | Rows in | Rows removed | Rows flagged | Rows out |
|---|---:|---:|---:|---:|
| Missing customer IDs | 1,067,371 | 0 | 243,007 | 1,067,371 |
| Cancellation invoices | 1,067,371 | 0 | 19,494 | 1,067,371 |
| Non-product stock codes | 1,067,371 | 0 | 5,752 | 1,067,371 |
| Zero, negative or missing unit prices | 1,067,371 | 6,207 | 6,207 | 1,061,164 |
| Exact duplicate rows | 1,061,164 | 34,147 | 34,147 | 1,027,017 |
| Unparseable invoice dates | 1,027,017 | 0 | 0 | 1,027,017 |

## Decisions

- **Missing customer IDs:** Retained for revenue summaries; excluded from customer-level analysis.
- **Cancellation invoices:** Separated into a cancellation table and used as negative adjustments.
- **Non-product stock codes:** Separated from product lines and excluded from product analysis.
- **Zero, negative or missing unit prices:** Removed because a valid line needs a positive unit price.
- **Exact duplicate rows:** One copy of each exact transaction row was retained.
- **Unparseable invoice dates:** Removed because time-based analysis requires a valid date.

Guest purchases remain in revenue summaries and are excluded only from
customer-level metrics. Cancellations are retained as negative adjustments
and do not count as completed orders. Non-product lines remain in the
cleaned audit table but are excluded from product analysis.
