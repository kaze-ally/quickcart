"""
debug_bigbasket.py — visible browser, prints ALL JSON responses from bigbasket.com
Run: python debug_bigbasket.py
"""
from playwright.sync_api import sync_playwright
import json

QUERY = input("Product to search (default: milk): ").strip() or "milk"
captured = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )
    ctx.add_cookies([
        {"name": "_bb_cid",        "value": "4",      "domain": ".bigbasket.com", "path": "/"},
        {"name": "_bb_pin_code",   "value": "400077", "domain": ".bigbasket.com", "path": "/"},
        {"name": "x-channel",      "value": "web",    "domain": ".bigbasket.com", "path": "/"},
        {"name": "_bb_bb2.0",      "value": "1",      "domain": ".bigbasket.com", "path": "/"},
        {"name": "_bb_sa_ids",     "value": "25476",  "domain": ".bigbasket.com", "path": "/"},
        {"name": "isintegratedsa", "value": "true",   "domain": ".bigbasket.com", "path": "/"},
        {"name": "xentrycontext",  "value": "bbnow",  "domain": ".bigbasket.com", "path": "/"},
        {"name": "xentrycontextid","value": "10",     "domain": ".bigbasket.com", "path": "/"},
    ])
    page = ctx.new_page()

    def on_response(response):
        url = response.url
        # Skip fonts, images, analytics
        if any(x in url for x in [".png",".jpg",".woff",".css",".svg","google","facebook",
                                    "analytics","collector","gtm","sentry","nr-data"]):
            return
        status = response.status
        ct = response.headers.get("content-type","")
        if "json" not in ct: return
        if "bigbasket.com" not in url: return

        try:
            body = response.json()
            s = json.dumps(body)
            captured.append({"url": url, "status": status, "body": body, "preview": s[:300]})
            print(f"\n✅ [{status}] {url}")
            print(f"   Keys: {list(body.keys())[:8]}")
            print(f"   Preview: {s[:200]}")
        except:
            pass

    page.on("response", on_response)

    print(f"\n📡 Opening BigBasket and searching '{QUERY}'...")
    print("   Wait for results to fully load, then press ENTER here\n")
    page.goto(f"https://www.bigbasket.com/ps/?q={QUERY}&nc=as", timeout=30000)
    page.wait_for_timeout(4000)

    input("\nPress ENTER after products are visible on screen...")

    # Save full capture
    with open("bigbasket_debug.json", "w") as f:
        json.dump(captured, f, indent=2)

    print(f"\n{'='*60}")
    print(f"TOTAL JSON RESPONSES: {len(captured)}")
    print(f"{'='*60}")
    for i, c in enumerate(captured):
        print(f"\n[{i+1}] {c['url']}")
        print(f"     {c['preview'][:250]}")

    print(f"\n💾 Full capture saved to bigbasket_debug.json")
    browser.close()