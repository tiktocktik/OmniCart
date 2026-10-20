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
  Deals page uses this for Stack & Buy.
- Deals -> Stack & Buy now searches the deal title instead of resolving the
  aggregator post, which could never contain a live product price.
- Flipkart product pages return real JSON-LD rating, ratings count, shipping
  rate and struck-through MRP where present. Missing fields stay null.
- Deals data cleaned up: no `x1.35` fake MRP, no forced 10-15% discounts, no
  fake "Live"/"Recent" timestamps, no "Online" store placeholder, corrected
  category inference, duplicate cards removed, and softened "verified/live"
  wording. The strikethrough MRP and "Save" line are hidden when the source
  does not provide a real higher price.
- `GET /search?q=` accepts an empty query with an explicit empty state instead
  of a 422. The UI also guards empty input.

## Verified

Environment: Windows, local backend `http://127.0.0.1:8000`, frontend
`http://127.0.0.1:3000` (production build).

Commands:
- `python -m pytest -q` -> 23 passed, 3 skipped (the 3 are opt-in fixtures).
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
- `/deals?limit=50` -> 50 deals, 0 duplicate IDs, corrected categories
  (Home & Kitchen for cookers/toasters/cleaners, Fashion for watches), real
  MRPs where the source card has one, no fake timestamps, store fallback is the
  aggregator name.

UI (Playwright):
- Text search for `sony wh-1000xm5` shows the candidate list. Selecting the XM5
  renders real 19,989 / 34,990 / 43% OFF / 4.5 (831) / FREE Delivery and
  "NO HISTORY", with no fabricated all-time low/high.
- A nonsense query shows "No relevant products found ... Try a more specific
  name, or paste a product link."
- Backend stopped: the page shows "Could not reach the OmniCart backend at
  http://127.0.0.1:8000. Start the backend and try again."
- Deals -> Stack & Buy for the Morphy Richards toaster lands on a real Flipkart
  candidate list, not the aggregator page.
- `/?q=sony%20wh-1000xm5` auto-runs the search and cleans the URL.

## Known limitations

- Amazon frequently serves robot-check pages on this network; the honest result
  is `status="unavailable"` with an Open-store link. Amazon search is often
  blocked, so Flipkart-only results appear with a partial-source note.
- Deals are public aggregator posts (DesiDime/Dealsmagnet), not store listings.
  The category is inferred from the title, prices come from the post, and
  availability can change. "Deal Post" opens the post; confirm on the store.
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
  Deals -> Stack & Buy.
- GitHub Actions on a clean clone.
