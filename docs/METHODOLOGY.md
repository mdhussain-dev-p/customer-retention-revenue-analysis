# Methodology

## Business question

The analysis looks at where product revenue comes from, how often identified
customers return, and how past purchase behaviour can be used to describe
customer groups. The data describes one UK-based online retailer, so the
findings apply to this business and period rather than to retail in general.

## Revenue and transaction rules

A line value is quantity multiplied by unit price. Invoice numbers beginning
with `C` are treated as cancellation records and stored as negative
adjustments. They are not counted as completed orders. Other negative-quantity
lines also reduce net revenue.

Rows without a Customer ID remain in the revenue-only transaction base. They
are not used for customer cohorts or RFM because there is no reliable customer
identifier.

A small, documented list of administrative or service stock codes is kept out
of product analysis. The codes and rule are visible in `src/clean.py`.

## Monthly reporting

Monthly net product revenue includes eligible merchandise sale lines and
negative cancellation or return adjustments. Completed orders count distinct
non-cancellation invoices with positive quantities. Active customers count
identified customers with at least one such purchase during the month.

The final source month ends on 9 December 2011. December 2011 is therefore
excluded from monthly trend comparisons and cohort activity to avoid treating
a partial month as a complete month.

## Cohort retention

Customers are assigned to the calendar month of their first qualifying
purchase. Each following month is numbered from that first month. A customer
is active in a month when they have at least one qualifying purchase in it.
Retention is the number of active customers in a cohort-month divided by the
number of customers in the original cohort.

Cells for months that have not yet elapsed are left blank in the retention
matrix, not filled with zero.

## RFM analysis

The reference date is fixed as the day after the last transaction date in the
workbook. It does not use today's date.

- Recency is the number of days since the customer's latest qualifying purchase.
- Frequency is the number of distinct completed purchase invoices.
- Monetary is net product spend after signed return and cancellation
  adjustments attached to the same Customer ID.

Scores run from 1 to 5. Recency is scored in reverse (a more recent purchase
gets a higher score); frequency and monetary are scored higher for larger
values. Ties are made reproducible by sorting on customer ID before ranking.

The segment rules are applied in the following order:

1. Champions: R, F and M are all at least 4.
2. Loyal customers: F is at least 4 and R is at least 3.
3. Potential loyalists: R is at least 4 and F is at least 2.
4. At risk: R is at most 2 and F is at least 3.
5. Lost: R and F are both at most 2.
6. Needs attention: any customer not captured above.

## Revenue concentration

Customer concentration is calculated among customers with an ID and a
positive net monetary total. Product concentration is calculated across
product codes with positive net revenue. Each Pareto file is sorted from
highest to lowest revenue.

## Reactivation scenario

The illustrative scenario assumes 5% of customers in the At risk segment
return once and spend the segment's historical average net spend. The output
is explicitly a scenario, not an estimate of campaign effectiveness. No
marketing costs, margins or future repeat purchases are modelled.
