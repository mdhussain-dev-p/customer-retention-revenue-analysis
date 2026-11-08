SELECT
    strftime('%Y-%m', invoice_date) AS month,
    ROUND(SUM(line_revenue), 2) AS net_product_revenue_gbp,
    COUNT(DISTINCT CASE
        WHEN is_cancellation = 0 AND quantity > 0 THEN invoice_no
    END) AS completed_orders,
    COUNT(DISTINCT CASE
        WHEN is_cancellation = 0 AND quantity > 0
         AND customer_id IS NOT NULL AND trim(customer_id) <> ''
        THEN customer_id
    END) AS active_customers
FROM product_transactions
WHERE is_product = 1
  AND date(invoice_date) < '2011-12-01'
GROUP BY strftime('%Y-%m', invoice_date)
ORDER BY month;
