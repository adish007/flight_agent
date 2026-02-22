# tests/test_filter_and_rank.py
from filter_and_rank import filter_flights, rank_by_miles


def test_filter_removes_long_flights():
    flights = [
        {"duration_hrs": 5.0, "miles_cost": 12500},
        {"duration_hrs": 11.0, "miles_cost": 10000},
        {"duration_hrs": 9.5, "miles_cost": 15000},
    ]
    result = filter_flights(flights, max_duration_hrs=10)
    assert len(result) == 2
    assert all(f["duration_hrs"] < 10 for f in result)


def test_filter_keeps_exactly_at_limit():
    flights = [{"duration_hrs": 10.0, "miles_cost": 12500}]
    result = filter_flights(flights, max_duration_hrs=10)
    assert len(result) == 0  # strictly less than 10


def test_rank_by_miles_sorts_ascending():
    flights = [
        {"miles_cost": 25000, "duration_hrs": 5.0},
        {"miles_cost": 12500, "duration_hrs": 6.0},
        {"miles_cost": 17500, "duration_hrs": 4.0},
    ]
    result = rank_by_miles(flights)
    assert result[0]["miles_cost"] == 12500
    assert result[1]["miles_cost"] == 17500
    assert result[2]["miles_cost"] == 25000


def test_filter_empty_list():
    assert filter_flights([], max_duration_hrs=10) == []


def test_rank_empty_list():
    assert rank_by_miles([]) == []
