# 🚛 Transport Data Quality Auditor

A production-style Python pipeline for auditing last-mile delivery records for data quality issues. The tool flags outliers and exceptions across multiple quality dimensions and generates a structured, multi-sheet Excel report with summary charts.

---

## 📌 Project Highlights

- Dataset size: 10,000 simulated delivery records
- Checks performed: 6 quality dimensions
- Typical flag rate: ~10–12% of records
- Output: Multi-sheet Excel report with charts (XLSX)
- Test coverage: 20+ unit tests across modules

---

## Key Features

- Validates geolocation, addresses, and status values
- Detects duplicate delivery IDs and missing required fields
- Flags duration outliers and other anomalies
- Produces a readable Excel report with separate sheets by severity and a dashboard
- Includes unit tests and example data generation for quick evaluation

---

## 🗂️ Repository Structure

transport-data-quality-auditor/

├── main.py                  # Entry point — runs full pipeline
├── generate_data.py         # Generates 10,000 simulated delivery records
├── audit_engine.py          # Core quality checks (6 dimensions)
├── report_generator.py      # Writes formatted multi-sheet Excel report
├── test_audit_engine.py     # 20+ unit tests (pytest)
├── requirements.txt
└── .gitignore

---

## ✅ Quality Checks (summary)

| Check | Severity | What it looks for |
|-------|----------|-------------------|
| Geocode Validation | HIGH | Latitude/longitude out of valid range or missing |
| Duplicate Detection | HIGH | Repeated delivery_id values |
| Address Validation | MEDIUM | Blank, placeholder (N/A, null), or too short |
| Duration Outliers | MEDIUM | Negative, zero, or > 720 minutes |
| Status Validation | MEDIUM | Values outside {DELIVERED, FAILED, PENDING, RETURNED} |
| Missing Fields | LOW | driver_id blank or missing |

---

## 🚀 Getting Started

1. Clone the repository

```bash
git clone https://github.com/Bhagyasrimaddisetty/transport-data-quality-auditor.git
cd transport-data-quality-auditor
```

2. (Optional) Create a virtual environment and activate it

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
.\.venv\Scripts\activate   # Windows (PowerShell)
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run the full pipeline (uses generated sample data by default)

```bash
python main.py
```

5. Use your own data

```bash
python main.py --input data/your_file.csv --output reports/your_report.xlsx
```

Notes:
- Input file must be a CSV with the expected delivery columns (delivery_id, latitude, longitude, address, duration_minutes, status, driver_id, city, etc.).
- The pipeline writes a multi-sheet Excel report to the path provided by --output (default: reports/audit_report.xlsx).

---

## 📊 Sample Terminal Output

```
=======================================================
TRANSPORT DATA QUALITY AUDIT — RESULTS SUMMARY

Total records      : 10,000
Flagged records    : 1,047  (10.47%)
Clean records      : 8,953

Geocode Issues      :  412
Duplicate IDs       :   98
Address Issues      :  201
Duration Outliers   :  156
Status Issues       :  148
Missing Fields      :  100
=======================================================
```

---

## 📂 Excel Report Sheets

The generated `audit_report.xlsx` contains these sheets:

1. Summary Dashboard — KPI blocks and a bar chart of issues by category
2. All Flagged Records — every flagged row with error_type, error_detail, severity
3. HIGH Severity — geocode and duplicate issues
4. MEDIUM Severity — address, duration, and status issues
5. LOW Severity — missing field issues
6. Clean Records (Sample) — first 2,000 records that passed all checks
7. City Breakdown — pivot table of flag counts per city

---

## 🧪 Running Tests

Install pytest if not already installed and run the test suite:

```bash
pip install pytest
python -m pytest test_audit_engine.py -v
```

---

## 🔧 Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.7+ | Core language |
| pandas | Data ingestion, transformation, filtering |
| openpyxl | Excel report generation with charts |
| pytest | Unit testing |

---

## Contributing

Contributions are welcome. If you find bugs or want to add checks, please fork the repository, create a feature branch, add tests, and open a pull request.

Suggested steps:
- Fork → create branch → add tests → run pytest → open PR

---

## License

This project is available under the MIT License. See LICENSE for details (add a LICENSE file if one does not exist).

---

## 👤 Author

**Maddisetty Bhagya Sri**  
B.Tech CSE (AI/ML) — Mohan Babu University  
[LinkedIn](https://www.linkedin.com/in/bhagya-sri-maddisetty-064102305/) | [GitHub](https://github.com/Bhagyasrimaddisetty)
