# config.py
from datetime import date, timedelta

ORIGIN = "BOS"

# Top 10 Caribbean destinations from Boston
DESTINATIONS = {
    "CUN": "Cancun",
    "PUJ": "Punta Cana",
    "SJU": "San Juan",
    "NAS": "Nassau",
    "MBJ": "Montego Bay",
    "AUA": "Aruba",
    "STT": "St. Thomas",
    "GCM": "Grand Cayman",
    "SXM": "St. Maarten",
    "SDQ": "Santo Domingo",
}

NUM_ADULTS = 2
NUM_CHILDREN = 0
MAX_DURATION_HOURS = 10

# Trip lengths to search (days)
TRIP_LENGTHS = [3, 4, 5, 6]

# Parallel search settings
MAX_WORKERS = 3  # concurrent searches (be gentle on Google)

# Scraper settings
SLEEP_MIN_SEC = 1
SLEEP_MAX_SEC = 3
MAX_RETRIES = 3


def generate_dates(start: date = None, end: date = None) -> list[str]:
    """Generate list of date strings YYYY-MM-DD for the search range."""
    if start is None:
        start = date(2026, 5, 1)
    if end is None:
        end = date(2026, 5, 31)
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates
