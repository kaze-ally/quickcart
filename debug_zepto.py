"""
Run this once to print the full Zepto API response structure.
python debug_zepto.py
"""
import requests, json, uuid

state = {
    "zepto_cookie":  "_fbp=fb.1.1774019715558.384175330142702883; _gcl_au=1.1.1171135500.1774019717; _ga=GA1.1.629480075.1774019717;",
    "zepto_xsrf":    "bE2oHUJOyIEOvQzEz-CMr:GKn67JEgzrvftxNJuDFEriprMLM.XjjjXGYiOv3M5WYHM37wvuK/VXMMzZ9IDBjIm5IHiJo",
    "zepto_csrf":    "36Iq75TT5EI",
    "zepto_session": "1ae64c04-15b2-42eb-b07a-ff234b5caa58",
}

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
    "app_sub_platform": "WEB",
    "app_version": "14.33.2",
    "appversion": "14.33.2",
    "auth_from_cookie": "true",
    "auth_revamp_flow": "v2",
    "compatible_components": "CONVENIENCE_FEE,RAIN_FEE,EXTERNAL_COUPONS,STANDSTILL,BUNDLE,MULTI_SELLER_ENABLED,PIP_V1,ROLLUPS",
    "content-type": "application/json",
    "device_id": "957ae239-b8e1-4fa3-9e8d-6d30df853a41",
    "deviceid": "957ae239-b8e1-4fa3-9e8d-6d30df853a41",
    "marketplace_type": "SUPER_SAVER",
    "origin": "https://www.zepto.com",
    "platform": "WEB",
    "referer": "https://www.zepto.com/search?query=football",
    "session_id":  state["zepto_session"],
    "sessionid":   state["zepto_session"],
    "source": "DIRECT",
    "store_id":  "b4dc8d65-ed2e-4142-81b6-373982b13500",
    "store_ids": "b4dc8d65-ed2e-4142-81b6-373982b13500,0059ff6a-7eb0-477a-a7f5-69256f2c444b",
    "storeid":   "b4dc8d65-ed2e-4142-81b6-373982b13500",
    "store_etas": '{"b4dc8d65-ed2e-4142-81b6-373982b13500":-1,"0059ff6a-7eb0-477a-a7f5-69256f2c444b":-1}',
    "tenant": "ZEPTO",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "x-csrf-secret":    state["zepto_csrf"],
    "x-without-bearer": "true",
    "x-xsrf-token":     state["zepto_xsrf"],
    "cookie":           state["zepto_cookie"],
}

body = {
    "query": "football",
    "pageNumber": 0,
    "intentId": str(uuid.uuid4()),
    "mode": "AUTOSUGGEST",
    "userSessionId": state["zepto_session"],
}

resp = requests.post(
    "https://bff-gateway.zepto.com/user-search-service/api/v3/search",
    headers=headers, json=body, timeout=15,
)
print(f"Status: {resp.status_code}")
data = resp.json()

# Find PRODUCT_GRID widget and print first item in full
for widget in data.get("layout", []):
    if widget.get("widgetId") == "PRODUCT_GRID":
        items = widget.get("data", {}).get("resolver", {}).get("data", {}).get("items", [])
        if items:
            print(f"\n=== FULL FIRST ITEM ({len(items)} total items) ===")
            print(json.dumps(items[0], indent=2))
            print(f"\n=== ALL KEYS IN productResponse ===")
            pr = items[0].get("productResponse", {})
            print(list(pr.keys()))
            print(f"\n=== ALL KEYS IN productResponse.product ===")
            p = pr.get("product", {})
            print(list(p.keys()))
            print(f"\n=== PRICE-RELATED FIELDS ===")
            for key in pr:
                val = pr[key]
                if any(x in key.lower() for x in ["price", "mrp", "cost", "amount", "discount", "sell"]):
                    print(f"  productResponse.{key} = {val}")
            for key in p:
                val = p[key]
                if any(x in key.lower() for x in ["price", "mrp", "cost", "amount", "discount", "sell"]):
                    print(f"  product.{key} = {val}")
        break