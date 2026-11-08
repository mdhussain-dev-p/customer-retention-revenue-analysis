# Customer Retention and Revenue Analysis

## What this project looks at

This project uses transaction records from a UK online retailer to answer
three practical questions:

- Where does the retailer's product revenue come from?
- How many identified customers return after their first purchase?
- Which customer groups may deserve attention?

The analysis uses monthly revenue reporting, customer cohort retention, RFM
segmentation and revenue concentration. It finishes with a small, clearly
labelled reactivation scenario.

## Dataset

The project uses the UCI Machine Learning Repository's **Online Retail II**
dataset. The original workbook contains 1,067,371 transactions from
1 December 2009 to 9 December 2011.

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
Creator: Daqing Chen
DOI: https://doi.org/10.24432/C5CG6D
Licence: CC BY 4.0

The raw workbook is not committed to GitHub. Download it directly from UCI:

```powershell
python scripts/download_data.py
```

The download script places the Excel workbook in `data/raw/`. The project then
loads it into a local SQLite database in batches. Neither the raw workbook nor
the SQLite database is committed to the repository.

## Run the project

Python 3.13.7 is the pinned project version.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python scripts/download_data.py
python scripts/run_project.py
```

Run the tests with:

```powershell
python -m pytest
```

## What the analysis produces

- Monthly net product revenue, completed orders and active customers.
- Cohort retention rates and a retention heatmap.
- Customer-level Recency, Frequency and Monetary scores.
- Reproducible customer segments with explicit rules.
- Customer and product revenue concentration.
- A hypothetical 5% reactivation scenario for the At risk segment.
- A row-by-row cleaning log and five evidence-based findings.

## Cleaning decisions

Guest purchases remain in revenue summaries but are excluded from cohort and
RFM analysis. Cancellation invoices are preserved as negative adjustments and
are not counted as completed orders. Non-product codes remain in the cleaned
audit data but are excluded from product analysis.

Non-positive or missing prices, exact duplicate transaction rows and
unparseable invoice dates are removed from the analysis-ready table. The
measured effect of each rule is written to `results/cleaning_counts.csv` and
explained in `docs/cleaning_log.md`.

## Project layout

```text
customer-retention-revenue-analysis/
├── data/
│   └── raw/
│       └── README.md
├── docs/
│   ├── DATASET_SOURCE.md
│   ├── GITHUB_PUBLISHING.md
│   ├── METHODOLOGY.md
│   ├── cleaning_log.md
│   ├── findings.md
│   └── limitations.md
├── figures/
│   └── README.md
├── logs/
│   └── README.md
├── results/
│   └── README.md
├── scripts/
│   ├── download_data.py
│   └── run_project.py
├── sql/
│   ├── 01_clean.sql
│   ├── 02_monthly.sql
│   ├── 03_cohorts.sql
│   └── 04_rfm.sql
├── src/
│   ├── __init__.py
│   ├── clean.py
│   ├── cohorts.py
│   ├── concentration.py
│   ├── load.py
│   ├── rfm.py
│   └── run_analysis.py
├── tests/
│   ├── test_clean.py
│   ├── test_cohorts.py
│   ├── test_concentration.py
│   ├── test_database.py
│   ├── test_download_data.py
│   ├── test_end_to_end.py
│   └── test_rfm.py
├── .gitignore
├── .python-version
├── LICENSE
├── pytest.ini
├── requirements.lock
├── requirements.txt
├── README.md
└── START_HERE.md
```
For the detailed decisions, see `docs/METHODOLOGY.md`,
`docs/cleaning_log.md`, `docs/findings.md`.
