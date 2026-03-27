from playwright.sync_api import sync_playwright
from datetime import datetime

URLS = [
    "https://www.merit123.com",
    "https://www.merit123.com/tr/category/news",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for url in URLS:
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"{datetime.utcnow().isoformat()}Z | OK | {url} | title={page.title()}")
        except Exception as e:
            print(f"{datetime.utcnow().isoformat()}Z | ERROR | {url} | {e}")

    browser.close()