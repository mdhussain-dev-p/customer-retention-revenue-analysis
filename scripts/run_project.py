from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.run_analysis import run_analysis
from src.load import load_workbook_into_database


RAW_WORKBOOK = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"
DATABASE = PROJECT_ROOT / "data" / "retail.db"
RESULTS_FOLDER = PROJECT_ROOT / "results"
LOG_FOLDER = PROJECT_ROOT / "logs"
LOG_FILE = LOG_FOLDER / "project_run.log"
EXPECTED_SOURCE_ROWS = 1_067_371


def existing_raw_row_count(database_path: Path) -> int:
    if not database_path.exists():
        return 0
    try:
        with sqlite3.connect(database_path) as connection:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='raw_transactions'"
            ).fetchone()
            if not exists:
                return 0
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM raw_transactions"
                ).fetchone()[0]
            )
    except sqlite3.Error:
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the customer retention and revenue analysis."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Rebuild the local SQLite database from the original workbook.",
    )
    args = parser.parse_args()

    if not RAW_WORKBOOK.exists():
        raise FileNotFoundError(
            "The raw workbook was not found. Run "
            "'python scripts/download_data.py' first."
        )

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    LOG_FOLDER.mkdir(parents=True, exist_ok=True)

    cached_rows = 0 if args.reload else existing_raw_row_count(DATABASE)
    if cached_rows:
        rows_loaded = cached_rows
        import_action = "Reused the existing local SQLite import"
        print(f"Using the existing SQLite database ({rows_loaded:,} source rows).")
    else:
        print("Loading the UCI workbook into SQLite in batches...")
        rows_loaded = load_workbook_into_database(RAW_WORKBOOK, DATABASE)
        import_action = "Imported the workbook into SQLite"
        print(f"Rows loaded: {rows_loaded:,}")

    row_count_matches = rows_loaded == EXPECTED_SOURCE_ROWS
    print(f"UCI listed row count: {EXPECTED_SOURCE_ROWS:,}")
    print(f"Source row count matches: {row_count_matches}")

    print("\nRunning the cleaning and analysis workflow...")
    summary = run_analysis(DATABASE)

    loading_summary = pd.DataFrame([{
        "workbook": RAW_WORKBOOK.name,
        "database_action": import_action,
        "source_rows": rows_loaded,
        "uci_listed_rows": EXPECTED_SOURCE_ROWS,
        "row_count_matches_uci_record": row_count_matches,
        "cleaned_rows": summary["cleaned_rows"],
        "customers_analysed": summary["customers"],
        "complete_months_reported": summary["months"],
        "rfm_reference_date": "Day after the last valid transaction date in the source table",
    }])
    loading_summary.to_csv(
        RESULTS_FOLDER / "data_loading_summary.csv",
        index=False,
    )

    message = (
        "Customer retention and revenue analysis completed.\n"
        f"Completed at: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Workbook: {RAW_WORKBOOK.name}\n"
        f"Database action: {import_action}\n"
        f"Source rows: {rows_loaded:,}\n"
        f"UCI listed rows: {EXPECTED_SOURCE_ROWS:,}\n"
        f"Source row count matches: {row_count_matches}\n"
        f"Rows retained after cleaning: {summary['cleaned_rows']:,}\n"
        f"Customers analysed: {summary['customers']:,}\n"
        f"Complete months reported: {summary['months']:,}\n"
        "Cleaning log: docs/cleaning_log.md\n"
        "Findings: docs/findings.md\n"
        "Tables: results/\n"
        "Charts: figures/\n"
    )
    print("\n" + message)
    LOG_FILE.write_text(message, encoding="utf-8")
    print(f"Run summary saved to {LOG_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
