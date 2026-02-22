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
