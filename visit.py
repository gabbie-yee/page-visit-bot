import requests
from datetime import datetime

URLS = [
    "https://www.merit123.com",
    "https://www.merit123.com/tr/category/news"
]

HEADERS = {
    "User-Agent": "SEO-Bot-Checker/1.0 (GitHubActions)"
}

for url in URLS:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)

        print("TIME:", datetime.utcnow())
        print("URL:", url)
        print("STATUS:", r.status_code)
        print("CONTENT LENGTH:", len(r.text))
        print("-" * 40)

    except Exception as e:
        print("ERROR:", url, e)