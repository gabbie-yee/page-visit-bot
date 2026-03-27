from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
from datetime import datetime, timezone
import random
import time
import os

SITES = [
    "https://www.merit123.com/",
    "https://www.24sportnews.com/",
]

GEO_USERS = [
    {
        "name": "sg_desktop",
        "locale": "en-SG",
        "timezone_id": "Asia/Singapore",
        "geolocation": {"latitude": 1.283, "longitude": 103.845, "accuracy": 100},
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1280, "height": 800},
    },
    {
        "name": "tr_mobile",
        "locale": "tr-TR",
        "timezone_id": "Europe/Istanbul",
        "geolocation": {"latitude": 41.0082, "longitude": 28.9784, "accuracy": 100},
        "user_agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.0 Mobile/15E148 Safari/604.1"
        ),
        "viewport": {"width": 390, "height": 844},
    },
]

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

MAX_CLICKS_PER_SESSION = 3
BACK_PROBABILITY = 0.35
MIN_LINKS_REQUIRED = 1


def human_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_url(url: str) -> str:
    return url.rstrip("/")


def is_internal_link(href: str, base_domain: str) -> bool:
    if not href:
        return False

    href = href.strip().lower()

    if (
        href.startswith("#")
        or href.startswith("mailto:")
        or href.startswith("tel:")
        or href.startswith("javascript:")
    ):
        return False

    if href.startswith("/"):
        return True

    if href.startswith("http://") or href.startswith("https://"):
        return urlparse(href).netloc == base_domain

    return False


def get_internal_link_candidates(page, current_url: str):
    base_domain = urlparse(current_url).netloc
    links = page.locator("a[href]")
    count = links.count()

    candidates = []

    for i in range(count):
        link = links.nth(i)

        try:
            href = link.get_attribute("href")
            if not href or not is_internal_link(href, base_domain):
                continue

            text = (link.inner_text(timeout=1000) or "").strip()
            if len(text) > 120:
                text = text[:120]

            candidates.append({
                "locator": link,
                "href": href,
                "text": text,
            })
        except Exception:
            continue

    return candidates


def pick_random_unvisited_link(candidates, visited_urls: set, current_url: str):
    good = []

    for item in candidates:
        href = item["href"]

        if href.startswith("/"):
            absolute = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}{href}"
        elif href.startswith("http://") or href.startswith("https://"):
            absolute = href
        else:
            continue

        normalized = normalize_url(absolute)

        if normalized in visited_urls:
            continue

        good.append((item, normalized))

    if not good:
        return None, None

    return random.choice(good)


def simulate_reading(page):
    # Small scrolls down
    for _ in range(random.randint(2, 5)):
        page.mouse.wheel(0, random.randint(250, 700))
        human_delay(0.5, 1.4)

    # Sometimes scroll slightly up
    if random.random() < 0.5:
        page.mouse.wheel(0, -random.randint(150, 500))
        human_delay(0.5, 1.2)

    # Stay on page a bit
    human_delay(1.5, 4.5)


def save_shot(page, filename: str):
    path = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for site in SITES:
        site_name = urlparse(site).netloc.replace(".", "_")

        for user in GEO_USERS:
            print(f"\n========== SITE: {site} | USER: {user['name']} ==========")

            context = browser.new_context(
                user_agent=user["user_agent"],
                viewport=user["viewport"],
                locale=user["locale"],
                timezone_id=user["timezone_id"],
                geolocation=user["geolocation"],
                permissions=["geolocation"],
            )

            page = context.new_page()
            visited_urls = set()

            try:
                print(f"\n--- Opening homepage: {site} ---")
                response = page.goto(site, wait_until="domcontentloaded", timeout=60000)

                if response is not None:
                    print("Initial status:", response.status)
                else:
                    print("Initial status: no response object")

                page.wait_for_load_state("networkidle", timeout=60000)
                visited_urls.add(normalize_url(page.url))

                print("Title:", page.title())
                print("URL:", page.url)
                print("Time:", utc_now())
                print("Locale:", user["locale"])
                print("Timezone:", user["timezone_id"])
                print("Geolocation:", user["geolocation"])

                simulate_reading(page)
                save_shot(page, f"{site_name}_{user['name']}_home.png")

                for step in range(1, MAX_CLICKS_PER_SESSION + 1):
                    print(f"\n--- Session step {step} ---")
                    current_url = page.url
                    candidates = get_internal_link_candidates(page, current_url)

                    print(f"Found {len(candidates)} internal link candidates")

                    if len(candidates) < MIN_LINKS_REQUIRED:
                        print("Not enough internal links, stop session")
                        break

                    chosen, chosen_url = pick_random_unvisited_link(
                        candidates,
                        visited_urls,
                        current_url,
                    )

                    if not chosen:
                        print("No unvisited internal link available, stop session")
                        break

                    print("Click target href:", chosen["href"])
                    print("Click target text:", chosen["text"] or "[no text]")

                    try:
                        chosen["locator"].click(timeout=5000)
                        page.wait_for_load_state("networkidle", timeout=60000)
                        visited_urls.add(normalize_url(page.url))

                        print("After click title:", page.title())
                        print("After click URL:", page.url)
                        print("Time:", utc_now())

                        simulate_reading(page)
                        save_shot(page, f"{site_name}_{user['name']}_step{step}.png")

                    except Exception as click_error:
                        print("Click failed:", click_error)
                        break

                    # Sometimes behave like a real user and go back
                    if step < MAX_CLICKS_PER_SESSION and random.random() < BACK_PROBABILITY:
                        try:
                            print("Going back...")
                            page.go_back(wait_until="domcontentloaded", timeout=60000)
                            page.wait_for_load_state("networkidle", timeout=60000)

                            print("Back URL:", page.url)
                            print("Back title:", page.title())

                            simulate_reading(page)
                            save_shot(page, f"{site_name}_{user['name']}_back_after_step{step}.png")
                        except Exception as back_error:
                            print("Back failed:", back_error)

            except Exception as e:
                print("ERROR:", e)

            finally:
                page.close()
                context.close()

    browser.close()