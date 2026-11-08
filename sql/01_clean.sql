DROP TABLE IF EXISTS cleaned_transactions;

CREATE TABLE cleaned_transactions AS
SELECT
    invoice_no,
    stock_code,
    description,
    quantity,
    invoice_date,
    unit_price,
    customer_id,
    country,
    CASE WHEN upper(substr(trim(invoice_no), 1, 1)) = 'C' THEN 1 ELSE 0 END AS is_cancellation,
    CASE
        WHEN upper(trim(stock_code)) IN (
            'POST', 'M', 'D', 'DOT', 'BANK CHARGES', 'CRUK',
            'C2', 'PADS', 'AMAZONFEE', 'S', 'TEST001'
        ) THEN 0
        ELSE 1
    END AS is_product,
    CASE
        WHEN upper(substr(trim(invoice_no), 1, 1)) = 'C'
            THEN -abs(quantity * unit_price)
        ELSE quantity * unit_price
    END AS line_revenue
FROM valid_date_transactions;

DROP TABLE IF EXISTS product_transactions;
CREATE TABLE product_transactions AS
SELECT * FROM cleaned_transactions WHERE is_product = 1;

DROP TABLE IF EXISTS non_product_transactions;
CREATE TABLE non_product_transactions AS
SELECT * FROM cleaned_transactions WHERE is_product = 0;

DROP TABLE IF EXISTS cancellation_transactions;
CREATE TABLE cancellation_transactions AS
SELECT * FROM cleaned_transactions WHERE is_cancellation = 1;
