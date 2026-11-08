from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT_ROOT / "data" / "raw"
DOWNLOAD_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
ZIP_PATH = RAW_FOLDER / "online_retail_ii.zip"
WORKBOOK_PATH = RAW_FOLDER / "online_retail_II.xlsx"


def extract_workbook(zip_path: str | Path, workbook_path: str | Path) -> Path:
    zip_path = Path(zip_path)
    workbook_path = Path(workbook_path)
    workbook_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        members = [
            member for member in archive.namelist()
            if member.lower().endswith(".xlsx")
        ]
        if not members:
            raise RuntimeError("The UCI archive does not contain an Excel workbook.")

        with archive.open(members[0]) as source, workbook_path.open("wb") as target:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                target.write(block)

    return workbook_path


def download_workbook() -> Path:
    RAW_FOLDER.mkdir(parents=True, exist_ok=True)
    if WORKBOOK_PATH.exists():
        print(f"Dataset already exists: {WORKBOOK_PATH}")
        return WORKBOOK_PATH

    print("Downloading Online Retail II from the UCI Machine Learning Repository...")
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "CustomerRetentionAnalysis/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with ZIP_PATH.open("wb") as output:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                output.write(block)

    result = extract_workbook(ZIP_PATH, WORKBOOK_PATH)
    ZIP_PATH.unlink(missing_ok=True)
    return result


def main() -> None:
    workbook_path = download_workbook()
    print(f"Dataset saved to: {workbook_path}")


if __name__ == "__main__":
    main()
