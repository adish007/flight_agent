# main.py
import json
import os
import time
import random
import re

from config import (
    ORIGIN,
    DESTINATIONS,
    NUM_ADULTS,
    MAX_DURATION_HOURS,
    MAX_RETRIES,
    OUTPUT_FILE_ALL,
    OUTPUT_FILE_FILTERED,
    ERRORS_LOG,
    PROGRESS_FILE,
    generate_dates,
)
from scraper import search_flights, random_delay
from filter_and_rank import filter_flights
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


def parse_duration_hrs(duration_str: str) -> float | None:
    """Parse duration string like '6 hr 25 min' to decimal hours."""
    if not duration_str:
        return None
    match = re.search(r"(\d+)\s*hr", duration_str)
    hours = int(match.group(1)) if match else 0
    match = re.search(r"(\d+)\s*min", duration_str)
    minutes = int(match.group(1)) if match else 0
    return hours + minutes / 60


def parse_price(price_str: str) -> int | None:
    """Parse price string like '$507' to integer cents."""
    if not price_str:
        return None
    match = re.search(r"\$?([\d,]+)", price_str)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def parse_stops(stops_val) -> int:
    """Parse stops value (str or int) to integer."""
    if isinstance(stops_val, int):
        return stops_val
    if not stops_val or stops_val == "Unknown":
        return -1
    if "nonstop" in str(stops_val).lower():
        return 0
    match = re.search(r"(\d+)", str(stops_val))
    return int(match.group(1)) if match else -1


def main():
    dates = generate_dates()
    completed = load_progress()
    destinations = list(DESTINATIONS.keys())

    total = len(destinations) * len(dates)
    already_done = len(completed)
    remaining = total - already_done

    print("Caribbean Flight Search Agent (via Google Flights)")
    print(f"Origin: {ORIGIN}")
    print(f"Destinations: {len(destinations)}")
    print(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"Total searches: {total} | Already done: {already_done} | Remaining: {remaining}")
    print("---")

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
                print(
                    f"  {date_str} ({i+1}/{len(dest_dates)}) "
                    f"[overall: {already_done + count}/{total}]",
                    end=" ",
                )

                flights_raw = None
                for attempt in range(MAX_RETRIES):
                    flights_raw = search_flights(
                        ORIGIN, dest_code, date_str, NUM_ADULTS, max_stops=1
                    )
                    if flights_raw:
                        break
                    if attempt < MAX_RETRIES - 1:
                        wait = random.uniform(3, 8) * (attempt + 1)
                        print(f"retry {attempt+1}...", end=" ")
                        time.sleep(wait)

                if not flights_raw:
                    print("no flights")
                    completed.add((dest_code, date_str))
                    save_progress(completed)
                    random_delay()
                    continue

                # Convert all flights to our CSV format
                csv_flights = []
                for f in flights_raw:
                    duration_hrs = parse_duration_hrs(f.get("duration", ""))
                    price = parse_price(f.get("price", ""))
                    csv_flights.append(
                        {
                            "destination": dest_code,
                            "city_name": city_name,
                            "date": date_str,
                            "departure_time": f.get("departure_time", ""),
                            "arrival_time": f.get("arrival_time", ""),
                            "duration_hrs": round(duration_hrs, 2) if duration_hrs else "",
                            "num_stops": parse_stops(f.get("stops", "")),
                            "price": price if price else "",
                            "flight_numbers": f.get("airline", ""),
                        }
                    )

                # Save all flights
                append_to_csv(csv_flights, OUTPUT_FILE_ALL)

                # Filter by duration and save
                filterable = [f for f in csv_flights if f["duration_hrs"] != ""]
                filtered = filter_flights(filterable, MAX_DURATION_HOURS)
                if filtered:
                    append_to_csv(filtered, OUTPUT_FILE_FILTERED)
                    best = min(
                        filtered,
                        key=lambda f: f.get("price", float("inf"))
                        if f.get("price")
                        else float("inf"),
                    )
                    print(
                        f"{len(csv_flights)} flights, {len(filtered)} under {MAX_DURATION_HOURS}h, "
                        f"best: ${best.get('miles_cost', '?')}"
                    )
                else:
                    print(
                        f"{len(csv_flights)} flights, none under {MAX_DURATION_HOURS}h"
                    )

                completed.add((dest_code, date_str))
                save_progress(completed)
                random_delay()

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Progress saved. {len(completed)} searches completed.")

    # Final summary
    print(f"\n{'='*60}")
    print(f"Search complete! {len(completed)} total searches.")
    print(f"All flights: {OUTPUT_FILE_ALL}")
    print(f"Filtered flights (<{MAX_DURATION_HOURS}h): {OUTPUT_FILE_FILTERED}")

    # Sort the filtered file by price
    if os.path.exists(OUTPUT_FILE_FILTERED):
        import pandas as pd

        df = pd.read_csv(OUTPUT_FILE_FILTERED)
        df = df.sort_values("price")
        df.to_csv(OUTPUT_FILE_FILTERED, index=False)
        print(f"\nTop 10 cheapest flights (under {MAX_DURATION_HOURS}h):")
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
