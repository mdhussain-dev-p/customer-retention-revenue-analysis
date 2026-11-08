# Start here

The source code and analysis workflow are ready. The original UCI workbook is
downloaded separately because it is large and should not be committed to GitHub.

Open this folder in VS Code, open a PowerShell terminal at the project root,
and run these commands in order:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python scripts/download_data.py
python scripts/run_project.py
python -m pytest
```

The first download is approximately 43.5 MB. The importer reads the Excel
workbook in batches and writes the source rows into SQLite.

The first full run creates `data/retail.db`. Later runs reuse that database.
To rebuild it from the original workbook, run:

```powershell
python scripts/run_project.py --reload
```

After the analysis finishes, look in:

- `results/` for CSV tables and generated analysis notes.
- `figures/` for revenue, cohort, RFM and Pareto charts.
- `docs/cleaning_log.md` for row counts and cleaning decisions.
- `docs/findings.md` for five findings and the limitations.
- `logs/project_run.log` for the latest run summary.

The raw workbook and SQLite database are local files and are intentionally
ignored by Git.
