# tests/test_exporter.py
import csv
import os
import tempfile
from exporter import append_to_csv, CSV_COLUMNS


def test_append_creates_file_with_headers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    os.unlink(path)  # ensure it doesn't exist

    try:
        flights = [
            {
                "destination": "CUN",
                "city_name": "Cancun",
                "date": "2026-04-15",
                "departure_time": "08:00",
                "arrival_time": "13:30",
                "duration_hrs": 5.5,
                "num_stops": 0,
                "price": 327,
                "flight_numbers": "American",
            }
        ]
        append_to_csv(flights, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["destination"] == "CUN"
        assert rows[0]["price"] == "327"
    finally:
        os.unlink(path)


def test_append_adds_to_existing_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        flight1 = [{"destination": "CUN", "city_name": "Cancun", "date": "2026-04-15",
                     "departure_time": "08:00", "arrival_time": "13:30",
                     "duration_hrs": 5.5, "num_stops": 0, "price": 327,
                     "flight_numbers": "American"}]
        flight2 = [{"destination": "SJU", "city_name": "San Juan", "date": "2026-04-16",
                     "departure_time": "10:00", "arrival_time": "14:00",
                     "duration_hrs": 4.0, "num_stops": 0, "price": 200,
                     "flight_numbers": "JetBlue"}]

        append_to_csv(flight1, path)
        append_to_csv(flight2, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
    finally:
        os.unlink(path)


def test_csv_columns_match_expected():
    expected = ["destination", "city_name", "date", "departure_time",
                "arrival_time", "duration_hrs", "num_stops", "price",
                "flight_numbers"]
    assert CSV_COLUMNS == expected
