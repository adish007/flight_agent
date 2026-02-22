# exporter.py
import csv
import os

CSV_COLUMNS = [
    "destination",
    "city_name",
    "depart_date",
    "return_date",
    "trip_days",
    "outbound_price",
    "return_price",
    "total_price",
    "outbound_airline",
    "return_airline",
    "outbound_duration_hrs",
    "return_duration_hrs",
    "outbound_stops",
    "return_stops",
]


def append_to_csv(flights: list[dict], filepath: str) -> None:
    """Append flight records to CSV, creating the file with headers if needed."""
    file_exists = os.path.exists(filepath)

    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(flights)
