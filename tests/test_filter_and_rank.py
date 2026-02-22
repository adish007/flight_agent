# tests/test_filter_and_rank.py
from filter_and_rank import filter_flights, rank_by_price


def test_filter_removes_long_flights():
    flights = [
        {"duration_hrs": 5.0, "price": 327},
        {"duration_hrs": 11.0, "price": 200},
        {"duration_hrs": 9.5, "price": 500},
    ]
    result = filter_flights(flights, max_duration_hrs=10)
    assert len(result) == 2
    assert all(f["duration_hrs"] < 10 for f in result)


def test_filter_keeps_exactly_at_limit():
    flights = [{"duration_hrs": 10.0, "price": 327}]
    result = filter_flights(flights, max_duration_hrs=10)
    assert len(result) == 0  # strictly less than 10


def test_rank_by_price_sorts_ascending():
    flights = [
        {"price": 500, "duration_hrs": 5.0},
        {"price": 200, "duration_hrs": 6.0},
        {"price": 350, "duration_hrs": 4.0},
    ]
    result = rank_by_price(flights)
    assert result[0]["price"] == 200
    assert result[1]["price"] == 350
    assert result[2]["price"] == 500


def test_filter_empty_list():
    assert filter_flights([], max_duration_hrs=10) == []


def test_rank_empty_list():
    assert rank_by_price([]) == []
