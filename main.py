# main.py
import json
import os
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
