# exporter.py
import csv
import os

CSV_COLUMNS = [
    "destination",
    "city_name",
    "date",
    "departure_time",
    "arrival_time",
    "duration_hrs",
    "num_stops",
    "miles_cost",
    "flight_numbers",
]


def append_to_csv(flights: list[dict], filepath: str) -> None:
    """Append flight records to CSV, creating the file with headers if needed."""
    file_exists = os.path.exists(filepath)

    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(flights)
