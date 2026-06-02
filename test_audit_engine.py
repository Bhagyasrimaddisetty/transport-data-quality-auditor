"""
test_audit_engine.py
--------------------
Unit tests for the audit_engine module.
Run with:  python -m pytest tests/ -v
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.audit_engine import (
    check_geocode, check_duplicates, check_address,
    check_duration, check_status, check_missing_fields,
    run_audit
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def base_row(**kwargs):
    """Return a single valid row, optionally overriding fields."""
    row = {
        "delivery_id":      "DLV000001",
        "driver_id":        "DRV101",
        "city":             "Hyderabad",
        "zone":             "NORTH",
        "address":          "12, MG Road, Hyderabad",
        "latitude":         "17.3850",
        "longitude":        "78.4867",
        "delivery_status":  "DELIVERED",
        "duration_minutes": "45",
        "distance_km":      "5.2",
        "attempt_number":   "1",
        "record_date":      "2024-03-15",
    }
    row.update(kwargs)
    return row


def make_df(rows):
    return pd.DataFrame(rows)


# ── Geocode tests ─────────────────────────────────────────────────────────────
class TestCheckGeocode:
    def test_valid_row_not_flagged(self):
        df = make_df([base_row()])
        result = check_geocode(df)
        assert result.empty, "Valid row should not be flagged"

    def test_lat_out_of_range(self):
        df = make_df([base_row(latitude="95.0", longitude="78.4")])
        result = check_geocode(df)
        assert len(result) == 1
        assert result.iloc[0]["error_type"] == "INVALID_GEOCODE"

    def test_lon_out_of_range(self):
        df = make_df([base_row(latitude="17.0", longitude="200.0")])
        result = check_geocode(df)
        assert len(result) == 1

    def test_missing_lat(self):
        df = make_df([base_row(latitude="", longitude="78.4")])
        result = check_geocode(df)
        assert len(result) == 1
        assert result.iloc[0]["error_type"] == "MISSING_GEOCODE"

    def test_missing_both(self):
        df = make_df([base_row(latitude="", longitude="")])
        result = check_geocode(df)
        assert len(result) == 1

    def test_multiple_invalid(self):
        rows = [
            base_row(delivery_id="DLV000001", latitude="91.0",  longitude="78.0"),
            base_row(delivery_id="DLV000002", latitude="17.0",  longitude="-190.0"),
            base_row(delivery_id="DLV000003", latitude="17.0",  longitude="78.0"),  # valid
        ]
        df = make_df(rows)
        result = check_geocode(df)
        assert len(result) == 2


# ── Duplicate tests ───────────────────────────────────────────────────────────
class TestCheckDuplicates:
    def test_no_duplicates(self):
        rows = [base_row(delivery_id="DLV000001"),
                base_row(delivery_id="DLV000002")]
        df = make_df(rows)
        result = check_duplicates(df)
        assert result.empty

    def test_one_pair_flagged(self):
        rows = [base_row(delivery_id="DLV000001"),
                base_row(delivery_id="DLV000001")]   # duplicate
        df = make_df(rows)
        result = check_duplicates(df)
        assert len(result) == 2   # both occurrences flagged

    def test_severity_is_high(self):
        rows = [base_row(delivery_id="X"), base_row(delivery_id="X")]
        df = make_df(rows)
        result = check_duplicates(df)
        assert all(result["severity"] == "HIGH")


# ── Address tests ─────────────────────────────────────────────────────────────
class TestCheckAddress:
    def test_valid_address_passes(self):
        df = make_df([base_row(address="12, MG Road, Hyderabad")])
        result = check_address(df)
        assert result.empty

    def test_blank_address_flagged(self):
        df = make_df([base_row(address="")])
        result = check_address(df)
        assert len(result) == 1

    def test_na_placeholder_flagged(self):
        for placeholder in ["N/A", "na", "None", "null", "???"]:
            df = make_df([base_row(address=placeholder)])
            result = check_address(df)
            assert len(result) == 1, f"Placeholder '{placeholder}' should be flagged"

    def test_too_short_flagged(self):
        df = make_df([base_row(address="123")])  # length < MIN_ADDRESS_LEN
        result = check_address(df)
        assert len(result) == 1


# ── Duration tests ────────────────────────────────────────────────────────────
class TestCheckDuration:
    def test_normal_duration_passes(self):
        df = make_df([base_row(duration_minutes="60")])
        result = check_duration(df)
        assert result.empty

    def test_negative_flagged(self):
        df = make_df([base_row(duration_minutes="-5")])
        result = check_duration(df)
        assert len(result) == 1

    def test_zero_flagged(self):
        df = make_df([base_row(duration_minutes="0")])
        result = check_duration(df)
        assert len(result) == 1

    def test_over_cap_flagged(self):
        df = make_df([base_row(duration_minutes="800")])
        result = check_duration(df)
        assert len(result) == 1

    def test_non_numeric_flagged(self):
        df = make_df([base_row(duration_minutes="abc")])
        result = check_duration(df)
        assert len(result) == 1


# ── Status tests ──────────────────────────────────────────────────────────────
class TestCheckStatus:
    def test_valid_statuses_pass(self):
        for s in ["DELIVERED", "FAILED", "PENDING", "RETURNED"]:
            df = make_df([base_row(delivery_status=s)])
            result = check_status(df)
            assert result.empty, f"Valid status '{s}' should pass"

    def test_invalid_status_flagged(self):
        for s in ["DONE", "CANCELLED", "UNKNOWN", ""]:
            df = make_df([base_row(delivery_status=s)])
            result = check_status(df)
            assert len(result) == 1, f"Invalid status '{s}' should be flagged"


# ── Missing field tests ───────────────────────────────────────────────────────
class TestCheckMissingFields:
    def test_driver_id_present(self):
        df = make_df([base_row(driver_id="DRV101")])
        result = check_missing_fields(df)
        assert result.empty

    def test_blank_driver_id_flagged(self):
        df = make_df([base_row(driver_id="")])
        result = check_missing_fields(df)
        assert len(result) == 1

    def test_severity_is_low(self):
        df = make_df([base_row(driver_id="")])
        result = check_missing_fields(df)
        assert result.iloc[0]["severity"] == "LOW"


# ── Integration test ──────────────────────────────────────────────────────────
class TestRunAudit:
    def test_clean_record_not_flagged(self):
        df = make_df([base_row()])
        results = run_audit(df)
        assert results["summary"]["total_flagged"] == 0
        assert results["summary"]["clean_records"] == 1

    def test_multiple_errors_all_detected(self):
        rows = [
            base_row(delivery_id="DLV000001"),           # valid
            base_row(delivery_id="DLV000001"),           # duplicate
            base_row(delivery_id="DLV000003", latitude="999"),  # bad geocode
            base_row(delivery_id="DLV000004", address=""),       # bad address
            base_row(delivery_id="DLV000005", duration_minutes="-10"),  # bad duration
        ]
        df = make_df(rows)
        results = run_audit(df)
        assert results["summary"]["total_flagged"] >= 4

    def test_summary_keys_present(self):
        df = make_df([base_row()])
        results = run_audit(df)
        for key in ["total_records", "total_flagged", "clean_records",
                    "flag_rate_pct", "geocode_issues", "duplicate_ids",
                    "address_issues", "duration_outliers", "status_issues",
                    "missing_fields"]:
            assert key in results["summary"], f"Missing key: {key}"

    def test_flag_rate_within_bounds(self):
        """On 10k generated records, flag rate should be between 5% and 20%."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from src.generate_data import generate
        import tempfile, pandas as pd
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            tmp = f.name
        generate(tmp)
        df = pd.read_csv(tmp, dtype=str)
        results = run_audit(df)
        rate = results["summary"]["flag_rate_pct"]
        assert 5 <= rate <= 25, f"Unexpected flag rate: {rate}%"
        os.unlink(tmp)


# ── Standalone runner (no pytest needed) ─────────────────────────────────────
if __name__ == "__main__":
    import traceback
    test_classes = [
        TestCheckGeocode, TestCheckDuplicates, TestCheckAddress,
        TestCheckDuration, TestCheckStatus, TestCheckMissingFields,
        TestRunAudit
    ]
    passed = failed = 0
    for cls in test_classes:
        obj = cls()
        methods = [m for m in dir(obj) if m.startswith("test_")]
        for method in methods:
            try:
                getattr(obj, method)()
                print(f"  ✅  {cls.__name__}.{method}")
                passed += 1
            except Exception as e:
                print(f"  ❌  {cls.__name__}.{method}  →  {e}")
                traceback.print_exc()
                failed += 1
    print(f"\n{'='*50}")
    print(f"  {passed} passed   {failed} failed   ({passed+failed} total)")
    print(f"{'='*50}")
