# scraper.py
import time
import random
from fast_flights import FlightData, Passengers, get_flights
from config import SLEEP_MIN_SEC, SLEEP_MAX_SEC


def search_flights(
    origin: str,
    destination: str,
    date: str,
    n_adults: int = 2,
    max_stops: int | None = None,
) -> list[dict]:
    """Search Google Flights for flights on a given route and date.

    Returns a list of flight dicts with keys:
    airline, departure_time, arrival_time, duration, stops, price

    Uses local Playwright (headless Chromium) to render Google Flights,
    which avoids bot detection and the unreliable try.playwright.tech service.
    """
    try:
        result = get_flights(
            flight_data=[
                FlightData(date=date, from_airport=origin, to_airport=destination)
            ],
            trip="one-way",
            passengers=Passengers(adults=n_adults),
            seat="economy",
            max_stops=max_stops,
            fetch_mode="local",
        )

        flights = []
        seen = set()
        for f in result.flights:
            # Deduplicate (fast-flights sometimes returns duplicates)
            key = (f.name, f.departure, f.arrival, f.price)
            if key in seen:
                continue
            seen.add(key)

            flights.append(
                {
                    "airline": f.name,
                    "departure_time": f.departure,
                    "arrival_time": f.arrival,
                    "duration": f.duration,
                    "stops": f.stops,
                    "price": f.price,
                }
            )

        return flights
    except Exception as e:
        print(f"  Error searching {origin}->{destination} on {date}: {e}")
        return []


def random_delay() -> None:
    """Sleep for a random duration to be polite to the API."""
    time.sleep(random.uniform(SLEEP_MIN_SEC, SLEEP_MAX_SEC))
