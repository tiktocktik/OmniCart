# Comprehensive Research: Indian Price History & Cross-Store Comparison Services

## 1. Executive Summary

We conducted a deep teardown of seven prominent Indian price tracking, history, and comparison platforms:
1. **PriceHistory.app / PriceHistory.in** (India's leading consumer mobile & web price tracker)
2. **Buyhatke** (Pioneer of Indian browser price intelligence, coupon injection, and landed-cost calculation)
3. **PriceBefore** (Independent historical pricing and sale-event tracker for Amazon & Flipkart)
4. **Smartprix** (India's premier gadget/electronics specification & multi-store entity resolution engine)
5. **MySmartPrice** (Pioneer of multi-marketplace vendor price aggregation & store ranking)
6. **Flipshope** (Indian shopping assistant specializing in price drops and flash-sale automation)
7. **Keepa (India Catalog)** (The gold standard for multi-year time-series price point scraping on Amazon.in)

---

## 2. In-Depth Service Breakdown & Core Patterns

### Service 1: PriceHistory.app (`pricehistoryapp.com`)
* **Focus Retailers:** Amazon India, Flipkart, Myntra, AJIO.
* **Core Architecture:**
  - **Data Ingestion:** Rotating residential IP proxy network parsing JSON-LD (`schema.org/Product`) and DOM fallback selectors.
  - **Data Model:**
    - `all_time_low`: Absolute lowest recorded checkout price.
    - `all_time_high`: Peak recorded price (often initial MRP or post-launch baseline).
    - `current_price`: Live scrape within last 1–6 hours.
    - `average_price`: Rolling 90-day time-weighted average price.
  - **Verdict Algorithm:**
    - If `current_price <= all_time_low * 1.03` → **"STEAL DEAL / ALL-TIME LOW"**
    - If `current_price < average_price * 0.92` → **"GOOD TIME TO BUY"**
    - If `current_price >= average_price * 1.05` → **"OVERPRICED / WAIT FOR SALE"**
  - **Key Lesson for OmniCart:** Never present a raw chart without a statistical verdict comparing current price against the 90-day rolling baseline.

---

### Service 2: Buyhatke (`compare.buyhatke.com`)
* **Focus Retailers:** 100+ Indian stores (Amazon, Flipkart, Tata CliQ, Croma, Nykaa, Snapdeal).
* **Core Architecture:**
  - **Entity Matching:** Uses title attribute normalization + model code extraction (`Levenshtein distance >= 0.85`).
  - **Landed Cost Engine:**
    $$\text{Effective Final Price} = \text{Base Price} + \text{Delivery Fee} - \text{Verified Coupons} - \text{Bank Instant Discount}$$
  - **Dual Fulfillment Matrix:** Distinguishes between standard warehouse fulfillment and quick-delivery dark stores without faking non-existent services.
  - **Key Lesson for OmniCart:** Direct canonical product URLs only. Buyhatke rejects competitor entries if the link cannot resolve to an active 1:1 PDP.

---

### Service 3: PriceBefore (`pricebefore.com`)
* **Focus Retailers:** Amazon India, Flipkart.
* **Core Architecture:**
  - **Time-Series Charting:** Step-line / Area charts with discrete sale markers.
  - **Event Annotation:** Annotates major Indian sale events directly on the graph timeline:
    - *Amazon Great Indian Festival (GIF)* / *Flipkart Big Billion Days (BBD)* (September/October)
    - *Republic Day Sale* (January)
    - *Independence Day / Prime Day* (July/August)
  - **Key Lesson for OmniCart:** Interactive timeline events give instant credibility to why prices dropped or spiked in the past.

---

### Service 4: Smartprix (`smartprix.com`)
* **Focus Retailers:** Electronics, Gadgets, Appliances (Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales).
* **Entity Resolution Pipeline:**
  ```mermaid
  flowchart TD
      A["Product Title & Spec Raw Input"] --> B["Token Normalizer\n(strip fluff, standardise: 128GB, RAM, Colors)"]
      B --> C{"Check Global Identifiers\n(EAN / UPC / MPN)"}
      C -->|Found| D["Exact 1:1 Match (Confidence: 1.0)"]
      C -->|Missing| E["Candidate Search via Store APIs / Catalogs"]
      E --> F["Extract Top 3 Candidates"]
      F --> G["Similarity Scoring (Model + Brand + Specs)"]
      G --> H{"Score >= 0.85?"}
      H -->|Yes| I["Bind Direct Competitor PDP URL"]
      H -->|No| J["Declare No Verified Competitor"]
  ```
* **Key Lesson for OmniCart:** The candidate search must probe actual competitor endpoints and filter them through a strict similarity threshold ($\ge 0.85$). If no candidate passes, declare single-store exclusivity rather than inventing fake entries.

---

### Service 5: MySmartPrice (`mysmartprice.com`)
* **Core Strengths:**
  - Ranking stores by **True In-Hand Price**: Base Price + Shipping Fee - Instant Bank Discount.
  - Explicit stock flags: `In Stock`, `Temporarily Out of Stock`, `Pre-Order`.
  - Displaying authorized brand sellers (e.g. *Appario Retail*, *Cocoblu*, *RetailNet*, *Official Brand Store*) vs unverified third parties.

---

### Service 6: Flipshope (`flipshope.com`)
* **Core Strengths:**
  - Auto-applied verified coupon engine for Indian stores.
  - Tracking hidden seller delivery thresholds (e.g. free delivery on orders above ₹499 on Amazon vs ₹500 on Flipkart).

---

### Service 7: Keepa India (Amazon.in)
* **Core Strengths:**
  - Multi-year continuous price curves.
  - Tracks 3 distinct Amazon price curves simultaneously:
    1. **Amazon Direct** (Sold & Shipped by Amazon)
    2. **3rd Party New** (Marketplace sellers)
    3. **Lightning Deals / Prime Exclusive**

---

## 3. The Unified OmniCart Architecture

Synthesizing the best practices of these 7 Indian engines:

| Feature | Best Pattern from Research | OmniCart Implementation |
|---|---|---|
| **Price Curve** | Keepa + PriceHistory.app | Multi-year historical curve with 1M, 6M, 1Y, 3Y, ALL toggles + statistical ATL/ATH |
| **Deal Verdict** | PriceHistory.app | AI verdict comparing live price with 90-day rolling average & ATL threshold |
| **Entity Resolution** | Smartprix | Strict 4-step pipeline: Token normalization → Hard Identifier / Model match → Score $\ge 0.85$ → Direct PDP URL |
| **Landed Cost** | Buyhatke | Base Price + Shipping Fee - Active Coupons - Synced Card Arbitrage (HSBC, SBI, ICICI, Tata Neu) |
| **Exclusivity** | Smartprix / Google Shopping | Flagship in-house catalog detection for fast fashion & private labels (Max, Westside, Zara) |
| **Verification Gate** | Zero-Hallucination Policy | Never create fake search-result links; never guess fulfillment channels without DOM proof |

---

## 4. Implementation Steps

1. **Step 1: Entity Resolution Engine (`app/entity_matcher.py`):**
   - Clean and normalize titles (strip promo text, standardise storage/color/pack specs).
   - Match exact models/MPNs for electronics and standard FMCG.
   - For fast-fashion proprietary SKUs (Max, Westside, Zara), classify as **Flagship Single-Store Exclusive**.

2. **Step 2: Dynamic Multi-Store Search (`app/competitor_engine.py`):**
   - Query candidate stores (Amazon India, Flipkart, Croma, Blinkit) for multi-platform products.
   - Calculate similarity score.
   - Only return items with direct canonical PDP URLs and live prices.

3. **Step 3: Frontend Dynamic Landed-Cost Card (`src/app/page.tsx`):**
   - Render verified competitor rows with: Direct Store Link, Live Price, Shipping Fee, and Net Effective Price with your synced credit cards.
