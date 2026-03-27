from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone
import random
import time
import os

SITES = [
    "https://www.merit123.com/",
    "https://www.24sportnews.com/"
]

MAX_STEPS = 3   # how deep user goes

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

USER_PROFILES = [
    {
        "name": "desktop",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "viewport": {"width": 1280, "height": 800},
    },
    {
        "name": "mobile",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Version/16.0 Mobile Safari/604.1",
        "viewport": {"width": 390, "height": 844},
    },
]


def human_delay(a=1, b=3):
    time.sleep(random.uniform(a, b))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def is_internal(href, base_domain):
    if not href:
        return False

    if href.startswith("/"):
        return True

    if href.startswith("http"):
        return urlparse(href).netloc == base_domain

    return False


def get_random_internal_link(page, base_domain):
    links = page.locator("a[href]")
    count = links.count()

    valid_links = []

    for i in range(count):
        link = links.nth(i)
        href = link.get_attribute("href")

        if not href:
            continue

        if is_internal(href, base_domain):
            valid_links.append((link, href))

    if not valid_links:
        return None, None

    return random.choice(valid_links)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for site in SITES:
        base_domain = urlparse(site).netloc

        for user in USER_PROFILES:
            print(f"\n===== SITE: {site} | USER: {user['name']} =====")

            context = browser.new_context(
                user_agent=user["user_agent"],
                viewport=user["viewport"],
            )

            page = context.new_page()

            try:
                # STEP 1: open homepage
                print(f"\n--- Opening: {site} ---")
                page.goto(site, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")

                human_delay()

                for step in range(MAX_STEPS):
                    print(f"\nStep {step+1}")

                    # scroll like user
                    for _ in range(random.randint(2, 4)):
                        page.mouse.wheel(0, random.randint(300, 800))
                        human_delay(0.5, 1.5)

                    print("Title:", page.title())
                    print("URL:", page.url)
                    print("Time:", utc_now())

                    # screenshot
                    filename = f"{SCREENSHOT_DIR}/{base_domain}_{user['name']}_step{step}.png"
                    page.screenshot(path=filename, full_page=True)

                    # pick random internal link
                    link, href = get_random_internal_link(page, base_domain)

                    if not link:
                        print("No internal links found, stop")
                        break

                    print("Clicking:", href)

                    try:
                        link.click(timeout=5000)
                        page.wait_for_load_state("networkidle")
                        human_delay()
                    except Exception as e:
                        print("Click failed:", e)
                        break

            except Exception as e:
                print("ERROR:", e)

            finally:
                context.close()

    browser.close()