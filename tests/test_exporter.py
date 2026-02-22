# tests/test_exporter.py
import csv
import os
import tempfile
from exporter import append_to_csv, CSV_COLUMNS


def test_append_creates_file_with_headers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        trips = [
            {
                "destination": "CUN",
                "city_name": "Cancun",
                "depart_date": "2026-05-10",
                "return_date": "2026-05-14",
                "trip_days": 4,
                "outbound_price": 327,
                "return_price": 350,
                "total_price": 677,
                "outbound_airline": "United",
                "return_airline": "American",
                "outbound_duration_hrs": 6.5,
                "return_duration_hrs": 5.8,
                "outbound_stops": 1,
                "return_stops": 0,
            }
        ]
        append_to_csv(trips, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["destination"] == "CUN"
        assert rows[0]["total_price"] == "677"
        assert rows[0]["trip_days"] == "4"
    finally:
        os.unlink(path)


def test_append_adds_to_existing_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        trip1 = [{"destination": "CUN", "city_name": "Cancun", "depart_date": "2026-05-10",
                  "return_date": "2026-05-14", "trip_days": 4, "outbound_price": 327,
                  "return_price": 350, "total_price": 677, "outbound_airline": "United",
                  "return_airline": "American", "outbound_duration_hrs": 6.5,
                  "return_duration_hrs": 5.8, "outbound_stops": 1, "return_stops": 0}]
        trip2 = [{"destination": "SJU", "city_name": "San Juan", "depart_date": "2026-05-15",
                  "return_date": "2026-05-18", "trip_days": 3, "outbound_price": 200,
                  "return_price": 180, "total_price": 380, "outbound_airline": "JetBlue",
                  "return_airline": "JetBlue", "outbound_duration_hrs": 3.5,
                  "return_duration_hrs": 3.8, "outbound_stops": 0, "return_stops": 0}]

        append_to_csv(trip1, path)
        append_to_csv(trip2, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
    finally:
        os.unlink(path)


def test_csv_has_round_trip_columns():
    assert "depart_date" in CSV_COLUMNS
    assert "return_date" in CSV_COLUMNS
    assert "trip_days" in CSV_COLUMNS
    assert "total_price" in CSV_COLUMNS
    assert "outbound_airline" in CSV_COLUMNS
    assert "return_airline" in CSV_COLUMNS
