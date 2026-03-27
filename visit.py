import requests
from datetime import datetime

URLS = [
    "https://www.merit123.com",
    "https://www.merit123.com/tr/category/news",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PageVisitBot/1.0)"
}

for url in URLS:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"{datetime.utcnow().isoformat()}Z | {r.status_code} | {url}")
    except Exception as e:
        print(f"{datetime.utcnow().isoformat()}Z | ERROR | {url} | {e}")