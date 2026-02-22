# main.py
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

from config import (
    ORIGIN,
    DESTINATIONS,
    NUM_ADULTS,
    MAX_DURATION_HOURS,
    MAX_RETRIES,
    MAX_WORKERS,
    TRIP_LENGTHS,
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
    """Load set of already-scraped keys."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return set(tuple(x) for x in json.load(f))
    return set()


def save_progress(completed: set) -> None:
    """Save progress to disk."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(completed), f)


def log_error(msg: str) -> None:
    """Append error to log file."""
    with open(ERRORS_LOG, "a") as f:
        f.write(f"{msg}\n")


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
    """Parse price string like '$507' to integer."""
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


def search_one_leg(origin: str, dest: str, date_str: str) -> list[dict]:
    """Search one direction and return parsed flight list."""
    for attempt in range(MAX_RETRIES):
        raw = search_flights(origin, dest, date_str, NUM_ADULTS, max_stops=1)
        if raw:
            return raw
        if attempt < MAX_RETRIES - 1:
            random_delay()
    return []


def find_best_flight(flights: list[dict], max_hours: float) -> dict | None:
    """Find cheapest flight under the duration limit."""
    candidates = []
    for f in flights:
        dur = parse_duration_hrs(f.get("duration", ""))
        price = parse_price(f.get("price", ""))
        if dur is not None and dur < max_hours and price is not None:
            candidates.append({**f, "_dur": dur, "_price": price})
    if not candidates:
        return None
    return min(candidates, key=lambda x: x["_price"])


def search_trip(dest_code: str, city_name: str, depart_date_str: str, trip_days: int) -> dict | None:
    """Search a full round trip: outbound + return, return the combined result."""
    return_date = date.fromisoformat(depart_date_str) + timedelta(days=trip_days)
    return_date_str = return_date.strftime("%Y-%m-%d")

    # Search outbound: BOS -> destination
    outbound_flights = search_one_leg(ORIGIN, dest_code, depart_date_str)
    if not outbound_flights:
        return None

    best_out = find_best_flight(outbound_flights, MAX_DURATION_HOURS)
    if not best_out:
        return None

    random_delay()

    # Search return: destination -> BOS
    return_flights = search_one_leg(dest_code, ORIGIN, return_date_str)
    if not return_flights:
        return None

    best_ret = find_best_flight(return_flights, MAX_DURATION_HOURS)
    if not best_ret:
        return None

    total_price = best_out["_price"] + best_ret["_price"]

    return {
        "destination": dest_code,
        "city_name": city_name,
        "depart_date": depart_date_str,
        "return_date": return_date_str,
        "trip_days": trip_days,
        "outbound_price": best_out["_price"],
        "return_price": best_ret["_price"],
        "total_price": total_price,
        "outbound_airline": best_out.get("airline", ""),
        "return_airline": best_ret.get("airline", ""),
        "outbound_duration_hrs": round(best_out["_dur"], 2),
        "return_duration_hrs": round(best_ret["_dur"], 2),
        "outbound_stops": parse_stops(best_out.get("stops", "")),
        "return_stops": parse_stops(best_ret.get("stops", "")),
    }


def main():
    dates = generate_dates()
    completed = load_progress()
    destinations = list(DESTINATIONS.items())

    # Build all search tasks: (dest_code, city, depart_date, trip_days)
    tasks = []
    for dest_code, city_name in destinations:
        for depart_date in dates:
            for trip_days in TRIP_LENGTHS:
                key = (dest_code, depart_date, str(trip_days))
                if key not in completed:
                    tasks.append((dest_code, city_name, depart_date, trip_days))

    total = len(destinations) * len(dates) * len(TRIP_LENGTHS)
    already_done = len(completed)

    print("Caribbean Flight Search Agent (via Google Flights)")
    print(f"Origin: {ORIGIN}")
    print(f"Destinations: {len(destinations)}")
    print(f"Dates: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"Trip lengths: {TRIP_LENGTHS} days")
    print(f"Total searches: {total} | Done: {already_done} | Remaining: {len(tasks)}")
    print(f"Parallel workers: {MAX_WORKERS}")
    print("---")

    if not tasks:
        print("All searches already complete!")
        _print_summary()
        return

    count = 0

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_task = {}
            for dest_code, city_name, depart_date, trip_days in tasks:
                future = executor.submit(
                    search_trip, dest_code, city_name, depart_date, trip_days
                )
                future_to_task[future] = (dest_code, city_name, depart_date, trip_days)

            for future in as_completed(future_to_task):
                dest_code, city_name, depart_date, trip_days = future_to_task[future]
                key = (dest_code, depart_date, str(trip_days))
                count += 1

                try:
                    result = future.result()
                except Exception as e:
                    log_error(f"{dest_code},{depart_date},{trip_days},{e}")
                    print(f"  [{count}/{len(tasks)}] {dest_code} {depart_date} {trip_days}d ERROR: {e}")
                    completed.add(key)
                    save_progress(completed)
                    continue

                if result:
                    append_to_csv([result], OUTPUT_FILE_ALL)
                    if result["outbound_duration_hrs"] < MAX_DURATION_HOURS and result["return_duration_hrs"] < MAX_DURATION_HOURS:
                        append_to_csv([result], OUTPUT_FILE_FILTERED)
                    print(
                        f"  [{count}/{len(tasks)}] {dest_code} {depart_date} {trip_days}d "
                        f"${result['total_price']} ({result['outbound_airline']}/{result['return_airline']})"
                    )
                else:
                    print(f"  [{count}/{len(tasks)}] {dest_code} {depart_date} {trip_days}d — no flights")

                completed.add(key)
                if count % 10 == 0:
                    save_progress(completed)

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Progress saved. {len(completed)} searches completed.")

    save_progress(completed)
    _print_summary()


def _print_summary():
    """Print final summary and top deals."""
    print(f"\n{'='*60}")
    print(f"All trips: {OUTPUT_FILE_ALL}")
    print(f"Filtered trips (<{MAX_DURATION_HOURS}h each way): {OUTPUT_FILE_FILTERED}")

    if os.path.exists(OUTPUT_FILE_FILTERED):
        import pandas as pd

        df = pd.read_csv(OUTPUT_FILE_FILTERED)
        if not df.empty:
            df = df.sort_values("total_price")
            df.to_csv(OUTPUT_FILE_FILTERED, index=False)
            print(f"\nTop 15 cheapest round trips:")
            cols = ["destination", "city_name", "depart_date", "return_date",
                    "trip_days", "total_price", "outbound_airline", "return_airline"]
            print(df[cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
