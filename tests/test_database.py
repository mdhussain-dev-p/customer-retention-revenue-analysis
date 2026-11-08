from datetime import datetime
import sqlite3

from openpyxl import Workbook

from src.load import load_workbook_into_database
from src.clean import (
    build_clean_tables,
    count_cancellation_invoices,
    count_missing_customer_ids,
    count_non_product_lines,
    remove_exact_duplicates,
    remove_invalid_prices,
    remove_unparseable_dates,
)


def make_sample_workbook(path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Year 1"
    sheet.append([
        "Invoice", "StockCode", "Description", "Quantity",
        "InvoiceDate", "Price", "Customer ID", "Country",
    ])
    sale = [
        "1001", "A1", "Mug", 2, datetime(2010, 1, 1, 10, 0), 10,
        101, "United Kingdom",
    ]
    sheet.append(sale)
    sheet.append(sale)
    sheet.append([
        "C1001", "A1", "Mug", -2, datetime(2010, 1, 10, 10, 0), 10,
        101, "United Kingdom",
    ])
    sheet.append([
        "1002", "B1", "Plate", 1, datetime(2010, 2, 5, 10, 0), 5,
        None, "United Kingdom",
    ])
    sheet.append([
        "1003", "POST", "Postage", 1, datetime(2010, 2, 5, 10, 0), 2,
        None, "United Kingdom",
    ])
    sheet.append([
        "1004", "A2", "Bowl", 1, datetime(2010, 3, 1, 10, 0), 0,
        102, "United Kingdom",
    ])
    sheet.append([
        "1005", "A3", "Cup", 1, "not a date", 3,
        103, "United Kingdom",
    ])
    sheet.append([
        "1006", "B1", "Plate", 3, datetime(2010, 2, 15, 10, 0), 5,
        102, "United Kingdom",
    ])
    workbook.save(path)


def test_workbook_loads_to_sqlite_and_cleaning_counts_are_auditable(tmp_path):
    workbook_path = tmp_path / "sample.xlsx"
    database_path = tmp_path / "sample.db"
    make_sample_workbook(workbook_path)

    loaded = load_workbook_into_database(workbook_path, database_path)
    assert loaded == 8

    connection = sqlite3.connect(database_path)
    counts = build_clean_tables(connection)

    assert connection.execute("SELECT COUNT(*) FROM raw_transactions").fetchone()[0] == 8
    assert connection.execute("SELECT COUNT(*) FROM cleaned_transactions").fetchone()[0] == 5

    removed_duplicates = counts.loc[
        counts["step"] == "Exact duplicate rows", "rows_removed"
    ].iloc[0]
    removed_prices = counts.loc[
        counts["step"] == "Zero, negative or missing unit prices", "rows_removed"
    ].iloc[0]
    removed_dates = counts.loc[
        counts["step"] == "Unparseable invoice dates", "rows_removed"
    ].iloc[0]
    missing_ids = counts.loc[
        counts["step"] == "Missing customer IDs", "rows_flagged"
    ].iloc[0]

    assert removed_duplicates == 1
    assert removed_prices == 1
    assert removed_dates == 1
    assert missing_ids == 2

    product_rows = connection.execute(
        "SELECT COUNT(*) FROM cleaned_transactions WHERE is_product = 1"
    ).fetchone()[0]
    cancellation_rows = connection.execute(
        "SELECT COUNT(*) FROM cleaned_transactions WHERE is_cancellation = 1"
    ).fetchone()[0]

    assert product_rows == 4
    assert cancellation_rows == 1
    connection.close()


def test_each_cleaning_rule_has_a_direct_row_count(tmp_path):
    workbook_path = tmp_path / "cleaning_rules.xlsx"
    database_path = tmp_path / "cleaning_rules.db"
    make_sample_workbook(workbook_path)
    load_workbook_into_database(workbook_path, database_path)

    connection = sqlite3.connect(database_path)

    assert count_missing_customer_ids(connection) == 2
    assert count_cancellation_invoices(connection) == 1
    assert count_non_product_lines(connection) == 1
    assert remove_invalid_prices(connection) == 1
    assert remove_exact_duplicates(connection) == 1
    assert remove_unparseable_dates(connection) == 1

    connection.close()
