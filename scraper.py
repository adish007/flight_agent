# scraper.py
import random
import time
from playwright.sync_api import sync_playwright, Page, Browser
from playwright_stealth import stealth_sync
from config import SLEEP_MIN_SEC, SLEEP_MAX_SEC


def create_browser() -> tuple:
    """Launch a stealth Playwright browser. Returns (playwright, browser, page)."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": random.randint(1200, 1400), "height": random.randint(800, 1000)},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    stealth_sync(page)
    return pw, browser, page


def close_browser(pw, browser) -> None:
    """Cleanly close browser and playwright."""
    browser.close()
    pw.stop()


def scrape_page(page: Page, url: str) -> str | None:
    """Navigate to URL and return page HTML content, or None on failure."""
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        # Wait for flight results to render
        time.sleep(random.uniform(SLEEP_MIN_SEC, SLEEP_MAX_SEC))
        # Try to wait for results container (adjust selector after inspecting AA.com)
        try:
            page.wait_for_selector("[class*='flight'], [class*='slice'], [class*='result']", timeout=15000)
        except Exception:
            pass  # Page may have loaded but with different structure
        return page.content()
    except Exception as e:
        print(f"  Error loading {url}: {e}")
        return None


def random_delay() -> None:
    """Sleep for a random duration to appear human."""
    time.sleep(random.uniform(SLEEP_MIN_SEC, SLEEP_MAX_SEC))
