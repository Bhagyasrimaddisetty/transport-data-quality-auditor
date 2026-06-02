"""
generate_data.py
----------------
Generates a realistic simulated dataset of last-mile delivery records
for the Transport Data Quality Auditor project.

Intentionally injects:
  - Missing values
  - Invalid geocoordinates (out-of-range lat/lon)
  - Duplicate delivery IDs
  - Address format errors
  - Unrealistic delivery durations
  - Invalid status codes

Run:
    python src/generate_data.py
Output:
    data/delivery_records.csv
"""

import csv
import random
import os

random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────
NUM_RECORDS = 10_000

CITIES = [
    ("Hyderabad", 17.3850, 78.4867),
    ("Bangalore", 12.9716, 77.5946),
    ("Chennai",   13.0827, 80.2707),
    ("Mumbai",    19.0760, 72.8777),
    ("Pune",      18.5204, 73.8567),
    ("Delhi",     28.6139, 77.2090),
]

VALID_STATUSES   = ["DELIVERED", "FAILED", "PENDING", "RETURNED"]
INVALID_STATUSES = ["DONE", "CANCELLED", "UNKNOWN", ""]   # injected errors

ZONES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

# ── Helpers ──────────────────────────────────────────────────────────────────
def jitter(val, spread=0.05):
    return round(val + random.uniform(-spread, spread), 6)

def random_address():
    streets = ["MG Road", "Brigade Road", "Jubilee Hills", "Banjara Hills",
               "Anna Nagar", "Koramangala", "Indiranagar", "Madhapur",
               "Gachibowli", "Whitefield"]
    return f"{random.randint(1, 999)}, {random.choice(streets)}"

def make_record(i, inject_error):
    city_name, base_lat, base_lon = random.choice(CITIES)
    delivery_id = f"DLV{str(i).zfill(6)}"

    # Duplicate IDs (~1% of records)
    if inject_error == "duplicate":
        delivery_id = f"DLV{str(random.randint(1, i - 1)).zfill(6)}"

    # Geocoord errors (~3%)
    if inject_error == "geocode":
        lat = round(random.uniform(91, 180), 6)   # invalid latitude
        lon = round(random.uniform(181, 360), 6)  # invalid longitude
    else:
        lat = jitter(base_lat)
        lon = jitter(base_lon)

    # Missing lat/lon (~1%)
    if inject_error == "missing_geo":
        lat, lon = "", ""

    # Address errors (~2%)
    address = random_address() + f", {city_name}"
    if inject_error == "address":
        address = random.choice(["", "N/A", "123", "????", address[:3]])

    # Duration errors — negative or >720 minutes (~1.5%)
    duration = random.randint(15, 180)
    if inject_error == "duration":
        duration = random.choice([-10, -1, 0, 800, 1440])

    # Status errors (~1.5%)
    status = random.choice(VALID_STATUSES)
    if inject_error == "status":
        status = random.choice(INVALID_STATUSES)

    # Missing fields (~1%)
    driver_id = f"DRV{random.randint(100, 999)}"
    if inject_error == "missing_field":
        driver_id = ""

    return {
        "delivery_id":       delivery_id,
        "driver_id":         driver_id,
        "city":              city_name,
        "zone":              random.choice(ZONES),
        "address":           address,
        "latitude":          lat,
        "longitude":         lon,
        "delivery_status":   status,
        "duration_minutes":  duration,
        "distance_km":       round(random.uniform(0.5, 25.0), 2),
        "attempt_number":    random.randint(1, 3),
        "record_date":       f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
    }

def decide_error(i):
    r = random.random()
    if r < 0.010: return "duplicate"
    if r < 0.040: return "geocode"
    if r < 0.050: return "missing_geo"
    if r < 0.070: return "address"
    if r < 0.085: return "duration"
    if r < 0.100: return "status"
    if r < 0.110: return "missing_field"
    return None

# ── Main ─────────────────────────────────────────────────────────────────────
def generate(output_path="data/delivery_records.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    records = []
    for i in range(1, NUM_RECORDS + 1):
        error_type = decide_error(i)
        records.append(make_record(i, error_type))

    fieldnames = records[0].keys()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[generate_data] {NUM_RECORDS} records written to {output_path}")

if __name__ == "__main__":
    generate()
