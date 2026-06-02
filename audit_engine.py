"""
audit_engine.py
---------------
Core auditing logic for the Transport Data Quality Auditor.

Checks performed:
  1. Geocode validation     – lat/lon out of valid range or missing
  2. Duplicate detection    – repeated delivery_id values
  3. Address validation     – too short, placeholder, or blank
  4. Duration outliers      – negative, zero, or > 720 minutes
  5. Status validation      – values outside the approved list
  6. Missing critical fields – driver_id blank/null

Each flagged record includes:
  - Original data
  - error_type  (category of the issue)
  - error_detail (human-readable explanation)
  - severity    (HIGH / MEDIUM / LOW)
"""

import pandas as pd

# ── Config ───────────────────────────────────────────────────────────────────
VALID_STATUSES    = {"DELIVERED", "FAILED", "PENDING", "RETURNED"}
LAT_RANGE         = (-90.0,   90.0)
LON_RANGE         = (-180.0, 180.0)
MIN_DURATION      = 1       # minutes
MAX_DURATION      = 720     # minutes  (12-hour hard cap)
MIN_ADDRESS_LEN   = 8       # characters
PLACEHOLDER_ADDRS = {"n/a", "na", "none", "null", "???", "-"}


# ── Individual check functions ────────────────────────────────────────────────

def check_geocode(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows with invalid or missing latitude / longitude."""
    issues = []

    lat_num = pd.to_numeric(df["latitude"],  errors="coerce")
    lon_num = pd.to_numeric(df["longitude"], errors="coerce")

    missing_mask = lat_num.isna() | lon_num.isna()
    for idx in df[missing_mask].index:
        row = df.loc[idx].to_dict()
        row["error_type"]   = "MISSING_GEOCODE"
        row["error_detail"] = "Latitude or longitude is missing / non-numeric"
        row["severity"]     = "HIGH"
        issues.append(row)

    lat_invalid = (~missing_mask) & ((lat_num < LAT_RANGE[0]) | (lat_num > LAT_RANGE[1]))
    lon_invalid = (~missing_mask) & ((lon_num < LON_RANGE[0]) | (lon_num > LON_RANGE[1]))
    geo_invalid = lat_invalid | lon_invalid
    for idx in df[geo_invalid].index:
        row = df.loc[idx].to_dict()
        row["error_type"]   = "INVALID_GEOCODE"
        row["error_detail"] = (
            f"lat={df.loc[idx,'latitude']} lon={df.loc[idx,'longitude']} "
            f"out of valid range"
        )
        row["severity"] = "HIGH"
        issues.append(row)

    return pd.DataFrame(issues)


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Flag all occurrences of duplicated delivery_id values."""
    dup_mask = df.duplicated(subset="delivery_id", keep=False)
    dupes = df[dup_mask].copy()
    if dupes.empty:
        return pd.DataFrame()
    dupes["error_type"]   = "DUPLICATE_ID"
    dupes["error_detail"] = dupes["delivery_id"].apply(
        lambda d: f"delivery_id '{d}' appears more than once"
    )
    dupes["severity"] = "HIGH"
    return dupes


def check_address(df: pd.DataFrame) -> pd.DataFrame:
    """Flag blank, placeholder, or suspiciously short addresses."""
    addr_col = df["address"].astype(str).str.strip()
    mask = (
        (addr_col == "") |
        (addr_col.str.lower().isin(PLACEHOLDER_ADDRS)) |
        (addr_col.str.len() < MIN_ADDRESS_LEN)
    )
    flagged = df[mask].copy()
    if flagged.empty:
        return pd.DataFrame()
    flagged["error_type"]   = "INVALID_ADDRESS"
    flagged["error_detail"] = addr_col[mask].apply(
        lambda a: f"Address is blank, placeholder, or too short: '{a}'"
    )
    flagged["severity"] = "MEDIUM"
    return flagged


def check_duration(df: pd.DataFrame) -> pd.DataFrame:
    """Flag delivery durations that are negative, zero, or exceed the cap."""
    dur = pd.to_numeric(df["duration_minutes"], errors="coerce")
    mask = dur.isna() | (dur < MIN_DURATION) | (dur > MAX_DURATION)
    flagged = df[mask].copy()
    if flagged.empty:
        return pd.DataFrame()
    flagged["error_type"] = "DURATION_OUTLIER"
    flagged["error_detail"] = dur[mask].apply(
        lambda v: (
            f"Duration {v} min is negative/zero"
            if pd.notna(v) and v <= 0
            else f"Duration {v} min exceeds cap of {MAX_DURATION} min"
            if pd.notna(v)
            else "Duration is missing or non-numeric"
        )
    )
    flagged["severity"] = "MEDIUM"
    return flagged


def check_status(df: pd.DataFrame) -> pd.DataFrame:
    """Flag delivery_status values not in the approved list."""
    mask = ~df["delivery_status"].str.strip().str.upper().isin(VALID_STATUSES)
    flagged = df[mask].copy()
    if flagged.empty:
        return pd.DataFrame()
    flagged["error_type"]   = "INVALID_STATUS"
    flagged["error_detail"] = flagged["delivery_status"].apply(
        lambda s: f"Status '{s}' is not in approved list {sorted(VALID_STATUSES)}"
    )
    flagged["severity"] = "MEDIUM"
    return flagged


def check_missing_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Flag records where driver_id is missing."""
    mask = df["driver_id"].isna() | (df["driver_id"].astype(str).str.strip() == "")
    flagged = df[mask].copy()
    if flagged.empty:
        return pd.DataFrame()
    flagged["error_type"]   = "MISSING_DRIVER_ID"
    flagged["error_detail"] = "driver_id field is blank or missing"
    flagged["severity"]     = "LOW"
    return flagged


# ── Main audit orchestrator ───────────────────────────────────────────────────

def run_audit(df: pd.DataFrame) -> dict:
    """
    Run all checks and return a results dict with:
        summary  – dict of counts per check
        flagged  – combined DataFrame of all flagged rows
        clean    – DataFrame of rows with zero flags
        total    – total input rows
    """
    checks = {
        "geocode_issues":   check_geocode(df),
        "duplicate_ids":    check_duplicates(df),
        "address_issues":   check_address(df),
        "duration_outliers":check_duration(df),
        "status_issues":    check_status(df),
        "missing_fields":   check_missing_fields(df),
    }

    all_flagged_indices = set()
    flagged_frames = []
    summary = {}

    for check_name, result_df in checks.items():
        count = len(result_df)
        summary[check_name] = count
        if count > 0:
            flagged_frames.append(result_df)
            all_flagged_indices.update(result_df.index.tolist())

    if flagged_frames:
        combined = pd.concat(flagged_frames, ignore_index=True)
    else:
        combined = pd.DataFrame()

    clean_df = df[~df.index.isin(all_flagged_indices)].copy()

    total_flagged = len(all_flagged_indices)
    fp_rate = round(total_flagged / len(df) * 100, 2) if len(df) > 0 else 0

    summary["total_records"]    = len(df)
    summary["total_flagged"]    = total_flagged
    summary["clean_records"]    = len(clean_df)
    summary["flag_rate_pct"]    = fp_rate

    return {
        "summary": summary,
        "flagged": combined,
        "clean":   clean_df,
        "total":   len(df),
    }
