"""
main.py
-------
Entry point for the Transport Data Quality Auditor.

Usage:
    # Generate fresh data, run audit, produce Excel report
    python main.py

    # Use an existing CSV instead of generating new data
    python main.py --input data/my_records.csv

    # Change output report path
    python main.py --output reports/my_report.xlsx

Pipeline:
    1. Generate (or load) delivery records  ->  data/delivery_records.csv
    2. Run audit_engine checks              ->  flagged + clean DataFrames
    3. Print summary to terminal
    4. Write Excel report                   ->  reports/audit_report.xlsx
"""

import argparse
import sys
import os
import pandas as pd

# Make sure src/ is importable regardless of where Python is run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.generate_data    import generate
from src.audit_engine     import run_audit
from src.report_generator import generate_report


def print_summary(summary):
    print("\n" + "=" * 55)
    print("  TRANSPORT DATA QUALITY AUDIT - RESULTS SUMMARY")
    print("=" * 55)
    print("  Total records      : {:,}".format(summary['total_records']))
    print("  Flagged records    : {:,}  ({}%)".format(summary['total_flagged'], summary['flag_rate_pct']))
    print("  Clean records      : {:,}".format(summary['clean_records']))
    print("-" * 55)
    checks = [
        ("Geocode Issues",    "geocode_issues"),
        ("Duplicate IDs",     "duplicate_ids"),
        ("Address Issues",    "address_issues"),
        ("Duration Outliers", "duration_outliers"),
        ("Status Issues",     "status_issues"),
        ("Missing Fields",    "missing_fields"),
    ]
    for label, key in checks:
        val = summary.get(key, 0)
        bar = "#" * min(val // 10, 30)
        print("  {:<22}: {:>4}  {}".format(label, val, bar))
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Transport Data Quality Auditor")
    parser.add_argument("--input",  default=None,
        help="Path to input CSV. If omitted, fresh data is generated.")
    parser.add_argument("--output", default="reports/audit_report.xlsx",
        help="Path for the Excel audit report.")
    args = parser.parse_args()

    # Step 1: Data
    data_path = args.input if args.input else "data/delivery_records.csv"
    if args.input is None:
        print("[main] Generating simulated delivery records...")
        generate(data_path)
    else:
        if not os.path.exists(data_path):
            print("[main] ERROR: Input file not found: {}".format(data_path))
            sys.exit(1)
        print("[main] Loading records from {}...".format(data_path))

    df = pd.read_csv(data_path, dtype=str)
    print("[main] Loaded {:,} records.".format(len(df)))

    # Step 2: Audit
    print("[main] Running audit checks...")
    results = run_audit(df)

    # Step 3: Terminal summary
    print_summary(results["summary"])

    # Step 4: Excel report
    print("[main] Generating Excel report...")
    report_path = generate_report(results, args.output)
    print("[main] Done. Report: {}\n".format(report_path))


if __name__ == "__main__":
    main()
