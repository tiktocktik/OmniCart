# OmniCart Development Plan & Milestone Roadmap

## Milestone 1: Universal Price Intelligence & Smart Stack (Completed)
- [x] Multi-year historical price aggregator integration (PriceBefore / BuyHatke archives).
- [x] Strict 1:1 cross-marketplace competitor arbitrage engine (Amazon, Flipkart, Myntra, Ajio, Westside, Tata).
- [x] Multi-layer discount stacking: Store coupons + instant bank card discounts (HDFC/ICICI/Axis) + UPI arbitrage.
- [x] Pincode & hyperlocal dark-store delivery promises (Zepto, Blinkit, Instamart).

## Milestone 2: Live Deals, Flash Glitches & Dedicated Deals Page (Completed)
- [x] **Real-Time Community & Algorithmic Scraper** (`deal_scraper.py`):
  - DesiDime community drops parsed directly from `.deal-card` DOM with clean titles and authentic merchant CDN images.
  - Dealsmagnet algorithmic lightning price drops extracted with calculated true discount and regular price.
  - In-memory 10-minute cache with instant `?refresh=true` force-invalidation.
- [x] **5-Tier Flash Deal & Glitch Detection Engine** (`classify_flash_deal`):
  - Digit boundary collapses: `⚡ 3-DIGIT DROP` (4-digit → < ₹1,000), `⚡ 2-DIGIT DROP` (3-digit → < ₹100), `🔥 4-DIGIT LOOT`.
  - DesiDime community thermal velocity tracking: Live heat score (`heatScore` e.g. 250°+, 1500°+) for viral glitches.
  - Anomaly discount threshold: `🚨 MEGA DROP` (≥ 70% true drop).
- [x] **Dedicated Deals Page** (`omnicart-app/src/app/deals/page.tsx`):
  - Accessible at `http://localhost:3000/deals`.
  - Client-side real-time search across deal titles, brands, and stores.
  - Filter pills for stores (Amazon, Flipkart, Online/Direct) and auto-inferred categories.
  - `⚡ Crazy Drops Only` toggle filter to view only extreme drops and pricing glitches.
  - Multi-sort (Highest Discount %, Max Savings ₹, Price: Low to High, Price: High to Low).
  - Dual action buttons: "Stack & Buy" (opens OmniCart inspector) and "Store Link" (direct external checkout).
- [x] **Elimination of Unsplash Stock Placeholders**:
  - Replaced all Unsplash fallbacks with authentic manufacturer CDN assets across `resolver.py`, `amazon_scraper.py`, `universal_scraper.py`, and `sampleData.ts`.
  - Libra 5.5L Glass Air Fryer mapped directly to authentic Amazon CDN asset `71TaUujFs6L._SL1254_.jpg` with corrected MRP (₹12,999).
- [x] **Social & Community Ingestion Framework** (`social_ingest.py`):
  - Reddit OAuth stream connector for `r/dealsindia`, `r/IndianGaming`, `r/IndianBeautyDeals`.
  - Headless Playwright X/Twitter session stream for `@deals_india`, `@indiantweeter`, `@desidimedeals`.
  - Telegram native MTProto client (`telethon`) to stream massive public channels (`@dealsmagnet`, `@LootDealsOfficial`, `@DealBeeOfficial`) bypassing Indian ISP DNS/SNI web blocks.
  - Template `.env.example` created for local credential storage without exposing passwords.

## Milestone 3: Autonomous Sniper & Notification Alerts (Upcoming)
- [ ] Read active Reddit/X/Telegram credentials from `.env` and spawn continuous background listeners.
- [ ] Telegram Bot / Desktop WebPush alerts when a verified `3-DIGIT DROP` or `75%+ GLITCH` occurs.
- [ ] User custom price alert watchlists with target price threshold notifications.
