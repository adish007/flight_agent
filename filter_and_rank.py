# filter_and_rank.py


def filter_flights(flights: list[dict], max_duration_hrs: float = 10.0) -> list[dict]:
    """Remove flights with travel time >= max_duration_hrs."""
    return [f for f in flights if f.get("duration_hrs", float("inf")) < max_duration_hrs]


def rank_by_miles(flights: list[dict]) -> list[dict]:
    """Sort flights by miles cost, lowest first."""
    return sorted(flights, key=lambda f: f.get("miles_cost", float("inf")))
