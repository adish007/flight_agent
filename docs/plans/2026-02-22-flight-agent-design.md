# AA Award Flight Search Agent — Design Document

**Date:** 2026-02-22
**Status:** Approved

## Purpose

Search American Airlines for award (miles) flights from Boston (BOS) to Caribbean destinations. Find the best deals over the next 6 months, filter by travel time < 10 hours, and export results to CSV.

## Requirements

- Search aa.com with miles turned on (award search)
- Origin: BOS (Boston)
- Destinations: ~25 major Caribbean airports
- Date range: next 6 months
- Passengers: 2 adults
- Cabin: Economy only
- Max travel time: 10 hours
- Output: CSV file sorted by lowest miles cost
- No AA login required (guest search)

## Architecture

### Approach: URL Construction + Playwright Stealth + OpenAI Parsing

Inspired by [tszumowski/aa_flight_search_tool](https://github.com/tszumowski/aa_flight_search_tool), we construct direct AA search result URLs with `searchType=Award` baked in, bypassing form interaction entirely.

Instead of brittle CSS selectors (BeautifulSoup), we send page HTML to OpenAI GPT-4o-mini to extract structured flight data. This makes the scraper resilient to AA site redesigns.

### File Structure

```
dad_flight_agent/
  .env                    # OPENAI_API_KEY
  requirements.txt        # Dependencies
  config.py               # Destinations, date range, filters, constants
  url_builder.py          # Constructs AA award search URLs
  scraper.py              # Playwright stealth browser, loads pages
  ai_parser.py            # Sends HTML to OpenAI, returns structured flight JSON
  filter_and_rank.py      # Filters by duration, sorts by miles
  exporter.py             # Writes/appends to CSV
  main.py                 # Orchestrator: progress, resume, error handling
  docs/plans/             # This design doc
```

### Data Flow

1. `config.py` provides list of 25 Caribbean destination codes and generates all dates for next 6 months
2. `url_builder.py` constructs AA award URLs: `https://aa.com/booking/search?searchType=Award&orig=BOS&dest={DST}&date={DATE}&pax=2...`
3. `scraper.py` uses Playwright with stealth plugin to load each URL in a headless browser
4. `ai_parser.py` takes the page HTML, sends it to OpenAI GPT-4o-mini with a structured extraction prompt, returns JSON list of flights
5. `filter_and_rank.py` removes flights with duration >= 10 hours
6. `exporter.py` appends results to CSV incrementally (crash-safe)
7. `main.py` orchestrates the loop, tracks progress, supports resuming from last checkpoint

### Caribbean Destinations (from BOS)

CUN, PUJ, SJU, NAS, MBJ, AUA, STT, STX, GCM, SXM, BGI, POS, SDQ, EIS, UVF, GND, ANU, SKB, TAB, SAL, CUR, BON, DOM, PTP, FDF

### CSV Output Columns

destination, city_name, date, departure_time, arrival_time, duration_hrs, num_stops, miles_cost, flight_numbers

### Anti-Detection Strategy

- Playwright stealth plugin (hides `navigator.webdriver`, spoofs fingerprints)
- Random delays between requests: 3-8 seconds
- Batch by destination (search all dates for one destination before moving on)
- Non-headless mode option for debugging
- Human-like: random viewport sizes, realistic user-agent strings

### Resilience

- Incremental CSV saves after each successful scrape
- Resume support: skip (destination, date) combos already in CSV
- Retry logic: 3 attempts per page with exponential backoff
- Graceful error logging: failed combos logged to `errors.log`

### Cost Estimate

- OpenAI GPT-4o-mini: ~$0.15/1M input tokens
- ~4,500 pages, ~2-5K tokens each = ~10-22M tokens
- Estimated cost: $2-5 total

### Scale

- 25 destinations x ~180 days = ~4,500 searches
- At ~6 seconds average per search = ~7.5 hours for a full run
- Resume support means you can run it over multiple sessions

## Tech Stack

- Python 3.11+
- Playwright + playwright-stealth
- OpenAI API (GPT-4o-mini)
- python-dotenv (for .env)
- pandas (CSV handling)

## Out of Scope

- AA account login
- Round-trip search (one-way only, matching the URL pattern)
- Business/first class
- Email notifications
- Web dashboard
