# AA Award Flight Search Agent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python agent that scrapes AA.com for award (miles) flights from Boston to ~25 Caribbean destinations over the next 6 months, uses OpenAI to parse results, and exports the best deals to CSV.

**Architecture:** Construct direct AA award search URLs (bypassing form interaction), load them with Playwright stealth browser, send page HTML to OpenAI GPT-4o-mini for structured data extraction, filter by <10h travel time, and export incrementally to CSV.

**Tech Stack:** Python 3.11+, Playwright + playwright-stealth, OpenAI API (GPT-4o-mini), python-dotenv, pandas

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `.gitignore`

**Step 1: Create requirements.txt**

```
playwright
playwright-stealth
openai
python-dotenv
pandas
```

**Step 2: Create .env file**

```
OPENAI_API_KEY=your_key_here
```

Note: The user already has their key — they will paste it in.

**Step 3: Create .gitignore**

```
.env
__pycache__/
*.pyc
flights_all.csv
flights_filtered.csv
errors.log
progress.json
```

**Step 4: Install dependencies**

Run: `pip install -r requirements.txt`
Run: `playwright install chromium`

**Step 5: Init git and commit**

```bash
git init
git add requirements.txt .gitignore docs/
git commit -m "chore: project setup with dependencies and design docs"
```

---

### Task 2: Config Module

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`

**Step 3: Write the implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config module with destinations, dates, and filters"
```

---

### Task 3: URL Builder

**Files:**
- Create: `url_builder.py`
- Create: `tests/test_url_builder.py`

**Step 1: Write the failing test**

```python
# tests/test_url_builder.py
import json
from urllib.parse import urlparse, parse_qs
from url_builder import build_award_url


def test_build_url_has_correct_base():
    url = build_award_url("BOS", "CUN", "2026-04-15", n_adults=2)
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.hostname == "www.aa.com"
    assert parsed.path == "/booking/search"


def test_build_url_has_award_search_type():
    url = build_award_url("BOS", "CUN", "2026-04-15", n_adults=2)
    params = parse_qs(urlparse(url).query)
    assert params["searchType"] == ["Award"]


def test_build_url_has_correct_pax():
    url = build_award_url("BOS", "CUN", "2026-04-15", n_adults=2)
    params = parse_qs(urlparse(url).query)
    assert params["adult"] == ["2"]
    assert params["pax"] == ["2"]


def test_build_url_has_correct_slice():
    url = build_award_url("BOS", "CUN", "2026-04-15", n_adults=2)
    params = parse_qs(urlparse(url).query)
    slices = json.loads(params["slices"][0])
    assert slices[0]["orig"] == "BOS"
    assert slices[0]["dest"] == "CUN"
    assert slices[0]["date"] == "2026-04-15"


def test_build_url_one_way():
    url = build_award_url("BOS", "SJU", "2026-05-01", n_adults=1)
    params = parse_qs(urlparse(url).query)
    assert params["type"] == ["OneWay"]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_url_builder.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# url_builder.py
import json
from urllib.parse import urlencode


def build_award_url(
    origin: str,
    destination: str,
    depart_date: str,
    n_adults: int = 2,
    n_children: int = 0,
) -> str:
    """Build a direct AA.com award search URL that bypasses the search form."""
    slices = json.dumps(
        [
            {
                "orig": origin,
                "origNearby": True,
                "dest": destination,
                "destNearby": True,
                "date": depart_date,
            }
        ]
    )

    params = {
        "locale": "en_US",
        "pax": n_adults + n_children,
        "adult": n_adults,
        "child": n_children,
        "type": "OneWay",
        "searchType": "Award",
        "cabin": "",
        "carriers": "ALL",
        "slices": slices,
        "maxAwardSegmentAllowed": 2,
    }

    return f"https://www.aa.com/booking/search?{urlencode(params)}"
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_url_builder.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add url_builder.py tests/test_url_builder.py
git commit -m "feat: add URL builder for AA award search URLs"
```

---

### Task 4: Scraper (Playwright Stealth)

**Files:**
- Create: `scraper.py`

**Step 1: Write the scraper**

This module is inherently an integration concern (hits real AA.com), so we skip unit tests and test it manually.

```python
# scraper.py
import random
import time
from playwright.sync_api import sync_playwright, Page, Browser
from playwright_stealth import stealth_sync
from config import SLEEP_MIN_SEC, SLEEP_MAX_SEC


def create_browser() -> tuple:
    """Launch a stealth Playwright browser. Returns (playwright, browser, page)."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": random.randint(1200, 1400), "height": random.randint(800, 1000)},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    stealth_sync(page)
    return pw, browser, page


def close_browser(pw, browser) -> None:
    """Cleanly close browser and playwright."""
    browser.close()
    pw.stop()


def scrape_page(page: Page, url: str) -> str | None:
    """Navigate to URL and return page HTML content, or None on failure."""
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        # Wait for flight results to render
        time.sleep(random.uniform(SLEEP_MIN_SEC, SLEEP_MAX_SEC))
        # Try to wait for results container (adjust selector after inspecting AA.com)
        try:
            page.wait_for_selector("[class*='flight'], [class*='slice'], [class*='result']", timeout=15000)
        except Exception:
            pass  # Page may have loaded but with different structure
        return page.content()
    except Exception as e:
        print(f"  Error loading {url}: {e}")
        return None


def random_delay() -> None:
    """Sleep for a random duration to appear human."""
    time.sleep(random.uniform(SLEEP_MIN_SEC, SLEEP_MAX_SEC))
```

**Step 2: Manual smoke test**

Run: `python -c "from scraper import create_browser, scrape_page, close_browser; from url_builder import build_award_url; pw, br, pg = create_browser(); url = build_award_url('BOS', 'CUN', '2026-04-15'); html = scrape_page(pg, url); print(f'Got {len(html)} chars' if html else 'Failed'); close_browser(pw, br)"`

Expected: A browser window opens, navigates to AA.com, and prints the HTML length.

**Step 3: Commit**

```bash
git add scraper.py
git commit -m "feat: add Playwright stealth scraper for AA.com"
```

---

### Task 5: AI Parser (OpenAI)

**Files:**
- Create: `ai_parser.py`
- Create: `tests/test_ai_parser.py`

**Step 1: Write the failing test**

```python
# tests/test_ai_parser.py
from unittest.mock import patch, MagicMock
from ai_parser import parse_flights_from_html, _build_extraction_prompt


def test_build_extraction_prompt_contains_instructions():
    prompt = _build_extraction_prompt("<html>test</html>")
    assert "miles" in prompt.lower()
    assert "duration" in prompt.lower()
    assert "JSON" in prompt


def test_parse_flights_returns_list():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''[
        {
            "departure_time": "08:00",
            "arrival_time": "13:30",
            "duration_hrs": 5.5,
            "num_stops": 0,
            "miles_cost": 12500,
            "flight_numbers": "AA 1234"
        }
    ]'''

    with patch("ai_parser.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        flights = parse_flights_from_html("<html>flight data</html>")

    assert isinstance(flights, list)
    assert len(flights) == 1
    assert flights[0]["miles_cost"] == 12500
    assert flights[0]["duration_hrs"] == 5.5


def test_parse_flights_handles_empty_response():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "[]"

    with patch("ai_parser.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        flights = parse_flights_from_html("<html>no flights</html>")

    assert flights == []


def test_parse_flights_handles_malformed_json():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "not valid json"

    with patch("ai_parser.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        flights = parse_flights_from_html("<html>bad</html>")

    assert flights == []
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ai_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# ai_parser.py
import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _build_extraction_prompt(html: str) -> str:
    """Build the prompt that instructs GPT to extract flight data from HTML."""
    # Trim HTML to reduce tokens — remove scripts, styles, and compress whitespace
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Truncate to ~100K chars to stay within token limits
    cleaned = cleaned[:100000]

    return f"""Extract all flight options from this American Airlines search results HTML page.

For each flight, return a JSON object with these fields:
- departure_time: string (HH:MM format, e.g. "08:30")
- arrival_time: string (HH:MM format, e.g. "14:45")
- duration_hrs: number (total travel time in decimal hours, e.g. 5.5)
- num_stops: integer (0 for nonstop, 1 for one stop, etc.)
- miles_cost: integer (number of miles required per person, e.g. 12500)
- flight_numbers: string (e.g. "AA 1234" or "AA 1234 / AA 5678")

Return ONLY a JSON array of flight objects. No other text. If there are no flights or the page shows an error, return an empty array [].

HTML content:
{cleaned}"""


def parse_flights_from_html(html: str) -> list[dict]:
    """Send HTML to OpenAI and extract structured flight data."""
    prompt = _build_extraction_prompt(html)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract structured data from HTML. Return only valid JSON arrays."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        # Handle markdown code blocks in response
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except (json.JSONDecodeError, Exception) as e:
        print(f"  AI parser error: {e}")
        return []
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ai_parser.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add ai_parser.py tests/test_ai_parser.py
git commit -m "feat: add OpenAI-powered flight data parser"
```

---

### Task 6: Filter and Rank

**Files:**
- Create: `filter_and_rank.py`
- Create: `tests/test_filter_and_rank.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_filter_and_rank.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# filter_and_rank.py


def filter_flights(flights: list[dict], max_duration_hrs: float = 10.0) -> list[dict]:
    """Remove flights with travel time >= max_duration_hrs."""
    return [f for f in flights if f.get("duration_hrs", float("inf")) < max_duration_hrs]


def rank_by_miles(flights: list[dict]) -> list[dict]:
    """Sort flights by miles cost, lowest first."""
    return sorted(flights, key=lambda f: f.get("miles_cost", float("inf")))
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_filter_and_rank.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add filter_and_rank.py tests/test_filter_and_rank.py
git commit -m "feat: add flight filter and ranking by miles"
```

---

### Task 7: CSV Exporter

**Files:**
- Create: `exporter.py`
- Create: `tests/test_exporter.py`

**Step 1: Write the failing test**

```python
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
                "miles_cost": 12500,
                "flight_numbers": "AA 1234",
            }
        ]
        append_to_csv(flights, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["destination"] == "CUN"
        assert rows[0]["miles_cost"] == "12500"
    finally:
        os.unlink(path)


def test_append_adds_to_existing_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        flight1 = [{"destination": "CUN", "city_name": "Cancun", "date": "2026-04-15",
                     "departure_time": "08:00", "arrival_time": "13:30",
                     "duration_hrs": 5.5, "num_stops": 0, "miles_cost": 12500,
                     "flight_numbers": "AA 1234"}]
        flight2 = [{"destination": "SJU", "city_name": "San Juan", "date": "2026-04-16",
                     "departure_time": "10:00", "arrival_time": "14:00",
                     "duration_hrs": 4.0, "num_stops": 0, "miles_cost": 10000,
                     "flight_numbers": "AA 5678"}]

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
                "arrival_time", "duration_hrs", "num_stops", "miles_cost",
                "flight_numbers"]
    assert CSV_COLUMNS == expected
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_exporter.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_exporter.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add exporter.py tests/test_exporter.py
git commit -m "feat: add incremental CSV exporter"
```

---

### Task 8: Main Orchestrator

**Files:**
- Create: `main.py`

**Step 1: Write the orchestrator**

```python
# main.py
import json
import os
import sys
import time
import random
from datetime import date

from config import (
    ORIGIN, DESTINATIONS, NUM_ADULTS, NUM_CHILDREN,
    MAX_DURATION_HOURS, MAX_RETRIES,
    OUTPUT_FILE_ALL, OUTPUT_FILE_FILTERED, ERRORS_LOG, PROGRESS_FILE,
    generate_dates,
)
from url_builder import build_award_url
from scraper import create_browser, close_browser, scrape_page, random_delay
from ai_parser import parse_flights_from_html
from filter_and_rank import filter_flights, rank_by_miles
from exporter import append_to_csv


def load_progress() -> set:
    """Load set of already-scraped (destination, date) combos."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return set(tuple(x) for x in json.load(f))
    return set()


def save_progress(completed: set) -> None:
    """Save progress to disk."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(completed), f)


def log_error(destination: str, date_str: str, error: str) -> None:
    """Append error to log file."""
    with open(ERRORS_LOG, "a") as f:
        f.write(f"{destination},{date_str},{error}\n")


def main():
    dates = generate_dates()
    completed = load_progress()
    destinations = list(DESTINATIONS.keys())

    total = len(destinations) * len(dates)
    already_done = len(completed)
    remaining = total - already_done

    print(f"AA Award Flight Search Agent")
    print(f"Origin: {ORIGIN}")
    print(f"Destinations: {len(destinations)}")
    print(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"Total searches: {total} | Already done: {already_done} | Remaining: {remaining}")
    print(f"---")

    pw, browser, page = create_browser()
    count = 0

    try:
        for dest_code in destinations:
            city_name = DESTINATIONS[dest_code]
            dest_dates = [d for d in dates if (dest_code, d) not in completed]

            if not dest_dates:
                print(f"[{dest_code}] {city_name} — already complete, skipping")
                continue

            print(f"\n[{dest_code}] {city_name} — {len(dest_dates)} dates to search")

            for i, date_str in enumerate(dest_dates):
                count += 1
                print(f"  {date_str} ({i+1}/{len(dest_dates)}) [overall: {already_done + count}/{total}]", end=" ")

                url = build_award_url(ORIGIN, dest_code, date_str, NUM_ADULTS, NUM_CHILDREN)

                html = None
                for attempt in range(MAX_RETRIES):
                    html = scrape_page(page, url)
                    if html and len(html) > 5000:
                        break
                    if attempt < MAX_RETRIES - 1:
                        wait = random.uniform(5, 15) * (attempt + 1)
                        print(f"retry {attempt+1}...", end=" ")
                        time.sleep(wait)

                if not html or len(html) < 5000:
                    print("FAILED")
                    log_error(dest_code, date_str, "page_load_failed")
                    completed.add((dest_code, date_str))
                    save_progress(completed)
                    continue

                flights = parse_flights_from_html(html)

                if not flights:
                    print(f"no flights found")
                else:
                    # Add destination metadata to each flight
                    for flight in flights:
                        flight["destination"] = dest_code
                        flight["city_name"] = city_name
                        flight["date"] = date_str

                    # Save all flights
                    append_to_csv(flights, OUTPUT_FILE_ALL)

                    # Filter and save filtered flights
                    filtered = filter_flights(flights, MAX_DURATION_HOURS)
                    if filtered:
                        append_to_csv(filtered, OUTPUT_FILE_FILTERED)
                        best = min(filtered, key=lambda f: f.get("miles_cost", float("inf")))
                        print(f"found {len(filtered)} flights, best: {best.get('miles_cost', '?')} miles")
                    else:
                        print(f"found {len(flights)} flights, none under {MAX_DURATION_HOURS}h")

                completed.add((dest_code, date_str))
                save_progress(completed)
                random_delay()

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Progress saved. {len(completed)} searches completed.")
    finally:
        close_browser(pw, browser)

    # Final summary
    print(f"\n{'='*60}")
    print(f"Search complete! {len(completed)} total searches.")
    print(f"All flights: {OUTPUT_FILE_ALL}")
    print(f"Filtered flights (<{MAX_DURATION_HOURS}h): {OUTPUT_FILE_FILTERED}")

    # Sort the filtered file by miles cost
    if os.path.exists(OUTPUT_FILE_FILTERED):
        import pandas as pd
        df = pd.read_csv(OUTPUT_FILE_FILTERED)
        df = df.sort_values("miles_cost")
        df.to_csv(OUTPUT_FILE_FILTERED, index=False)
        print(f"\nTop 10 deals:")
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
```

**Step 2: Manual smoke test with a single destination/date**

Run: `python main.py`

Watch the browser open, navigate to AA.com, and verify:
- The URL loads correctly
- The AI parser extracts flight data
- Results appear in the CSV

If AA blocks the request, we'll see it here and can adjust stealth settings.

**Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add main orchestrator with progress tracking and resume"
```

---

### Task 9: End-to-End Smoke Test

**Step 1: Create a small test config override**

Run a quick test with just 1 destination and 2 dates to verify the full pipeline:

```bash
python -c "
from url_builder import build_award_url
from scraper import create_browser, scrape_page, close_browser
from ai_parser import parse_flights_from_html
from filter_and_rank import filter_flights, rank_by_miles

pw, br, page = create_browser()
url = build_award_url('BOS', 'CUN', '2026-04-15', n_adults=2)
print(f'URL: {url}')

html = scrape_page(page, url)
print(f'HTML length: {len(html) if html else 0}')

if html:
    flights = parse_flights_from_html(html)
    print(f'Flights found: {len(flights)}')
    for f in flights:
        print(f'  {f}')
    filtered = filter_flights(flights, max_duration_hrs=10)
    ranked = rank_by_miles(filtered)
    print(f'After filter (<10h): {len(ranked)}')
    for f in ranked:
        print(f'  {f[\"miles_cost\"]} miles - {f[\"duration_hrs\"]}h - {f[\"flight_numbers\"]}')

close_browser(pw, br)
"
```

**Step 2: Verify CSV output**

Check that `flights_all.csv` and `flights_filtered.csv` are created and contain valid data.

**Step 3: Adjust and fix**

Based on smoke test results:
- If AA blocks: adjust stealth settings, add more delays
- If AI parser returns bad data: refine the prompt
- If selectors/waits need tuning: update scraper.py

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: finalize end-to-end pipeline, ready for use"
```

---

## Running the Agent

```bash
# First time setup
pip install -r requirements.txt
playwright install chromium

# Edit .env with your OpenAI API key
# Then run:
python main.py

# It will resume from where it left off if interrupted.
# Results in flights_filtered.csv, sorted by lowest miles.
```
