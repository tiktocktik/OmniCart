# 🛒 OmniCart

India's product price inspector. Paste a product link or an Amazon ASIN and OmniCart reads the live price, shows verified price history when a real source exists, and tells you clearly when a store cannot be read. It never substitutes a different product or a made-up number.

## 🧱 Structure

| Path | What it is |
|---|---|
| `omnicart-backend/` | FastAPI backend — link parsing, live scraping, verified history, deal detection |
| `omnicart-app/` | Next.js 16 frontend — product inspector and live Deals page |

## ✨ Key Features

- **Link resolver** — strips affiliate/tracking parameters and resolves Amazon.in, Flipkart, Myntra, Ajio and more to clean product IDs.
- **Honest live data** — every price, rating and image comes from the store page. Missing fields stay empty instead of being invented.
- **Explicit unavailable states** — if a store blocks the request or exposes no price, the UI says so and links to the store. No substitute products.
- **Verified history only** — price charts appear only when a real history source returns data; otherwise the UI says history is unavailable.
- **Verified coupons only** — only promo codes actually found on the store page are shown. No invented bank offers or success rates.
- **Live Deals & Flash-Glitch Engine** — community deal feeds with tiered drop detection.
- **Social ingestion** — optional connectors for Reddit, X/Twitter and Telegram deal channels.

## 🚀 Quick Start

### One-click start (Windows)
Double-click `start.bat` in the project root. It starts the backend and
frontend, waits until both are ready, and opens http://localhost:3000.
Use `start.bat prod` to build and run the production server.

### Backend (FastAPI — port 8000)
```bash
cd omnicart-backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app
```

### Frontend (Next.js — port 3000)
```bash
cd omnicart-app
npm install
copy .env.example .env.local
npm run dev
```

Then open:
- Inspector → http://localhost:3000
- Deals page → http://localhost:3000/deals

## ⚙️ Configuration

Backend: copy `omnicart-backend/.env.example` to `omnicart-backend/.env` and fill in any credentials you need (Reddit OAuth, X/Twitter session, Telegram MTProto). Everything runs without them; social streaming stays off.

Frontend: copy `omnicart-app/.env.example` to `.env.local`. Set `NEXT_PUBLIC_API_BASE` if the backend is not at `http://127.0.0.1:8000`.

Optional backend settings:

| Variable | Purpose |
|---|---|
| `PRICE_AGGREGATOR_DIR` | Path to a sibling PriceAggregator checkout. Required only for its tests. |
| `PRICEHISTORY_SECRET` | Signing secret for the price-history API. Without it, history is reported as unavailable. |
| `OMNICART_ALLOW_FIXTURES` | Set to `1` in tests to allow replay fixtures. Off by default. |

## 🛠 Tech Stack

- **Backend:** Python, FastAPI, BeautifulSoup, urllib
- **Frontend:** Next.js 16, React, TypeScript, Tailwind CSS
