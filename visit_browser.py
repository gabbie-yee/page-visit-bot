from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import os
import random
import time
from urllib.parse import urlparse, urljoin

URLS = [
    "https://www.merit123.com",
    "https://www.merit123.com/tr/category/news",
]

# Per-page click preferences
# Key = page you open first
# Value = list of preferred links to click on that page
CLICK_TARGETS = {
    "https://www.merit123.com": [
        "/tr/category/news",
        "tr/category/travel-transport",
    ],
    "https://www.merit123.com/tr/category/news": [
        "/tr/site/news-dunya",
        "tr/site/news-haberturk"
    ],
}

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def human_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_url(url: str) -> str:
    return url.rstrip("/")


def is_internal_link(href: str, base_domain: str) -> bool:
    if not href:
        return False

    href = href.strip()

    if href.startswith("#"):
        return False

    if href.startswith("/"):
        return True

    if href.startswith("http://") or href.startswith("https://"):
        return urlparse(href).netloc == base_domain

    return False


def href_matches_target(href: str, target: str, current_url: str) -> bool:
    if not href:
        return False

    absolute_href = urljoin(current_url, href)
    absolute_target = urljoin(current_url, target)

    return normalize_url(absolute_href) == normalize_url(absolute_target)


def find_clickable_link(page, current_url: str, preferred_targets: list[str]):
    base_domain = urlparse(current_url).netloc
    links = page.locator("a[href]")
    count = links.count()

    # 1. Try preferred targets first
    for target in preferred_targets:
        for i in range(count):
            link = links.nth(i)
            href = link.get_attribute("href")

            if href_matches_target(href, target, current_url):
                return link, f"preferred ({target})"

    # 2. Fallback: first internal link
    for i in range(count):
        link = links.nth(i)
        href = link.get_attribute("href")

        if is_internal_link(href, base_domain):
            return link, "internal fallback"

    return None, None


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )

    for i, start_url in enumerate(URLS):
        page = context.new_page()

        try:
            print(f"\n--- Visiting: {start_url} ---")

            response = page.goto(start_url, wait_until="domcontentloaded", timeout=60000)

            if response is not None:
                print("Status:", response.status)
            else:
                print("Status: no response object")

            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(1, 2)

            # Scroll down a bit
            for _ in range(3):
                page.mouse.wheel(0, 400)
                human_delay(0.5, 1.2)

            # Scroll up slightly
            page.mouse.wheel(0, -400)
            human_delay(0.8, 1.5)

            current_url = page.url
            preferred_targets = CLICK_TARGETS.get(normalize_url(start_url), [])

            print("Title:", page.title())
            print("Current URL:", current_url)
            print("Time:", utc_now())
            print("Preferred targets:", preferred_targets)

            try:
                link, reason = find_clickable_link(page, current_url, preferred_targets)

                if link:
                    href = link.get_attribute("href")
                    print(f"Clicking link [{reason}]: {href}")

                    link.click(timeout=5000)
                    page.wait_for_load_state("networkidle", timeout=60000)
                    human_delay(1, 2)

                    click_file = os.path.join(SCREENSHOT_DIR, f"page_click_{i}.png")
                    page.screenshot(path=click_file, full_page=True)
                    print(f"Click screenshot saved: {click_file}")
                    print("After click URL:", page.url)
                else:
                    print("No suitable clickable link found")

            except Exception as click_error:
                print(f"Click skipped: {click_error}")

            shot_file = os.path.join(SCREENSHOT_DIR, f"page_{i}.png")
            page.screenshot(path=shot_file, full_page=True)
            print(f"Main screenshot saved: {shot_file}")

        except Exception as e:
            print(f"ERROR visiting {start_url}: {e}")

        finally:
            page.close()

    browser.close()