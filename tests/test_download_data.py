import zipfile

import pytest

from scripts.download_data import extract_workbook


def test_zip_extractor_saves_the_excel_workbook(tmp_path):
    archive_path = tmp_path / "source.zip"
    workbook_bytes = b"sample workbook bytes"

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("online_retail_II.xlsx", workbook_bytes)

    output_path = extract_workbook(archive_path, tmp_path / "raw" / "retail.xlsx")

    assert output_path.read_bytes() == workbook_bytes


def test_zip_extractor_rejects_archives_without_workbooks(tmp_path):
    archive_path = tmp_path / "no_workbook.zip"

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("readme.txt", "not an Excel file")

    with pytest.raises(RuntimeError, match="does not contain"):
        extract_workbook(archive_path, tmp_path / "retail.xlsx")
