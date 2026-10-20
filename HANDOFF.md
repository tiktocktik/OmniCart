# Handoff

## Completed

### M0 - Setup and hygiene
- Pinned dependencies, fixed README startup, removed the tracked DB and dead tables.
- Env-driven paths and secrets; no `CERT_NONE`; stable `hashlib` IDs.
- Frontend backend URL is centralised in `src/lib/api.ts`.

### M1 - Truthful data
- Removed all hard-coded demo products and fabricated defaults.
- Amazon robot-check detection; explicit `status="unavailable"` results.
- Verified history only; no estimated charts.
- Verified coupons only; no invented bank offers.
- Personal card portfolio removed.
- Frontend and Deals page now show real error/unavailable states.

### M2 - Input understanding and search
- Text input is a search query, not a link-only error. The UI calls `/search`
  and shows a pick-a-result list; a link or ASIN goes to `/resolve`.
- Hostname-based URL detection with exact/suffix matching. Lookalikes such as
  `notamazon.in` are Universal, not Amazon.
- Short links (`amzn.to`, `dl.flipkart.com`, `fkrt.it`, `fkrt.co`) are expanded
  once. An invalid link that redirects to a homepage is `SHORT_LINK`, not a
  product. The original short URL is kept for the Open-store link.
- Search results are filtered for relevance. A nonsense query now returns an
  explicit `status="empty"` instead of a fuzzy, unrelated product.
- `?q=` deep links auto-run the search and remove the query from the URL. The
  Deals page uses this for Find Product.
- Deals -> Find Product searches the deal title instead of resolving the
  aggregator post, which could never contain a live product price. The primary
  deal action is now Open Deal, which opens the aggregator post directly.
- Flipkart product pages return real JSON-LD rating, ratings count, shipping
  rate and struck-through MRP where present. Missing fields stay null.
- Deals data cleaned up: no `x1.35` fake MRP, no forced 10-15% discounts, no
  fake "Live"/"Recent" timestamps, no "Online" store placeholder, corrected
  category inference, duplicate cards removed, and softened "verified/live"
  wording. The strikethrough MRP and "Save" line are hidden when the source
  does not provide a real higher price.
- `GET /search?q=` accepts an empty query with an explicit empty state instead
  of a 422. The UI also guards empty input.

### M2 fix 2 - deal cards open the retailer product page
- Deal cards no longer open the third-party deal post. The image, title and
  primary **Open Product** action go through the backend
  `GET /deals/go?url=...`, which resolves the deal post's outbound link and
  returns a `302` to the actual retailer product page.
- DesiDime: `visit.desidime.com/visit/...` is followed to Flipkart/Myntra/etc.
  Dealsmagnet: the page's `buy-button[data-code]` is followed through
  `/buy?...` to Amazon/Flipkart/etc.
- Product URLs are canonicalised: Amazon becomes
  `https://www.amazon.in/dp/<ASIN>` and Flipkart tracking/affiliate parameters
  (`affid`, `affExtParam1`, `affExtParam2`, `utm_*`) are removed.
- Only DesiDime/Dealsmagnet posts and known retailer hosts are accepted, so the
  endpoint is not an open URL proxy. Successful resolutions are cached for 6
  hours; failures are cached for 60 seconds to avoid hammering a dead post.
- If a deal post cannot be resolved, the new tab shows an explicit **Product
  page unavailable** page with the deal-post fallback. It never silently opens
  the aggregator.
- Main-page **Community Price Drops** and `/deals` both use the same helper
  (`dealProductHref` in `src/lib/api.ts`).

### M2 fix - deal targets and unavailable product shell (`7bb2b0b`)
- Deal cards on `/` and `/deals` open the real `deal.url` in a new tab. The
  text search is a separate, clearly labelled **Find Product** action, so a deal
  click can never fall through to the `/resolve` text-input error.
- A pasted product URL that resolves to `status="unavailable"` keeps the product
  page shell. The display title is derived from the original URL slug (for the
  reported Amazon URL: `CHKOKKO Sleeveless Running Workout Onion`), and the UI
  says the title came from the link.
- Unavailable products show **STORE PAGE UNAVAILABLE**, **Live price
  unavailable**, **Open Store**, and explicit empty states for image,
  comparison, price history, sellers, coupons/payment offers, and
  specifications. Add to Cart / Fast Checkout are hidden, and the history tab
  never claims an estimated trajectory or synced-card portfolio.

## Verified

Environment: Windows, local backend `http://127.0.0.1:8000`, frontend
`http://127.0.0.1:3000` (production build).

Commands:
- `python -m pytest -q` -> 29 passed, 3 skipped (the 3 are opt-in fixtures).
  New offline tests cover DesiDime/Dealsmagnet outbound extraction, Amazon
  canonicalisation, Flipkart tracking removal and non-retailer rejection.
- `npx tsc --noEmit` -> no errors.
- `npm run build` -> compiled successfully; static routes `/`, `/_not-found`,
  `/deals`.

API:
- `/health` -> 200.
- `/resolve?query=not a product` -> 400 (text is not a URL).
- `/resolve?query=https://not-a-real-store.example/product/abc` -> 200,
  `status="unavailable"`, `title=""`, explicit "Could not read..." message.
- `/resolve?query=https://amzn.to/3abcDEF` -> 200, `status="unavailable"`,
  `platform="Short link"`, `canonical_url` is the original short link, and the
  message asks for the final product URL. The link redirected to the Amazon
  homepage; it is never shown as a product.
- `/search?q=` -> 200, `status="empty"`, "Type a product name to search."
- `/search?q=zzzqqq nonexistent gadget xyz` -> 200, `status="empty"`, 0
  results. Before the relevance filter this returned a cigarette lighter.
- `/search?q=sony wh-1000xm5` -> 200, `status="ok"`, 5 Flipkart results
  (XM5/XM6/XM4/WF-1000XM5) with real prices. Amazon was blocked, so the partial
  source note is shown.
- `/resolve` for the Flipkart XM5 URL -> `status="ok"`, live price 19,989,
  MRP 34,990, rating 4.5, 831 ratings, delivery charge 0, all-time low/high
  null, history `UNAVAILABLE`.
- `/deals?limit=50` -> 38 deals, 0 duplicate IDs, corrected categories
  (Home & Kitchen for cookers/toasters/cleaners, Fashion for watches), real
  MRPs where the source card has one, no fake timestamps, store fallback is the
  aggregator name.
- `/deals/go?url=<DesiDime Mokobara post>` -> `302` to
  `https://www.flipkart.com/mokobara-grey-sling-bag-transit-cross-body-2-0/p/itm3eb6766f8797c`
  (no `affid`/`affExtParam`).
- `/deals/go?url=<Dealsmagnet Titan Raga post>` -> `302` to
  `https://www.amazon.in/dp/B0CLRD5HWT` (no `tag`/`ascsubtag`).
- `/deals/go?url=https://example.com/product` -> `404` HTML
  **Product page unavailable**, with the deal-post fallback; no redirect.
- `/resolve` for the reported Amazon URL
  `.../CHKOKKO-Sleeveless-Running-Workout-Onion/dp/B0GTMLSNR4` -> 200,
  `status="unavailable"`, `title=""`, canonical
  `https://www.amazon.in/dp/B0GTMLSNR4`, message "Amazon returned a robot-check
  page instead of the product. Try again later or open the store directly.",
  0 sellers/competitors/coupons/payment options, `historySource="UNAVAILABLE"`,
  badge `VERIFY ON STORE`.

UI (Playwright):
- Text search for `sony wh-1000xm5` shows the candidate list. Selecting the XM5
  renders real 19,989 / 34,990 / 43% OFF / 4.5 (831) / FREE Delivery and
  "NO HISTORY", with no fabricated all-time low/high.
- A nonsense query shows "No relevant products found ... Try a more specific
  name, or paste a product link."
- Backend stopped: the page shows "Could not reach the OmniCart backend at
  http://127.0.0.1:8000. Start the backend and try again."
- Deals -> Find Product for the Morphy Richards toaster lands on a real Flipkart
  candidate list, not the aggregator page.
- `/?q=sony%20wh-1000xm5` auto-runs the search and cleans the URL.
- Pasting the reported Amazon URL into the production build keeps the product
  shell: "CHKOKKO Sleeveless Running Workout Onion" from the link, "No image
  from store", "STORE PAGE UNAVAILABLE", "Live price unavailable", **Open
  Store**, and all five tabs. Comparison: "No Alternatives Available". History:
  "NO VERIFIED HISTORY" / "No verified price history yet". Sellers, Smart
  Stack, payment offers and specs show explicit unavailable empty states.
- `/deals` loaded 38 deals. The card image/title and **Open Product** opened the
  backend resolver link. The Dealsmagnet Titan Raga card landed on
  `https://www.amazon.in/dp/B0CLRD5HWT`; the DesiDime Mokobara card landed on
  the Flipkart product page, not the aggregator. **Find Product** remains a
  separate text-search action.
- A main-page **Community Price Drops** Royaloak card opened
  `https://www.amazon.in/dp/B0DB5D7BLV` in a new tab.

## Known limitations

- Amazon frequently serves robot-check pages on this network; the honest result
  is `status="unavailable"` with an Open-store link. Amazon search is often
  blocked, so Flipkart-only results appear with a partial-source note.
- Deals are public aggregator posts (DesiDime/Dealsmagnet), not store listings.
  The category is inferred from the title, prices come from the post, and
  availability can change. **Open Product** resolves the post to the retailer;
  confirm the price/availability on the store.
- Some DesiDime outbound links are already dead (HTTP 500/404) or hit a
  certificate error. Those show **Product page unavailable** with an explicit
  deal-post fallback instead of opening the aggregator automatically.
- The resolver strips the source aggregator's affiliate parameters when it
  canonicalises the product URL. That keeps the product link clean, but it also
  means DesiDime/Dealsmagnet do not earn from these clicks. Use direct retailer
  feeds or an approved affiliate network if monetising; do not silently replace
  another publisher's attribution.
- A text search can still show "Some sources could not be read; showing the
  readable results" when one search source is blocked. That is the search path,
  not a deal click; deal clicks go through `/deals/go`.
- No verified price history source is connected yet, so the UI shows
  "NO HISTORY" and hides all-time low/high.
- Flipkart's XM5 page shows 42% off; OmniCart computes 43% from 19,989 against
  34,990. The difference is rounding, not invented data.
- Live Amazon product verification remains blocked by robot checks. The
  Flipkart page is the current live-product evidence.

## Next

M3 - speed and robustness:
- Remove the deal scrape from `/resolve`; refresh deals in the background with a lock.
- Run independent fetches in parallel under one total deadline.
- Add a per-URL TTL cache.
- Frontend: `AbortController`, request IDs to ignore stale responses, a 15 s timeout.
- Split `page.tsx`, memoize chart data, keep search input state local.

M4 - tests and CI:
- Offline pytest with saved HTML fixtures.
- Playwright E2E for Amazon, Flipkart, text search, bad input, backend down,
  Deals -> Open Deal / Find Product, and the unavailable product shell.
- GitHub Actions on a clean clone.
