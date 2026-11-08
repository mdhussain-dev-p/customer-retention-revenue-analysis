from __future__ import annotations

from datetime import datetime
from typing import Any
import sqlite3
from pathlib import Path

import pandas as pd

NON_PRODUCT_CODES = {
    "POST", "M", "D", "DOT", "BANK CHARGES",
    "CRUK", "C2", "PADS", "AMAZONFEE", "S", "TEST001",
}


def normalise_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return None
    return text


def normalise_customer_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = normalise_text(value)
    if text is None:
        return None
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
    except ValueError:
        pass
    return text


def parse_invoice_date(value: Any) -> str | None:
    if value is None:
        return None
    try:
        stamp = pd.to_datetime(value, errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return None
    if pd.isna(stamp):
        return None
    return stamp.to_pydatetime().strftime("%Y-%m-%d %H:%M:%S")


def is_cancellation(invoice_no: Any) -> bool:
    invoice = normalise_text(invoice_no)
    return bool(invoice and invoice.upper().startswith("C"))


def is_product_code(stock_code: Any) -> bool:
    code = normalise_text(stock_code)
    return bool(code and code.upper() not in NON_PRODUCT_CODES)


def line_revenue(quantity: Any, unit_price: Any, cancellation: bool = False) -> float:
    amount = float(quantity) * float(unit_price)
    return -abs(amount) if cancellation else amount


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def count_missing_customer_ids(connection: sqlite3.Connection) -> int:
    return int(connection.execute(
        "SELECT COUNT(*) FROM raw_transactions "
        "WHERE customer_id IS NULL OR trim(customer_id) = ''"
    ).fetchone()[0])


def count_cancellation_invoices(connection: sqlite3.Connection) -> int:
    return int(connection.execute(
        "SELECT COUNT(*) FROM raw_transactions "
        "WHERE upper(substr(trim(invoice_no), 1, 1)) = 'C'"
    ).fetchone()[0])


def count_non_product_lines(connection: sqlite3.Connection) -> int:
    placeholders = ",".join("?" for _ in NON_PRODUCT_CODES)
    return int(connection.execute(
        f"SELECT COUNT(*) FROM raw_transactions "
        f"WHERE upper(trim(stock_code)) IN ({placeholders})",
        tuple(sorted(NON_PRODUCT_CODES)),
    ).fetchone()[0])


def remove_invalid_prices(connection: sqlite3.Connection) -> int:
    raw_count = _table_count(connection, "raw_transactions")
    connection.execute("DROP TABLE IF EXISTS price_valid_transactions")
    connection.execute(
        """
        CREATE TABLE price_valid_transactions AS
        SELECT * FROM raw_transactions
        WHERE unit_price IS NOT NULL AND unit_price > 0
        """
    )
    return raw_count - _table_count(connection, "price_valid_transactions")


def remove_exact_duplicates(connection: sqlite3.Connection) -> int:
    price_valid_count = _table_count(connection, "price_valid_transactions")
    connection.execute("DROP TABLE IF EXISTS deduplicated_transactions")
    connection.execute(
        """
        CREATE TABLE deduplicated_transactions AS
        SELECT DISTINCT
            invoice_no, stock_code, description, quantity,
            invoice_date, unit_price, customer_id, country
        FROM price_valid_transactions
        """
    )
    return price_valid_count - _table_count(connection, "deduplicated_transactions")


def remove_unparseable_dates(connection: sqlite3.Connection) -> int:
    deduplicated_count = _table_count(connection, "deduplicated_transactions")
    invalid_count = int(connection.execute(
        "SELECT COUNT(*) FROM deduplicated_transactions "
        "WHERE invoice_date IS NULL OR date(invoice_date) IS NULL"
    ).fetchone()[0])
    connection.execute("DROP TABLE IF EXISTS valid_date_transactions")
    connection.execute(
        """
        CREATE TABLE valid_date_transactions AS
        SELECT * FROM deduplicated_transactions
        WHERE invoice_date IS NOT NULL AND date(invoice_date) IS NOT NULL
        """
    )
    if _table_count(connection, "valid_date_transactions") != deduplicated_count - invalid_count:
        raise RuntimeError("Date-cleaning row counts do not reconcile.")
    return invalid_count


def build_clean_tables(connection: sqlite3.Connection) -> pd.DataFrame:
    raw_count = _table_count(connection, "raw_transactions")

    missing_customer_count = count_missing_customer_ids(connection)
    cancellation_count = count_cancellation_invoices(connection)
    non_product_count = count_non_product_lines(connection)

    invalid_price_count = remove_invalid_prices(connection)
    price_valid_count = _table_count(connection, "price_valid_transactions")

    duplicate_count = remove_exact_duplicates(connection)
    deduplicated_count = _table_count(connection, "deduplicated_transactions")

    invalid_date_count = remove_unparseable_dates(connection)
    clean_count = _table_count(connection, "valid_date_transactions")

    sql_path = Path(__file__).resolve().parents[1] / "sql" / "01_clean.sql"
    connection.executescript(sql_path.read_text(encoding="utf-8"))

    return pd.DataFrame([
        {
            "step": "Missing customer IDs",
            "rows_in": raw_count,
            "rows_removed": 0,
            "rows_flagged": missing_customer_count,
            "rows_out": raw_count,
            "decision": "Retained for revenue summaries; excluded from customer-level analysis.",
        },
        {
            "step": "Cancellation invoices",
            "rows_in": raw_count,
            "rows_removed": 0,
            "rows_flagged": cancellation_count,
            "rows_out": raw_count,
            "decision": "Separated into a cancellation table and used as negative adjustments.",
        },
        {
            "step": "Non-product stock codes",
            "rows_in": raw_count,
            "rows_removed": 0,
            "rows_flagged": non_product_count,
            "rows_out": raw_count,
            "decision": "Separated from product lines and excluded from product analysis.",
        },
        {
            "step": "Zero, negative or missing unit prices",
            "rows_in": raw_count,
            "rows_removed": invalid_price_count,
            "rows_flagged": invalid_price_count,
            "rows_out": raw_count - invalid_price_count,
            "decision": "Removed because a valid line needs a positive unit price.",
        },
        {
            "step": "Exact duplicate rows",
            "rows_in": price_valid_count,
            "rows_removed": duplicate_count,
            "rows_flagged": duplicate_count,
            "rows_out": deduplicated_count,
            "decision": "One copy of each exact transaction row was retained.",
        },
        {
            "step": "Unparseable invoice dates",
            "rows_in": deduplicated_count,
            "rows_removed": invalid_date_count,
            "rows_flagged": invalid_date_count,
            "rows_out": clean_count,
            "decision": "Removed because time-based analysis requires a valid date.",
        },
    ])
