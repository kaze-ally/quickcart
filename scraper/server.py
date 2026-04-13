"""
QuickCart Backend — Blinkit, Zepto, JioMart
No price history, clean and simple.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, json, threading, uuid

app = Flask(__name__)
CORS(app)

state = {
    "zepto_cookie":  "_fbp=fb.1.1774019715558.384175330142702883; _gcl_au=1.1.1171135500.1774019717; _ga=GA1.1.629480075.1774019717;",
    "zepto_xsrf":    "bE2oHUJOyIEOvQzEz-CMr:GKn67JEgzrvftxNJuDFEriprMLM.XjjjXGYiOv3M5WYHM37wvuK/VXMMzZ9IDBjIm5IHiJo",
    "zepto_csrf":    "36Iq75TT5EI",
    "zepto_session": "1ae64c04-15b2-42eb-b07a-ff234b5caa58",
    "jiomart_cookie":"nms_mgo_city=Mumbai; nms_mgo_state_code=MH; nms_mgo_pincode=400077; _ALGOLIA=anonymous-e6af42fa-be75-4b64-8ade-70e1cd5d0175; _ga=GA1.1.399947505.1775226287;",
    "bb_cookie": "_bb_locSrc=default; x-channel=web; _bb_vid=MTE5Mzg0NDU3NzI2Mzk5MjMwMg==; _bb_nhid=7427; _bb_dsid=7427; csrftoken=q9Lm8bUzrTYjmedtCRuV21Uy6FPnbcAICMnEHDRKc67E6oBiFRGLTOCLxsXnUAL6; _bb_bb2.0=1; bb2_enabled=true; bigbasket.com=039e2aed-da1b-467a-850a-7a67a8990e75; _gcl_au=1.1.520006463.1775225886; ufi=1; is_global=0; _bb_lat_long=MTkuMDc4NTk4OHw3Mi45MTAxNDU1OTk5OTk5OQ==; _bb_cid=4; isintegratedsa=true; _bb_addressinfo=MTkuMDc4NTk4OHw3Mi45MTAxNDU1OTk5OTk5OXxHYXJvZGlhIE5hZ2FyfDQwMDA3N3xNdW1iYWl8MXxmYWxzZXx0cnVlfHRydWV8QmlnYmFza2V0ZWVy; _bb_pin_code=400077; _bb_sa_ids=25476; is_integrated_sa=1; jentrycontextid=10; xentrycontextid=10; xentrycontext=bbnow; _is_tobacco_enabled=1; _bb_cda_sa_info=djIuY2RhX3NhLjEwLjI1NDc2; _ga=GA1.2.1906143274.1775225886;",
    "refreshing":    False,
}
lock = threading.Lock()
ZEPTO_IMG_BASE = "https://cdn.zeptonow.com/production//tr:w-500,ar-1-1,pr-true,f-webp,q-80/"

JIOMART_FILTER = (
    'attributes.status:ANY("active") AND '
    '(attributes.mart_availability:ANY("JIO","JIO_WA")) AND '
    '(attributes.available_regions:ANY("PANINDIAGROCERIES","PANINDIABOOKS","PANINDIAFASHION",'
    '"PANINDIAFURNITURE","TXCF","PANINDIAHOMEANDKITCHEN","PANINDIAHOMEIMPROVEMENT","S575",'
    '"PANINDIASTL","PANINDIAWELLNESS")) AND '
    '(attributes.inv_stores_1p:ANY("ALL","TD0S","S535","SURR","R300","SLI1","S575","440","254",'
    '"60","270","SF11","SF40","SX9A","SACU","R696","SE40","S0BN","R080","SK1M","SJ93","S573",'
    '"SLTY","V014","SLKO") OR '
    'attributes.inv_stores_3p:ANY("ALL","3P8JXZXRFC33","3P38SR7XFC37","3P8JXZXRFC31",'
    '"groceries_zone_non-essential_services","general_zone","groceries_zone_essential_services",'
    '"fashion_zone","electronics_zone")) AND '
    '(NOT attributes.vertical_code:ANY("ALCOHOL")) AND '
    '(NOT attributes.vertical_code:ANY("GROCERIES") OR NOT attributes.seller_ids:ANY("1"))'
)


def refresh_zepto_cookies():
    with lock:
        if state["refreshing"]: return
        state["refreshing"] = True
    try:
        from playwright.sync_api import sync_playwright
        print("\n[Refresh] Refreshing Zepto cookies...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
            page = ctx.new_page()
            page.goto("https://www.zepto.com", timeout=25000)
            page.wait_for_timeout(4000)
            cookies = ctx.cookies("https://www.zepto.com")
            state["zepto_cookie"]  = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            state["zepto_xsrf"]    = next((c["value"] for c in cookies if "xsrf"        in c["name"].lower()), state["zepto_xsrf"])
            state["zepto_csrf"]    = next((c["value"] for c in cookies if "csrf-secret" in c["name"].lower()), state["zepto_csrf"])
            state["zepto_session"] = next((c["value"] for c in cookies if "session"     in c["name"].lower()), state["zepto_session"])
            print(f"[Refresh] ✅ Zepto: {len(cookies)} cookies")
            ctx.close(); browser.close()
    except Exception as e:
        print(f"[Refresh] Error: {e}")
    finally:
        state["refreshing"] = False

threading.Thread(target=refresh_zepto_cookies, daemon=True).start()


def _dedup(products, platform):
    seen, unique = set(), []
    for p in products:
        k = (p["name"], p["price"])
        if k not in seen:
            seen.add(k); unique.append(p)
    print(f"  [{platform}] ✅ {len(unique)} products")
    return unique


# ══════════════════════════════════════════════════════════════════════════════
#  BLINKIT
# ══════════════════════════════════════════════════════════════════════════════

def fetch_blinkit(query, lat, lon):
    try:
        from playwright.sync_api import sync_playwright
        print(f"  [Blinkit] Launching browser...")
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
                    try: captured.append(response.json())
                    except: pass
            page.on("response", on_response)
            page.goto(f"https://blinkit.com/s/?q={query}", timeout=20000)
            page.wait_for_timeout(5000)
            browser.close()

        products = []
        for data in captured:
            for snippet in data.get("response", {}).get("snippets", []):
                if "product_card" not in snippet.get("widget_type", ""): continue
                p = _parse_blinkit_card(snippet.get("data", {}))
                if p: products.append(p)
        return _dedup(products, "Blinkit")
    except Exception as e:
        print(f"  [Blinkit] Error: {e}"); return []


def _parse_price_text(obj):
    text = obj.get("text", "") if isinstance(obj, dict) else str(obj)
    text = text.replace("₹", "").replace(",", "").strip()
    try: return int(float(text))
    except: return 0

def _parse_blinkit_card(d):
    name  = d.get("name",    {}).get("text", "")
    unit  = d.get("variant", {}).get("text", "")
    img   = d.get("image",   {}).get("url",  "")
    mrp   = _parse_price_text(d.get("mrp", {}))
    price = _parse_price_text(d.get("price", d.get("selling_price", d.get("discounted_price", {}))))
    # Product URL from click_action deeplink — extract product_id and build web URL
    url = "https://blinkit.com"
    try:
        deeplink = d.get("click_action", {}).get("blinkit_deeplink", {}).get("url", "")
        import re as _re
        pid = _re.search(r"product_id=(\d+)", deeplink)
        mid = _re.search(r"merchant_id=(\d+)", deeplink)
        if pid:
            url = f"https://blinkit.com/prn/p/prid/{pid.group(1)}"
            if mid:
                url += f"?merchant_id={mid.group(1)}"
    except: pass
    if not name: return None
    if not price: price = mrp
    if not mrp:   mrp = price
    if price < 5: return None
    return {"platform":"Blinkit","name":name,"unit":unit,"image":img,"price":price,"mrp":mrp,
            "url": url, "discount": round((1-price/mrp)*100) if mrp > price else 0}


# ══════════════════════════════════════════════════════════════════════════════
#  ZEPTO
# ══════════════════════════════════════════════════════════════════════════════

def fetch_zepto(query, lat, lon):
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
        "app_sub_platform": "WEB", "app_version": "14.33.2", "appversion": "14.33.2",
        "auth_from_cookie": "true", "auth_revamp_flow": "v2",
        "compatible_components": "CONVENIENCE_FEE,RAIN_FEE,EXTERNAL_COUPONS,STANDSTILL,BUNDLE,MULTI_SELLER_ENABLED,PIP_V1,ROLLUPS,SCHEDULED_DELIVERY,HOMEPAGE_V2,NEW_ETA_BANNER,SEARCH_PRODUCT_GRID_V2,DYNAMIC_FILTERS,SEARCH_FILTERS_V1,PLP_ON_SEARCH",
        "content-type": "application/json",
        "device_id": "957ae239-b8e1-4fa3-9e8d-6d30df853a41",
        "deviceid": "957ae239-b8e1-4fa3-9e8d-6d30df853a41",
        "marketplace_type": "SUPER_SAVER", "origin": "https://www.zepto.com", "platform": "WEB",
        "referer": f"https://www.zepto.com/search?query={query}",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
        "session_id": state["zepto_session"], "sessionid": state["zepto_session"],
        "source": "DIRECT",
        "store_id":  "b4dc8d65-ed2e-4142-81b6-373982b13500",
        "store_ids": "b4dc8d65-ed2e-4142-81b6-373982b13500,0059ff6a-7eb0-477a-a7f5-69256f2c444b",
        "storeid":   "b4dc8d65-ed2e-4142-81b6-373982b13500",
        "store_etas": '{"b4dc8d65-ed2e-4142-81b6-373982b13500":-1,"0059ff6a-7eb0-477a-a7f5-69256f2c444b":-1}',
        "tenant": "ZEPTO",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-csrf-secret": state["zepto_csrf"], "x-without-bearer": "true",
        "x-xsrf-token":  state["zepto_xsrf"], "cookie": state["zepto_cookie"],
    }
    body = {
        "query": query, "pageNumber": 0,
        "intentId": str(uuid.uuid4()),
        "mode": "AUTOSUGGEST", "userSessionId": state["zepto_session"],
    }
    try:
        resp = requests.post(
            "https://bff-gateway.zepto.com/user-search-service/api/v3/search",
            headers=headers, json=body, timeout=15,
        )
        print(f"  [Zepto] Status: {resp.status_code}")
        if resp.status_code in (401, 403):
            threading.Thread(target=refresh_zepto_cookies, daemon=True).start(); return []
        if resp.status_code != 200: return []
        data = resp.json()
        products = []
        for widget in data.get("layout", []):
            for item in widget.get("data",{}).get("resolver",{}).get("data",{}).get("items",[]):
                p = _parse_zepto_item(item)
                if p: products.append(p)
        return _dedup(products, "Zepto")
    except Exception as e:
        print(f"  [Zepto] Error: {e}"); return []

def _parse_zepto_item(item):
    pr = item.get("productResponse", {})
    if not pr: return None
    name   = pr.get("product", {}).get("name", "")
    price  = pr.get("discountedSellingPrice", pr.get("sellingPrice", 0))
    mrp    = pr.get("mrp", price)
    unit   = pr.get("productVariant", {}).get("formattedPacksize", "")
    images = pr.get("productVariant", {}).get("images", [])
    img    = (ZEPTO_IMG_BASE + images[0].get("path", "")) if images else ""
    # Zepto product URL — correct format: /pn/{slug}/pvid/{variant_id}/
    import re as _re
    variant_id = pr.get("productVariant", {}).get("id", "")
    slug = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") if name else ""
    url = (f"https://www.zepto.com/pn/{slug}/pvid/{variant_id}/"
           if variant_id else f"https://www.zepto.com/search?query={_re.sub(r' ', '+', name)}")
    if not name or not price: return None
    try: price = int(price)//100; mrp = int(mrp)//100
    except: return None
    if price < 5: return None
    return {"platform":"Zepto","name":name,"unit":unit,"image":img,"price":price,"mrp":mrp,
            "url": url, "discount": round((1-price/mrp)*100) if mrp > price else 0}


# ══════════════════════════════════════════════════════════════════════════════
#  JIOMART  —  POST /trex/search
# ══════════════════════════════════════════════════════════════════════════════

def fetch_jiomart(query, lat, lon):
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
        "content-type": "application/json",
        "origin":  "https://www.jiomart.com",
        "referer": f"https://www.jiomart.com/search?q={query}",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "cookie": state["jiomart_cookie"],
    }
    body = {
        "query": query,
        "pageSize": 20,
        "branch": "projects/sr-project-jiomart-jfront-prod/locations/global/catalogs/default_catalog/branches/0",
        "canonicalFilter": JIOMART_FILTER,
        "filter": JIOMART_FILTER,
        "queryExpansionSpec": {"condition": "AUTO", "pinUnexpandedResults": True},
        "spellCorrectionSpec": {"mode": "AUTO"},
        "userInfo": {"userId": None},
        "variantRollupKeys": ["variantId"],
        "visitorId": "anonymous-" + str(uuid.uuid4()),
        "facetSpecs": [
            {"facetKey": {"key": "brands"},     "limit": 10, "excludedFilterKeys": ["brands"]},
            {"facetKey": {"key": "categories"}, "limit": 10, "excludedFilterKeys": ["categories"]},
        ],
    }
    try:
        print(f"  [JioMart] POST /trex/search")
        resp = requests.post("https://www.jiomart.com/trex/search",
                             headers=headers, json=body, timeout=15)
        print(f"  [JioMart] Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  [JioMart] Body: {resp.text[:300]}")
            return []
        data = resp.json()
        print(f"  [JioMart] Top keys: {list(data.keys())[:8]}")
        products = []
        for result in data.get("results", []):
            p = _parse_jiomart_product(result)
            if p: products.append(p)
        # Debug if empty
        if not products and data.get("results"):
            sample = json.dumps(data["results"][0])[:600]
            print(f"  [JioMart] Sample result: {sample}")
        return _dedup(products, "JioMart")
    except Exception as e:
        print(f"  [JioMart] Error: {e}"); return []

def _attr_val(attrs, *keys):
    """Extract a numeric or text value from JioMart attributes dict."""
    for key in keys:
        v = attrs.get(key, {})
        if isinstance(v, dict):
            nums = v.get("numbers", v.get("text", []))
            if isinstance(nums, list) and nums: return nums[0]
            if isinstance(nums, (int, float, str)) and nums: return nums
        elif isinstance(v, (int, float)) and v: return v
        elif isinstance(v, str) and v: return v
    return 0

def _parse_jiomart_product(result):
    """
    JioMart Google Retail API structure:
      result.product.title       -- product name
      result.product.variants[]  -- prices live inside variants[0].attributes
    """
    product = result.get("product", {})
    if not product: return None
    name = product.get("title", "")
    if not name: return None

    # Prices are inside variants[], not top-level product
    variants = product.get("variants", [])
    variant  = variants[0] if variants else {}

    attrs = variant.get("attributes", {})
    price = _attr_val(attrs, "avg_selling_price", "selling_price", "price", "sp", "offer_price")
    mrp   = _attr_val(attrs, "mrp", "original_price", "max_price", "strike_price")
    unit  = _attr_val(attrs, "pack_size", "unit", "quantity", "net_quantity")

    # priceInfo fallback
    pi = variant.get("priceInfo", product.get("priceInfo", {}))
    if pi.get("price"):         price = pi["price"]
    if pi.get("originalPrice"): mrp   = pi["originalPrice"]

    # images from variant or product
    images = variant.get("images", product.get("images", []))
    img = images[0].get("uri", "") if images and isinstance(images[0], dict) else (images[0] if images else "")

    try:
        price = int(float(str(price).replace(",", "")))
        mrp   = int(float(str(mrp  ).replace(",", ""))) if mrp else price
    except:
        return None

    if price < 5: return None
    if not mrp or mrp < price: mrp = price

    # JioMart URL — use product id from result + name slug
    import re as _re
    product_id = result.get("id", "").replace("_P", "")
    slug = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") if name else ""
    # JioMart search URL as fallback (direct product URLs need login)
    url = (f"https://www.jiomart.com/search#{_re.sub(r' ', '+', name)}"
           if not product_id else
           f"https://www.jiomart.com/p/{slug}/{product_id}")

    return {
        "platform": "JioMart", "name": name, "unit": str(unit), "image": img,
        "price": price, "mrp": mrp, "url": url,
        "discount": round((1 - price/mrp)*100) if mrp > price else 0,
    }




# ══════════════════════════════════════════════════════════════════════════════
#  BIGBASKET  —  GET /listing-svc/v2/products
#  Real endpoint discovered via DevTools
# ══════════════════════════════════════════════════════════════════════════════

def fetch_bigbasket(query, lat, lon):
    """
    BigBasket listing-svc API with exact headers from DevTools.
    bucket_id comes from /ui-svc/v1/app-data/ — default is 8.
    """
    import re as _re
    slug = _re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")

    session = requests.Session()

    # Step 1: hit homepage to get fresh cookies + csrftoken
    try:
        home = session.get(
            "https://www.bigbasket.com/",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"},
            timeout=10
        )
        # Extract csurftoken from cookies
        csrf = session.cookies.get("csurftoken", "")
        print(f"  [BigBasket] Session cookies: {len(session.cookies)} | csrf: {csrf[:20] if csrf else 'none'}")
    except Exception as e:
        print(f"  [BigBasket] Homepage error: {e}")
        csrf = ""

    # Step 2: get bucket_id from app-data
    bucket_id = 8  # default from your debug output
    try:
        import time
        ts = int(time.time() * 1000)
        r = session.get(
            f"https://www.bigbasket.com/ui-svc/v1/app-data/?i={ts}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Referer": "https://www.bigbasket.com/",
                "x-channel": "BB-WEB",
                "x-entry-context": "bbnow",
                "x-entry-context-id": "10",
            },
            timeout=10
        )
        if r.status_code == 200:
            bucket_id = r.json().get("bucket_id", 8)
            print(f"  [BigBasket] bucket_id: {bucket_id}")
    except Exception as e:
        print(f"  [BigBasket] app-data error: {e}")

    # Step 3: search products
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
        "common-client-static-version": "101",
        "content-type": "application/json",
        "osmos-enabled": "true",
        "referer": f"https://www.bigbasket.com/ps/?q={query}&nc=as",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-channel": "BB-WEB",
        "x-entry-context": "bbnow",
        "x-entry-context-id": "10",
        "x-integrated-fc-door-visible": "false",
    }

    try:
        print(f"  [BigBasket] GET listing-svc?slug={slug}&bucket_id={bucket_id}")
        resp = session.get(
            "https://www.bigbasket.com/listing-svc/v2/products",
            params={"type": "ps", "slug": slug, "page": 1, "bucket_id": bucket_id},
            headers=headers,
            timeout=15,
        )
        print(f"  [BigBasket] Status: {resp.status_code} | Size: {len(resp.content)} bytes | Encoding: {resp.encoding}")

        if resp.status_code != 200 or not resp.content:
            print(f"  [BigBasket] Response: {resp.text[:200]}")
            return []

        # Handle compressed responses manually
        raw = resp.content
        content_encoding = resp.headers.get("content-encoding", "")
        print(f"  [BigBasket] Content-Encoding: {content_encoding}")
        try:
            if "br" in content_encoding:
                import brotli
                raw = brotli.decompress(raw)
            elif "gzip" in content_encoding:
                import gzip
                raw = gzip.decompress(raw)
            elif "deflate" in content_encoding:
                import zlib
                raw = zlib.decompress(raw)
            data = json.loads(raw)
        except Exception as decomp_err:
            print(f"  [BigBasket] Decompress error: {decomp_err}")
            # Try letting requests handle it
            try:
                data = resp.json()
            except Exception as json_err:
                print(f"  [BigBasket] JSON error: {json_err}")
                print(f"  [BigBasket] Raw bytes preview: {resp.content[:100]}")
                return []
        print(f"  [BigBasket] Keys: {list(data.keys())[:8]}")

        products = []
        for tab in data.get("tabs", []):
            for p in tab.get("product_info", {}).get("products", []):
                item = _parse_bb_product(p)
                if item: products.append(item)

        if not products and data.get("tabs"):
            sample = data["tabs"][0].get("product_info",{}).get("products",[])
            if sample:
                print(f"  [BigBasket] Still 0 — pricing sample: {json.dumps(sample[0].get('pricing',{}))[:300]}")

        return _dedup(products, "BigBasket")
    except Exception as e:
        print(f"  [BigBasket] Error: {e}"); return []


def _parse_bb_product(p):
    """
    BigBasket listing-svc v2 — confirmed field paths from terminal debug:
      desc              — product name
      w                 — unit/weight e.g. "1 pc"
      absolute_url      — product page path e.g. "/pd/40347607/cosco-..."
      pricing.offer_price.dsc  — selling price (discounted)
      pricing.prd_pr           — MRP
      images[0].m or images[0].s — image URL
    """
    name = p.get("desc", p.get("name", ""))
    unit = p.get("w", p.get("pack_desc", ""))

    # Pricing — confirmed key is pricing{}
    pricing = p.get("pricing", {})

    # Confirmed from debug:
    # pricing.discount.prim_price.sp  = selling price e.g. "299"
    # pricing.discount.mrp            = MRP e.g. "999"
    discount_obj = pricing.get("discount", {})
    price = (discount_obj.get("prim_price", {}).get("sp")
             or discount_obj.get("sp")
             or pricing.get("sp")
             or p.get("sp", 0))
    mrp   = (discount_obj.get("mrp")
             or pricing.get("mrp")
             or p.get("mrp", price))

    # Images
    img = ""
    images = p.get("images", [])
    if images and isinstance(images[0], dict):
        img = (images[0].get("m") or images[0].get("s")
               or images[0].get("l") or images[0].get("url") or "")
    elif images and isinstance(images[0], str):
        img = images[0]
    if img and not img.startswith("http"):
        img = "https://www.bbassets.com/media/uploads/p/l/" + img.lstrip("/")

    # URL — absolute_url is the full path confirmed from debug
    abs_url = p.get("absolute_url", "")
    url = f"https://www.bigbasket.com{abs_url}" if abs_url else "https://www.bigbasket.com"

    try:
        price = int(float(str(price).replace(",", "")))
        mrp   = int(float(str(mrp  ).replace(",", "")))
    except:
        return None

    if not name or price < 5: return None
    if not mrp or mrp < price: mrp = price

    return {
        "platform": "BigBasket", "name": name, "unit": str(unit),
        "image": img, "price": price, "mrp": mrp, "url": url,
        "discount": round((1 - price/mrp)*100) if mrp > price else 0,
    }

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    lat   = float(request.args.get("lat", 28.465204))
    lon   = float(request.args.get("lon", 77.06159))
    if not query: return jsonify({"error": "No query"}), 400

    print(f"\n{'='*50}\nSEARCH: '{query}' @ ({lat}, {lon})\n{'='*50}")

    results = {"blinkit": [], "zepto": [], "jiomart": [], "bigbasket": []}

    def run(key, fn): results[key] = fn(query, lat, lon)

    threads = [
        threading.Thread(target=run, args=("blinkit", fetch_blinkit)),
        threading.Thread(target=run, args=("zepto",   fetch_zepto)),
        threading.Thread(target=run, args=("jiomart",   fetch_jiomart)),
        threading.Thread(target=run, args=("bigbasket", fetch_bigbasket)),
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    blinkit   = sorted(results["blinkit"],   key=lambda x: x["price"])
    zepto     = sorted(results["zepto"],     key=lambda x: x["price"])
    jiomart   = sorted(results["jiomart"],   key=lambda x: x["price"])
    bigbasket = sorted(results["bigbasket"], key=lambda x: x["price"])
    all_p     = sorted(blinkit + zepto + jiomart + bigbasket, key=lambda x: x["price"])

    print(f"\nRESULT → Blinkit={len(blinkit)}, Zepto={len(zepto)}, JioMart={len(jiomart)}, BigBasket={len(bigbasket)}")

    return jsonify({
        "query":     query,
        "blinkit":   blinkit[:8],
        "zepto":     zepto[:8],
        "jiomart":   jiomart[:8],
        "bigbasket": bigbasket[:8],
        "cheapest":  all_p[:5],
        "count": {"blinkit": len(blinkit), "zepto": len(zepto), "jiomart": len(jiomart), "bigbasket": len(bigbasket)},
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("🚀 QuickCart — Blinkit · Zepto · JioMart · BigBasket → http://localhost:5000")
    app.run(debug=False, port=5000)