"""
debug_jiomart.py — prints JioMart API response, focusing on variants[] price fields
Run: python debug_jiomart.py
"""
import requests, json, uuid

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

QUERY = input("Product to search (default: milk): ").strip() or "milk"

headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin":  "https://www.jiomart.com",
    "referer": f"https://www.jiomart.com/search?q={QUERY}",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "cookie": "nms_mgo_city=Mumbai; nms_mgo_state_code=MH; nms_mgo_pincode=400077; _ga=GA1.1.399947505.1775226287;",
}

body = {
    "query": QUERY, "pageSize": 3,
    "branch": "projects/sr-project-jiomart-jfront-prod/locations/global/catalogs/default_catalog/branches/0",
    "canonicalFilter": JIOMART_FILTER, "filter": JIOMART_FILTER,
    "queryExpansionSpec": {"condition": "AUTO", "pinUnexpandedResults": True},
    "spellCorrectionSpec": {"mode": "AUTO"},
    "userInfo": {"userId": None},
    "variantRollupKeys": ["variantId"],
    "visitorId": "anonymous-" + str(uuid.uuid4()),
    "facetSpecs": [{"facetKey": {"key": "brands"}, "limit": 5}],
}

print(f"\n📡 Searching JioMart for '{QUERY}'...")
resp = requests.post("https://www.jiomart.com/trex/search", headers=headers, json=body, timeout=15)
print(f"Status: {resp.status_code}")

if resp.status_code != 200:
    print(f"Error: {resp.text[:400]}")
else:
    data = resp.json()
    results = data.get("results", [])
    print(f"Total results: {len(results)}")

    for i, r in enumerate(results[:3]):
        product  = r.get("product", {})
        variants = product.get("variants", [])
        variant  = variants[0] if variants else {}
        v_attrs  = variant.get("attributes", {})
        p_attrs  = product.get("attributes", {})

        print(f"\n{'='*60}")
        print(f"[{i+1}] {product.get('title')}")
        print(f"  product.priceInfo:  {product.get('priceInfo')}")
        print(f"  variant.priceInfo:  {variant.get('priceInfo')}")
        print(f"  product attrs keys: {list(p_attrs.keys())[:10]}")
        print(f"  variant attrs keys: {list(v_attrs.keys())[:10]}")
        # Show all price-related fields in variant attrs
        print(f"  --- variant price fields ---")
        for k, v in v_attrs.items():
            if any(x in k.lower() for x in ["price","mrp","sp","cost","sell","discount","amount","offer"]):
                print(f"    {k}: {v}")
        print(f"  variant.images: {variant.get('images', [])[:1]}")

    with open("jiomart_debug.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n💾 Full response → jiomart_debug.json")