# ⚡ QuickCart — Real-time Quick Commerce Price Comparison

A research project that compares product prices across **4 major quick commerce platforms** in India — Blinkit, Zepto, JioMart, and BigBasket — in real time.

---

## 📋 Features

- **Real-time price comparison** across 4 platforms simultaneously
- **Best Time to Buy** suggestion — analyzes discounts and availability to recommend whether to buy now or wait
- **Direct Buy links** — click to go straight to the product or search page on each platform
- **GPS location** — auto-detects your city for accurate local pricing
- **Parallel search** — all 4 platforms fetched at the same time for speed

---

## 🏗️ Architecture

```
Browser (index.html)
    │  GET /search?q=milk&lat=...&lon=...
    ▼
Flask Server (server.py) — port 5000
    │
    ├─► Blinkit   → Playwright (headless Chrome) intercepts /v1/layout/search
    ├─► Zepto     → requests POST bff-gateway.zepto.com/user-search-service/v3
    ├─► JioMart   → requests POST jiomart.com/trex/search (Google Retail API)
    └─► BigBasket → requests GET bigbasket.com/listing-svc/v2/products
    │
    ▼  sorted by price, cheapest flagged
Browser renders results
```

### Why different approaches per platform?

| Platform | Method | Reason |
|---|---|---|
| Blinkit | Playwright (real browser) | Cloudflare blocks plain HTTP requests |
| Zepto | requests library | JSON API accessible with correct headers |
| JioMart | requests library | Google Retail API format, no anti-bot |
| BigBasket | requests + session | Needs fresh session cookies per request |

---

## 🗂️ Project Structure

```
quickcart/
├── scraper/
│   ├── server.py          ← Flask backend (main file)
│   ├── requirements.txt   ← Python dependencies
│   ├── debug_blinkit.py   ← Tool used to find Blinkit API structure
│   ├── debug_zepto.py     ← Tool used to find Zepto API structure
│   ├── debug_jiomart.py   ← Tool used to find JioMart API structure
│   ├── debug_bigbasket.py ← Tool used to find BigBasket API structure
│   └── frontend/
│       └── index.html     ← Frontend (open in browser)
└── README.md
```

---

## ⚙️ Setup

### Step 1 — Install Python dependencies

```bash
cd quickcart/scraper
pip install -r requirements.txt
```

### Step 2 — Install Playwright browser

```bash
playwright install chromium
```

### Step 3 — Run the backend

```bash
python server.py
```

You should see:
```
🚀 QuickCart — Blinkit · Zepto · JioMart · BigBasket → http://localhost:5000
```

### Step 4 — Open the frontend

Double-click `frontend/index.html` or open it in your browser.
The address bar will show something like `127.0.0.1:5500/...`

---

## 🔧 How It Works

### 1. User searches a product

The browser sends a GET request to the Flask server:
```
GET http://localhost:5000/search?q=football&lat=28.46&lon=77.06
```

### 2. Flask spawns 4 parallel threads

Each thread fetches from one platform simultaneously:

```python
threads = [
    Thread(target=fetch_blinkit),
    Thread(target=fetch_zepto),
    Thread(target=fetch_jiomart),
    Thread(target=fetch_bigbasket),
]
```

### 3. Results are merged and sorted

Products from all platforms are sorted by price. The cheapest overall is flagged as the winner.

### 4. Best Time to Buy analysis

After every search, the app analyzes:
- Maximum discount available (🔥 if ≥40%)
- Price spread across platforms
- Number of platforms stocking the item
- Recommends: **Buy Now** / **Good Time** / **Consider Waiting**

### 5. JSON response sent to browser

```json
{
  "blinkit":  [...],
  "zepto":    [...],
  "jiomart":  [...],
  "bigbasket":[...],
  "cheapest": [...],
  "count":    {"blinkit": 23, "zepto": 19, ...}
}
```

---

## 🛠️ API Endpoints

| Endpoint | Description |
|---|---|
| `GET /search?q=milk&lat=...&lon=...` | Search products across all platforms |
| `GET /health` | Check if server is running |
| `GET /refresh` | Manually refresh Zepto session cookies |

---

## ⚠️ Limitations

- **Blinkit** — uses a real browser (Playwright) which takes ~5-8 seconds per search
- **Swiggy Instamart** — AWS WAF blocks even headless browsers, not implemented
- **Amazon Fresh** — renders as HTML with no clean API, not implemented
- **Cookies expire** — Zepto session cookies are automatically refreshed; BigBasket uses a fresh session per search
- **Location-dependent** — prices and availability vary by city; default is set to Mumbai

---

## 📊 Research Findings

| Platform | API Type | Anti-bot Protection | Search Speed |
|---|---|---|---|
| Blinkit | REST JSON | Cloudflare WAF | ~6s (browser) |
| Zepto | REST JSON (POST) | Session tokens | ~2s |
| JioMart | Google Retail API | Minimal | ~2s |
| BigBasket | REST JSON (GET) | CSRF + session | ~3s |

---

## 🧰 Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, Flask-CORS |
| HTTP Requests | requests library |
| Browser Automation | Playwright (Chromium) |
| Decompression | brotli |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Concurrency | Python threading |

---

## 📦 Dependencies

```
flask          — web server framework
flask-cors     — allow browser to call local API
requests       — HTTP client for API calls
playwright     — headless browser for Blinkit
brotli         — decompress BigBasket brotli responses
```

---

## 👨‍💻 Author

Second Year Engineering Research Project
