"""
Run once to find exact Blinkit snippet structure.
python debug_blinkit.py
"""
from playwright.sync_api import sync_playwright
import json

lat, lon = 28.465204, 77.06159
captured = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        geolocation={"latitude": lat, "longitude": lon},
        permissions=["geolocation"],
    )
    ctx.add_cookies([
        {"name": "gr_1_lat",      "value": str(lat),   "domain": "blinkit.com", "path": "/"},
        {"name": "gr_1_lon",      "value": str(lon),   "domain": "blinkit.com", "path": "/"},
        {"name": "gr_1_locality", "value": "1849",     "domain": "blinkit.com", "path": "/"},
        {"name": "city",          "value": "Bhiwandi", "domain": "blinkit.com", "path": "/"},
    ])
    page = ctx.new_page()

    def on_response(response):
        if "layout/search" in response.url and response.status == 200:
            try:
                captured.append(response.json())
                print(f"Captured: {response.url[:80]}")
            except:
                pass

    page.on("response", on_response)
    page.goto("https://blinkit.com/s/?q=football", timeout=20000)
    page.wait_for_timeout(5000)
    browser.close()

if not captured:
    print("Nothing captured!")
else:
    data = captured[0]
    snippets = data.get("response", {}).get("snippets", [])
    print(f"\nTotal snippets: {len(snippets)}")

    # Print widget_type of each snippet
    print("\nSnippet types:")
    for i, s in enumerate(snippets):
        print(f"  [{i}] widget_type={s.get('widget_type')} | data keys={list(s.get('data',{}).keys())[:6]}")

    # Find first snippet that looks like a product
    print("\n--- FIRST 3 SNIPPETS FULL DATA ---")
    for i, s in enumerate(snippets[:3]):
        print(f"\n[{i}] widget_type: {s.get('widget_type')}")
        print(json.dumps(s.get("data", {}), indent=2)[:1000])
        print("...")