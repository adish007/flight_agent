# config.py
from datetime import date, timedelta

ORIGIN = "BOS"

DESTINATIONS = {
    "CUN": "Cancun",
    "PUJ": "Punta Cana",
    "SJU": "San Juan",
    "NAS": "Nassau",
    "MBJ": "Montego Bay",
    "AUA": "Aruba",
    "STT": "St. Thomas",
    "STX": "St. Croix",
    "GCM": "Grand Cayman",
    "SXM": "St. Maarten",
    "BGI": "Barbados",
    "POS": "Trinidad",
    "SDQ": "Santo Domingo",
    "EIS": "Tortola",
    "UVF": "St. Lucia",
    "GND": "Grenada",
    "ANU": "Antigua",
    "SKB": "St. Kitts",
    "TAB": "Tobago",
    "SAL": "El Salvador",
    "CUR": "Curacao",
    "BON": "Bonaire",
    "DOM": "Dominica",
    "PTP": "Guadeloupe",
    "FDF": "Martinique",
}

NUM_ADULTS = 2
NUM_CHILDREN = 0
MAX_DURATION_HOURS = 10
CABIN = "ECONOMY"

# Scraper settings
SLEEP_MIN_SEC = 3
SLEEP_MAX_SEC = 8
MAX_RETRIES = 3

# Output files
OUTPUT_FILE_ALL = "flights_all.csv"
OUTPUT_FILE_FILTERED = "flights_filtered.csv"
ERRORS_LOG = "errors.log"
PROGRESS_FILE = "progress.json"


def generate_dates(start: date = None, end: date = None) -> list[str]:
    """Generate list of date strings YYYY-MM-DD for the search range."""
    if start is None:
        start = date.today() + timedelta(days=1)
    if end is None:
        end = start + timedelta(days=180)
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates
