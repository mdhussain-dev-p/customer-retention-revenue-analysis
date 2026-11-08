from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from openpyxl import load_workbook

from src.clean import (
    normalise_customer_id,
    normalise_text,
    parse_invoice_date,
)


RAW_COLUMNS = (
    "invoice_no", "stock_code", "description", "quantity",
    "invoice_date", "unit_price", "customer_id", "country",
)
HEADER_ALIASES = {
    "invoiceno": "invoice_no",
    "invoice": "invoice_no",
    "stockcode": "stock_code",
    "description": "description",
    "quantity": "quantity",
    "invoicedate": "invoice_date",
    "price": "unit_price",
    "unitprice": "unit_price",
    "customerid": "customer_id",
    "country": "country",
}


def connect_database(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


def create_raw_table(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS raw_transactions")
    connection.execute(
        """
        CREATE TABLE raw_transactions (
            invoice_no TEXT,
            stock_code TEXT,
            description TEXT,
            quantity REAL,
            invoice_date TEXT,
            unit_price REAL,
            customer_id TEXT,
            country TEXT,
            source_sheet TEXT
        )
        """
    )
    connection.commit()


def _header_map(values: Iterable[object]) -> dict[str, int]:
    mapping = {}
    for index, value in enumerate(values):
        key = "".join(ch for ch in str(value or "").lower() if ch.isalnum())
        if key in HEADER_ALIASES:
            mapping[HEADER_ALIASES[key]] = index
    missing = set(RAW_COLUMNS).difference(mapping)
    if missing:
        raise ValueError(
            "The workbook is missing expected column(s): "
            + ", ".join(sorted(missing))
        )
    return mapping


def _cell_value(row: tuple, mapping: dict[str, int], column: str):
    index = mapping[column]
    return row[index] if index < len(row) else None


def _number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_workbook_into_database(
    workbook_path: str | Path,
    database_path: str | Path,
    batch_size: int = 10000,
) -> int:
    workbook_path = Path(workbook_path)
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    connection = connect_database(database_path)
    create_raw_table(connection)
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    inserted = 0
    batch = []

    insert_sql = """
        INSERT INTO raw_transactions (
            invoice_no, stock_code, description, quantity,
            invoice_date, unit_price, customer_id, country, source_sheet
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        for sheet in workbook.worksheets:
            rows = sheet.iter_rows(values_only=True)
            header = next(rows, None)
            if header is None:
                continue
            mapping = _header_map(header)

            for row in rows:
                invoice = normalise_text(_cell_value(row, mapping, "invoice_no"))
                stock = normalise_text(_cell_value(row, mapping, "stock_code"))
                if invoice is None and stock is None:
                    continue

                date_value = _cell_value(row, mapping, "invoice_date")
                batch.append(
                    (
                        invoice,
                        stock,
                        normalise_text(_cell_value(row, mapping, "description")),
                        _number(_cell_value(row, mapping, "quantity")),
                        parse_invoice_date(date_value),
                        _number(_cell_value(row, mapping, "unit_price")),
                        normalise_customer_id(_cell_value(row, mapping, "customer_id")),
                        normalise_text(_cell_value(row, mapping, "country")),
                        sheet.title,
                    )
                )

                if len(batch) >= batch_size:
                    connection.executemany(insert_sql, batch)
                    connection.commit()
                    inserted += len(batch)
                    batch.clear()

        if batch:
            connection.executemany(insert_sql, batch)
            connection.commit()
            inserted += len(batch)
    finally:
        workbook.close()
        connection.close()

    return inserted
