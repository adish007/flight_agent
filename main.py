# main.py
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pandas as pd

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

# One-way legs CSV (intermediate data)
LEGS_FILE = "legs.csv"
LEGS_COLUMNS = [
    "direction",  # "outbound" or "return"
    "destination",
    "city_name",
    "date",
    "price",
    "airline",
    "duration_hrs",
    "stops",
    "departure_time",
    "arrival_time",
]


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
    match_hr = re.search(r"(\d+)\s*hr", duration_str)
    hours = int(match_hr.group(1)) if match_hr else 0
    match_min = re.search(r"(\d+)\s*min", duration_str)
    minutes = int(match_min.group(1)) if match_min else 0
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


def search_and_save_leg(
    direction: str, origin: str, dest: str, dest_code: str, city_name: str, date_str: str
) -> list[dict]:
    """Search one leg and return parsed results ready for CSV."""
    for attempt in range(MAX_RETRIES):
        raw = search_flights(origin, dest, date_str, NUM_ADULTS, max_stops=1)
        if raw:
            break
        if attempt < MAX_RETRIES - 1:
            random_delay()
    else:
        return []

    results = []
    seen = set()
    for f in raw:
        dur = parse_duration_hrs(f.get("duration", ""))
        price = parse_price(f.get("price", ""))
        if dur is None or price is None:
            continue
        if dur >= MAX_DURATION_HOURS:
            continue

        key = (f.get("airline"), f.get("departure_time"), price)
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "direction": direction,
            "destination": dest_code,
            "city_name": city_name,
            "date": date_str,
            "price": price,
            "airline": f.get("airline", ""),
            "duration_hrs": round(dur, 2),
            "stops": parse_stops(f.get("stops", "")),
            "departure_time": f.get("departure_time", ""),
            "arrival_time": f.get("arrival_time", ""),
        })

    return results


def append_legs_csv(legs: list[dict]) -> None:
    """Append leg records to the legs CSV file."""
    import csv

    file_exists = os.path.exists(LEGS_FILE)
    with open(LEGS_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEGS_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(legs)


def build_round_trips() -> None:
    """Post-process: combine outbound + return legs into round trips for each trip length."""
    if not os.path.exists(LEGS_FILE):
        print("No legs data found.")
        return

    df = pd.read_csv(LEGS_FILE)
    outbound = df[df["direction"] == "outbound"].copy()
    returns = df[df["direction"] == "return"].copy()

    if outbound.empty or returns.empty:
        print("Not enough data for round trips.")
        return

    # For each outbound leg, find the cheapest return for each trip length
    # Group by destination and date to get cheapest one-way per date
    best_outbound = (
        outbound.sort_values("price")
        .groupby(["destination", "date"])
        .first()
        .reset_index()
    )
    best_return = (
        returns.sort_values("price")
        .groupby(["destination", "date"])
        .first()
        .reset_index()
    )

    trips = []
    for _, out_row in best_outbound.iterrows():
        depart_date = date.fromisoformat(out_row["date"])
        dest = out_row["destination"]

        for trip_days in TRIP_LENGTHS:
            return_date = depart_date + timedelta(days=trip_days)
            return_date_str = return_date.strftime("%Y-%m-%d")

            ret_match = best_return[
                (best_return["destination"] == dest)
                & (best_return["date"] == return_date_str)
            ]
            if ret_match.empty:
                continue

            ret_row = ret_match.iloc[0]
            total = int(out_row["price"]) + int(ret_row["price"])

            trips.append({
                "destination": dest,
                "city_name": out_row["city_name"],
                "depart_date": out_row["date"],
                "return_date": return_date_str,
                "trip_days": trip_days,
                "outbound_price": int(out_row["price"]),
                "return_price": int(ret_row["price"]),
                "total_price": total,
                "outbound_airline": out_row["airline"],
                "return_airline": ret_row["airline"],
                "outbound_duration_hrs": out_row["duration_hrs"],
                "return_duration_hrs": ret_row["duration_hrs"],
                "outbound_stops": int(out_row["stops"]),
                "return_stops": int(ret_row["stops"]),
            })

    if not trips:
        print("No valid round trips found.")
        return

    trips_df = pd.DataFrame(trips).sort_values("total_price")
    trips_df.to_csv(OUTPUT_FILE_FILTERED, index=False)

    print(f"\nGenerated {len(trips_df)} round-trip combinations.")
    print(f"Saved to {OUTPUT_FILE_FILTERED}")
    print(f"\nTop 20 cheapest round trips:")
    cols = [
        "destination", "city_name", "depart_date", "return_date",
        "trip_days", "total_price", "outbound_airline", "return_airline",
    ]
    print(trips_df[cols].head(20).to_string(index=False))


def main():
    dates = generate_dates()
    completed = load_progress()
    destinations = list(DESTINATIONS.items())

    # Build search tasks: one outbound + one return per (destination, date)
    tasks = []
    for dest_code, city_name in destinations:
        for search_date in dates:
            # Outbound: BOS -> dest
            key_out = ("outbound", dest_code, search_date)
            if key_out not in completed:
                tasks.append((key_out, ORIGIN, dest_code, dest_code, city_name, search_date))
            # Return: dest -> BOS
            key_ret = ("return", dest_code, search_date)
            if key_ret not in completed:
                tasks.append((key_ret, dest_code, ORIGIN, dest_code, city_name, search_date))

    # Also search return dates that extend into June (for trips departing late May)
    max_trip = max(TRIP_LENGTHS)
    extra_end = date.fromisoformat(dates[-1]) + timedelta(days=max_trip)
    extra_start = date.fromisoformat(dates[-1]) + timedelta(days=1)
    extra_date = extra_start
    while extra_date <= extra_end:
        date_str = extra_date.strftime("%Y-%m-%d")
        for dest_code, city_name in destinations:
            key_ret = ("return", dest_code, date_str)
            if key_ret not in completed:
                tasks.append((key_ret, dest_code, ORIGIN, dest_code, city_name, date_str))
        extra_date += timedelta(days=1)

    total_legs = len(destinations) * len(dates) * 2
    already_done = len(completed)

    print("Caribbean Flight Search Agent (via Google Flights)")
    print(f"Origin: {ORIGIN}")
    print(f"Destinations: {len(destinations)}")
    print(f"Dates: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"Trip lengths: {TRIP_LENGTHS} days (computed in post-processing)")
    print(f"Searches: {len(tasks)} remaining | {already_done} already done")
    print(f"Parallel workers: {MAX_WORKERS}")
    print("---")

    if not tasks:
        print("All searches already complete! Running post-processing...")
        build_round_trips()
        return

    count = 0

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_task = {}
            for key, origin, dest, dest_code, city_name, search_date in tasks:
                direction = key[0]
                future = executor.submit(
                    search_and_save_leg, direction, origin, dest, dest_code, city_name, search_date
                )
                future_to_task[future] = key

            for future in as_completed(future_to_task):
                key = future_to_task[future]
                direction, dest_code, search_date = key
                count += 1

                try:
                    legs = future.result()
                except Exception as e:
                    log_error(f"{direction},{dest_code},{search_date},{e}")
                    print(f"  [{count}/{len(tasks)}] {direction} {dest_code} {search_date} ERROR: {e}")
                    completed.add(key)
                    if count % 20 == 0:
                        save_progress(completed)
                    continue

                if legs:
                    append_legs_csv(legs)
                    cheapest = min(legs, key=lambda x: x["price"])
                    print(
                        f"  [{count}/{len(tasks)}] {direction:8s} {dest_code} {search_date} "
                        f"— {len(legs)} flights, best ${cheapest['price']} ({cheapest['airline']})"
                    )
                else:
                    print(f"  [{count}/{len(tasks)}] {direction:8s} {dest_code} {search_date} — no flights under {MAX_DURATION_HOURS}h")

                completed.add(key)
                if count % 20 == 0:
                    save_progress(completed)

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Progress saved. {len(completed)} searches completed.")

    save_progress(completed)

    # Post-processing: build round trips from legs
    print(f"\n{'='*60}")
    print("Post-processing: building round-trip combinations...")
    build_round_trips()


if __name__ == "__main__":
    main()
