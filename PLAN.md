# OmniCart plan

Rules: one milestone at a time. Verify with real inputs. Commit only when the
acceptance checks pass. Never fill a missing value with a plausible guess.

## M0 — Setup and hygiene ✅

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

## M1 — Truthful data ✅

- Deleted the hard-coded Tata olive oil, Pigeon air fryer and Sony XM5 products.
- Deleted the 449/699 Amazon price fallbacks and the `live_price * 1.25` fake MRP.
- Added Amazon robot-check / captcha detection.
- Removed fabricated ratings, review counts, sellers, categories, images and
  highlights from both scrapers.
- Removed estimated price histories. History is now `UNAVAILABLE` unless a real
  source returns data.
- Removed invented coupons and success rates. Only coupons scraped from the
  product page are returned.
- Removed the personal card portfolio. Payment arbitrage returns no options
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

## M2 — Understanding input (next)

- ASIN only if it matches `^B0[A-Z0-9]{8}$`.
- Detect URLs by parsed hostname, with exact/suffix host matching.
- Expand `amzn.to`, `dl.flipkart.com` and `fkrt.it` redirects.
- Add `GET /search?q=` returning candidates; UI lets the user pick one.
- Read `?q=` on page load so Deals → Stack & Buy works.
- Add a Flipkart fetcher or an explicit "store not supported" state.
- Offline tests for every classifier rule (positive and negative).

## M3 — Speed and robustness

- Remove the deal scrape from `/resolve`; refresh deals in the background with a lock.
- Run independent fetches in parallel under one total deadline.
- Add a per-URL TTL cache.
- Frontend: `AbortController`, request IDs to ignore stale responses, a 15 s timeout.
- Split `page.tsx`, memoize chart data, keep search input state local.

## M4 — Tests and CI

- Offline pytest suite with saved HTML fixtures (Amazon product, robot check, Myntra).
- Playwright E2E: Amazon link, Flipkart link, text search, bad input, backend down,
  Deals → Stack & Buy.
- GitHub Actions on a clean clone.
