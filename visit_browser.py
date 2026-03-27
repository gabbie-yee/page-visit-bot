from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import os
import random
import time

URLS = [
    "https://www.merit123.com",
    "https://www.merit123.com/tr/category/news"
]

os.makedirs("screenshots", exist_ok=True)

def human_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def utc_now():
    return datetime.now(timezone.utc).isoformat()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800}
    )

    for i, url in enumerate(URLS):
        page = context.new_page()

        try:
            print(f"\n--- Visiting: {url} ---")

            response = page.goto(url, wait_until="domcontentloaded", timeout=60000)

            if response:
                print("Status:", response.status)

            page.wait_for_load_state("networkidle")
            human_delay()

            # scroll
            for _ in range(3):
                page.mouse.wheel(0, 400)
                human_delay(0.5, 1.5)

            page.mouse.wheel(0, -400)
            human_delay()

            print("Title:", page.title())
            print("URL:", page.url)
            print("Time:", utc_now())

            # try click
            try:
                locator = page.locator("a[href='/tr/category/news']").first

                if locator.count() > 0:
                    print("Clicking link...")
                    locator.click()
                    page.wait_for_load_state("networkidle")
                    human_delay()

                    page.screenshot(path=f"screenshots/page_click_{i}.png", full_page=True)
                else:
                    print("No clickable link found")

            except Exception as e:
                print("Click skipped:", e)

            # main screenshot
            page.screenshot(path=f"screenshots/page_{i}.png", full_page=True)

        except Exception as e:
            print("ERROR:", url, e)

        finally:
            page.close()

    browser.close()