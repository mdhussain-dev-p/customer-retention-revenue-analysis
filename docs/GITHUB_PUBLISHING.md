# Publishing the project on GitHub

The repository contains the analysis code, SQL, tests, documentation, and
generated example output. The raw Excel workbook and local SQLite database
are excluded by `.gitignore`.

After the project runs locally, review the generated `results/`, `figures/`,
`docs/cleaning_log.md` and `docs/findings.md` files. Then run:

```powershell
git status --short
git add .
git diff --cached --check
git commit -m "Add customer retention and revenue analysis"
git push origin main
```

Before pushing, confirm that `data/raw/online_retail_II.xlsx` and
`data/retail.db` are not listed by `git status`.
