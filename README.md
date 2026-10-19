# 🛒 OmniCart

India's smart shopping cart & price-intelligence platform. Paste any product link and OmniCart compares prices across marketplaces, stacks the best coupons + bank offers, and hunts live flash deals and pricing glitches.

## 🧱 Structure

| Path | What it is |
|---|---|
| `omnicart-backend/` | FastAPI backend — URL parsing, scraping, price aggregation, deal & glitch detection |
| `omnicart-app/` | Next.js 16 frontend — product inspector and live Deals page |

## ✨ Key Features

- **Universal link resolver** — strips affiliate/tracking params and resolves Amazon.in, Flipkart, Myntra, Ajio and more to clean product IDs (ASIN, etc.).
- **Cross-marketplace comparison** — 1:1 competitor arbitrage plus historical price data (PriceBefore / BuyHatke).
- **Smart Stack** — combines store coupons, bank card discounts (HDFC/ICICI/Axis) and UPI offers.
- **Live Deals & Flash-Glitch Engine** — 5-tier detection (`⚡ 3-DIGIT DROP`, `🔥 4-DIGIT LOOT`, `🚨 MEGA DROP`) with community heat scores.
- **Hyperlocal delivery** — pincode-level promises from Zepto, Blinkit and Instamart.
- **Social ingestion** — connectors for Reddit, X/Twitter and Telegram deal channels.

## 🚀 Quick Start

### Backend (FastAPI — port 8000)
```bash
cd omnicart-backend
pip install -r requirements.txt        # (create a venv first)
uvicorn app.main:app --reload
```

### Frontend (Next.js — port 3000)
```bash
cd omnicart-app
npm install
npm run dev
```

Then open:
- Inspector → http://localhost:3000
- Deals page → http://localhost:3000/deals

## ⚙️ Configuration

Copy `omnicart-backend/.env.example` to `omnicart-backend/.env` and fill in any credentials you need (Reddit OAuth, X/Twitter session, Telegram MTProto). Everything runs without them, but social streaming stays off.

## 🛠 Tech Stack

- **Backend:** Python, FastAPI, httpx/Playwright scrapers, SQLite
- **Frontend:** Next.js 16, React, TypeScript, Tailwind CSS
