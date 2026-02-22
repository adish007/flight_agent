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
