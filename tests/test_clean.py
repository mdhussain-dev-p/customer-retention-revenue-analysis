import sqlite3

import pandas as pd
import pytest

from src.clean import (
    is_cancellation,
    is_product_code,
    line_revenue,
    normalise_customer_id,
    parse_invoice_date,
)
from src.clean import build_clean_tables


@pytest.mark.parametrize(
    ("invoice", "expected"),
    [("C536365", True), ("c536366", True), ("536367", False), (None, False)],
)
def test_cancellation_detection(invoice, expected):
    assert is_cancellation(invoice) is expected


@pytest.mark.parametrize(
    ("code", "expected"),
    [("POST", False), ("M", False), ("BANK CHARGES", False), ("85123A", True)],
)
def test_product_code_classification(code, expected):
    assert is_product_code(code) is expected


def test_customer_ids_are_normalised():
    assert normalise_customer_id(13085.0) == "13085"
    assert normalise_customer_id(" 13085 ") == "13085"
    assert normalise_customer_id(None) is None


def test_invoice_date_parser_handles_excel_datetime_and_bad_values():
    assert parse_invoice_date(pd.Timestamp("2010-12-01 08:30:00")) == "2010-12-01 08:30:00"
    assert parse_invoice_date("not a date") is None


def test_cancellation_revenue_is_always_a_negative_adjustment():
    assert line_revenue(-2, 5, cancellation=True) == -10
    assert line_revenue(2, 5, cancellation=True) == -10
    assert line_revenue(2, 5, cancellation=False) == 10


def test_cleaning_log_counts_and_retention_decisions():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE raw_transactions (
            invoice_no TEXT, stock_code TEXT, description TEXT,
            quantity REAL, invoice_date TEXT, unit_price REAL,
            customer_id TEXT, country TEXT, source_sheet TEXT
        )
        """
    )
    rows = [
        ("1001", "A1", "Mug", 2, "2010-01-01 10:00:00", 5, "101", "UK", "Sheet1"),
        ("1001", "A1", "Mug", 2, "2010-01-01 10:00:00", 5, "101", "UK", "Sheet1"),
        ("C1001", "A1", "Mug", -2, "2010-01-02 10:00:00", 5, "101", "UK", "Sheet1"),
        ("1002", "POST", "Postage", 1, "2010-01-03 10:00:00", 2, None, "UK", "Sheet1"),
        ("1003", "A2", "Plate", 1, "2010-01-03 10:00:00", 0, "102", "UK", "Sheet1"),
        ("1004", "A3", "Bowl", 1, "bad date", 3, "103", "UK", "Sheet1"),
    ]
    connection.executemany(
        "INSERT INTO raw_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

    counts = build_clean_tables(connection)

    assert counts.loc[counts["step"] == "Missing customer IDs", "rows_flagged"].iloc[0] == 1
    assert counts.loc[counts["step"] == "Cancellation invoices", "rows_flagged"].iloc[0] == 1
    assert counts.loc[counts["step"] == "Exact duplicate rows", "rows_removed"].iloc[0] == 1
    assert counts.loc[counts["step"] == "Zero, negative or missing unit prices", "rows_removed"].iloc[0] == 1
    assert counts.loc[counts["step"] == "Unparseable invoice dates", "rows_removed"].iloc[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM cleaned_transactions").fetchone()[0] == 3
    connection.close()
