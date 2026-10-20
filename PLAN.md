# OmniCart plan

Rules: one milestone at a time. Verify with real inputs. Commit only when the
acceptance checks pass. Never fill a missing value with a plausible guess.

## M0 - Setup and hygiene (done)

- Pinned `requirements.txt`.
- Removed `--reload` from the README.
- Removed the tracked `omnicart.db` and ignored local databases.
- Removed `init_db()` and the unused `price_history` / `coupons_cache` tables.
- Replaced hard-coded `D:/...` paths with `PRICE_AGGREGATOR_DIR`.
- Moved the price-history signing secret to `PRICEHISTORY_SECRET`.
- Removed `ssl.CERT_NONE`.
- Centralised the frontend backend URL in `src/lib/api.ts` (`NEXT_PUBLIC_API_BASE`).
- Replaced Python `hash()` IDs with `hashlib`.

Acceptance: backend imports, `/health` returns 200, `npm run build` passes.

## M1 - Truthful data (done)

- Deleted the hard-coded Tata olive oil, Pigeon air fryer and Sony XM5 products.
- Deleted the 449/699 Amazon price fallbacks and the `live_price * 1.25` fake MRP.
- Added Amazon robot-check / captcha detection.
- Removed fabricated ratings, review counts, sellers, categories, images and
  highlights from both scrapers.
- Removed estimated price histories. History is now `UNAVAILABLE` unless a real
  source returns data.
- Removed invented coupons and success rates. Only coupons scraped from the
  product page are returned.
- Removed the personal card portfolio. Payment stacking returns no options
  unless a real offer exists.
- Removed demo slugs from the history resolver.
- Removed quick-commerce fixtures from production; they require
  `OMNICART_ALLOW_FIXTURES=1` and are test-only.
- Frontend now shows an explicit error/unavailable banner with an Open-store
  link instead of silently showing a sample product.
- Deals page now shows a real error with Retry when the backend is down.
- README updated to match the actual behaviour.

Acceptance: a blocked Amazon request returns `status="unavailable"` and never a
made-up price; text input returns HTTP 400; `tsc` and `next build` pass.

## M2 - Understanding input and search (done)

- ASIN is accepted only if it matches `^B0[A-Z0-9]{8}$`.
- URLs are detected from the parsed hostname, with exact/suffix host matching.
  Lookalikes such as `notamazon.in` stay Universal.
- `amzn.to`, `dl.flipkart.com`, `fkrt.it` and `fkrt.co` are expanded once. An
  expired or invalid short link that lands on a store homepage is reported as
  `SHORT_LINK`; it is never treated as a product.
- `GET /search?q=` returns live Amazon/Flipkart candidates. The UI shows a
  pick-a-result list with the real platform, title, price and image.
- Results must share at least one meaningful query token with the title, so a
  nonsense query returns `status="empty"` instead of an unrelated product.
- `?q=` is read on page load. Deals -> Stack & Buy searches the product title
  and cleans the URL after the search starts.
- Flipkart product fetching returns real JSON-LD rating, shipping and MRP where
  present. Unknown fields stay null and are hidden in the UI.
- Deals honesty: no invented MRP, no forced 10-15% discounts, no fake
  Live/Recent timestamps, no "Online" store placeholder, corrected category
  inference, duplicate cards removed, and softened "verified/live" wording.
- Offline tests cover the classifier, short-link product validation, search
  relevance, Flipkart price parsing and deal categorisation.

Acceptance: a text query opens a candidate list; a bad query returns an
explicit empty state; an invalid short link returns `SHORT_LINK`; a Flipkart
link returns the real price/MRP/rating; blocked stores return `unavailable`;
`pytest`, `tsc` and `next build` pass.

## M3 - Speed and robustness (next)

- Remove the deal scrape from `/resolve`; refresh deals in the background with a lock.
- Run independent fetches in parallel under one total deadline.
- Add a per-URL TTL cache.
- Frontend: `AbortController`, request IDs to ignore stale responses, a 15 s timeout.
- Split `page.tsx`, memoize chart data, keep search input state local.

## M4 - Tests and CI

- Offline pytest suite with saved HTML fixtures (Amazon product, robot check, Myntra).
- Playwright E2E: Amazon link, Flipkart link, text search, bad input, backend down,
  Deals -> Stack & Buy.
- GitHub Actions on a clean clone.
