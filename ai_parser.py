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
