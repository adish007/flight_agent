# tests/test_config.py
from datetime import date
from config import DESTINATIONS, ORIGIN, generate_dates, MAX_DURATION_HOURS, NUM_ADULTS, TRIP_LENGTHS


def test_origin_is_bos():
    assert ORIGIN == "BOS"


def test_destinations_contains_known_airports():
    assert "CUN" in DESTINATIONS
    assert "SJU" in DESTINATIONS
    assert "PUJ" in DESTINATIONS
    assert len(DESTINATIONS) == 10


def test_generate_dates_returns_may():
    dates = generate_dates()
    assert dates[0] == "2026-05-01"
    assert dates[-1] == "2026-05-31"
    assert len(dates) == 31


def test_generate_dates_custom_range():
    start = date(2026, 3, 1)
    end = date(2026, 3, 5)
    dates = generate_dates(start, end)
    assert dates == ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05"]


def test_max_duration_is_10_hours():
    assert MAX_DURATION_HOURS == 10


def test_num_adults_is_2():
    assert NUM_ADULTS == 2


def test_trip_lengths():
    assert TRIP_LENGTHS == [3, 4, 5, 6]
