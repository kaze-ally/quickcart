"""
api_sniffer.py — prints ALL network calls in real time.
Instructions:
  1. Run this script
  2. Browser opens → set location → search your product
  3. Watch the terminal — search API calls print instantly
  4. Press ENTER to save and exit
"""
from playwright.sync_api import sync_playwright
import json

PRODUCT = input("Product to search (e.g. football): ").strip() or "football"
SITE    = input("Site? [1] Blinkit  [2] Zepto  [3] Swiggy Instamart : ").strip()

captured = []

def handle_response(response):
    url = response.url
    if any(url.endswith(ext) for ext in [".woff2",".woff",".js",".css",".png",".jpg",".ico",".svg"]):
        return
    if any(s in url for s in ["facebook","google","appsflyer","firebase","sentry","gtm"]):
        return
    try:
        body = response.body()
        if not body:
            return
        try:
            data = json.loads(body)
            preview = json.dumps(data)[:300]
            tag = "🟢 JSON"
        except Exception:
            preview = body.decode("utf-8", errors="ignore")[:200]
            tag = "⚪"
        
        captured.append({"url": url, "status": response.status, "preview": preview})
        print(f"\n{tag} [{response.status}] {url}")
        print(f"   {preview[:200]}")
    except Exception:
        pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.on("response", handle_response)

    if SITE == "3":
        url = "https://www.swiggy.com/instamart"
    elif SITE == "2":
        url = "https://www.zeptonow.com"
    else:
        url = "https://blinkit.com"

    print(f"\n📡 Browser is opening {url}")
    print(f"   → Set your location")
    print(f"   → Search for '{PRODUCT}'  (watch terminal for API calls!)")
    print(f"   → Once results load, press ENTER here\n")

    page.goto(url)
    input("\nPress ENTER after results are fully visible...")

    with open("captured_apis.json", "w", encoding="utf-8") as f:
        json.dump(captured, f, indent=2)

    print(f"\n✅ {len(captured)} responses saved to captured_apis.json")
    browser.close()