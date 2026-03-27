from playwright.sync_api import sync_playwright
from datetime import datetime

URL = "https://www.merit123.com"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )

    page = context.new_page()

    print("Opening page...")
    page.goto(URL, wait_until="networkidle")

    print("Page title:", page.title())

    # simulate user behavior
    page.wait_for_timeout(2000)   # stay 2s
    page.mouse.wheel(0, 1000)    # scroll down
    page.wait_for_timeout(1000)

    print("Visited at:", datetime.utcnow())

    browser.close()