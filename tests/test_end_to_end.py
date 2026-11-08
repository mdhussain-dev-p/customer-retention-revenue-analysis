from datetime import datetime
import sqlite3

from openpyxl import Workbook

from src.load import load_workbook_into_database
from src.run_analysis import run_analysis


def test_full_analysis_creates_reports_and_charts(tmp_path, monkeypatch):
    workbook_path = tmp_path / "mini_retail.xlsx"
    database_path = tmp_path / "mini_retail.db"

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sample"
    sheet.append([
        "Invoice", "StockCode", "Description", "Quantity",
        "InvoiceDate", "Price", "Customer ID", "Country",
    ])
    sheet.append(["1001", "A1", "Mug", 2, datetime(2010, 1, 1), 10, 101, "UK"])
    sheet.append(["C1001", "A1", "Mug", -2, datetime(2010, 1, 10), 10, 101, "UK"])
    sheet.append(["1002", "B1", "Plate", 1, datetime(2010, 2, 5), 5, None, "UK"])
    sheet.append(["1003", "POST", "Postage", 1, datetime(2010, 2, 5), 2, None, "UK"])
    sheet.append(["1004", "B1", "Plate", 3, datetime(2010, 2, 15), 5, 102, "UK"])
    workbook.save(workbook_path)

    load_workbook_into_database(workbook_path, database_path)

    import src.run_analysis as analysis

    monkeypatch.setattr(analysis, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(analysis, "FIGURES", tmp_path / "figures")
    monkeypatch.setattr(analysis, "DOCS", tmp_path / "docs")

    summary = run_analysis(database_path)

    assert summary["cleaned_rows"] == 5
    assert summary["customers"] == 2
    assert summary["months"] == 2

    expected_results = [
        "cleaning_counts.csv",
        "monthly_metrics.csv",
        "cohort_retention.csv",
        "cohort_retention_matrix.csv",
        "customer_rfm.csv",
        "rfm_segment_summary.csv",
        "customer_pareto.csv",
        "product_pareto.csv",
        "recommendation_scenarios.csv",
    ]
    for name in expected_results:
        assert (tmp_path / "results" / name).is_file()

    expected_figures = [
        "monthly_revenue.png",
        "cohort_retention_heatmap.png",
        "rfm_segments.png",
        "customer_pareto.png",
        "product_pareto.png",
    ]
    for name in expected_figures:
        assert (tmp_path / "figures" / name).is_file()

    assert (tmp_path / "docs" / "cleaning_log.md").is_file()
    assert (tmp_path / "docs" / "findings.md").is_file()
