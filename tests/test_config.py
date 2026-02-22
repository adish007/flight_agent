# tests/test_config.py
from datetime import date, timedelta
from config import DESTINATIONS, ORIGIN, generate_dates, MAX_DURATION_HOURS, NUM_ADULTS


def test_origin_is_bos():
    assert ORIGIN == "BOS"


def test_destinations_contains_known_airports():
    assert "CUN" in DESTINATIONS
    assert "SJU" in DESTINATIONS
    assert "PUJ" in DESTINATIONS
    assert len(DESTINATIONS) >= 20


def test_generate_dates_returns_correct_range():
    start = date(2026, 3, 1)
    end = date(2026, 3, 5)
    dates = generate_dates(start, end)
    assert dates == [
        "2026-03-01",
        "2026-03-02",
        "2026-03-03",
        "2026-03-04",
        "2026-03-05",
    ]


def test_generate_dates_default_is_6_months():
    dates = generate_dates()
    assert len(dates) > 150
    assert len(dates) <= 185


def test_max_duration_is_10_hours():
    assert MAX_DURATION_HOURS == 10


def test_num_adults_is_2():
    assert NUM_ADULTS == 2
