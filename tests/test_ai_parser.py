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
