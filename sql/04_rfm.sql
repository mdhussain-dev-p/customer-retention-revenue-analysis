WITH customer_activity AS (
    SELECT
        customer_id,
        MAX(CASE
            WHEN is_cancellation = 0 AND quantity > 0
            THEN date(invoice_date)
        END) AS last_purchase_date,
        COUNT(DISTINCT CASE
            WHEN is_cancellation = 0 AND quantity > 0
            THEN invoice_no
        END) AS frequency,
        ROUND(SUM(line_revenue), 2) AS monetary_gbp
    FROM product_transactions
    WHERE is_product = 1
      AND customer_id IS NOT NULL
      AND trim(customer_id) <> ''
    GROUP BY customer_id
)
SELECT
    customer_id,
    last_purchase_date,
    frequency,
    monetary_gbp
FROM customer_activity
WHERE frequency > 0
ORDER BY customer_id;
