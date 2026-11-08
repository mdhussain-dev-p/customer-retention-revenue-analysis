WITH eligible_orders AS (
    SELECT DISTINCT
        customer_id,
        date(invoice_date, 'start of month') AS activity_month
    FROM product_transactions
    WHERE is_product = 1
      AND is_cancellation = 0
      AND quantity > 0
      AND customer_id IS NOT NULL
      AND trim(customer_id) <> ''
      AND date(invoice_date) < '2011-12-01'
),
first_purchase AS (
    SELECT customer_id, MIN(activity_month) AS cohort_month
    FROM eligible_orders
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        e.activity_month,
        CAST(
            (CAST(strftime('%Y', e.activity_month) AS INTEGER)
             - CAST(strftime('%Y', f.cohort_month) AS INTEGER)) * 12
            + CAST(strftime('%m', e.activity_month) AS INTEGER)
            - CAST(strftime('%m', f.cohort_month) AS INTEGER)
            AS INTEGER
        ) AS month_number,
        COUNT(DISTINCT e.customer_id) AS active_customers
    FROM eligible_orders e
    JOIN first_purchase f USING (customer_id)
    GROUP BY f.cohort_month, e.activity_month
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.month_number,
    a.active_customers,
    s.cohort_size,
    1.0 * a.active_customers / s.cohort_size AS retention_rate
FROM cohort_activity a
JOIN cohort_sizes s USING (cohort_month)
ORDER BY a.cohort_month, a.month_number;
