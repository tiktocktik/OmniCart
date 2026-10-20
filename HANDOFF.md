# Handoff

## Completed

### M0 — Setup and hygiene
- Pinned dependencies, fixed README startup, removed tracked DB and dead tables.
- Env-driven paths and secrets; no `CERT_NONE`; stable `hashlib` IDs.
- Frontend backend URL is centralised in `src/lib/api.ts`.

### M1 — Truthful data
- Removed all hard-coded demo products and fabricated defaults.
- Amazon robot-check detection; explicit `status="unavailable"` results.
- Verified history only; no estimated charts.
- Verified coupons only; no invented bank offers.
- Personal card portfolio removed.
- Frontend and Deals page now show real error/unavailable states.

## Verified

Commands run in `D:\Workspace\Projects\OmniCart`:

- `python -c "import app.main; ..."` → backend imports OK.
- `python -m pytest -q` → 3 skipped (the fixture tests are opt-in).
- `npx tsc --noEmit` → no errors.
- `npm run build` → compiled successfully, 3 static routes.
- FastAPI TestClient:
  - `/health` → `200 {"status":"ok",...}`
  - `/resolve?query=iphone 15` → `400` with a link-only message.
  - `/resolve?query=https://www.amazon.in/dp/B0TEST1234` → `200`,
    `status="unavailable"`, `live_price=0.0`, message: Amazon returned a
    robot-check page. This is the intended honest outcome.

Offline resolver checks (mocked sources):
- blocked Amazon → `unavailable`, price 0.
- successful Amazon → real title/price, rating 0 (not invented), history
  `UNAVAILABLE`, no sellers, no fake image.
- blocked Croma → `unavailable`, price 0.

## Not verified

- A real live Amazon product with a readable price from this network (Amazon
  served a robot check, which is expected).
- Flipkart product fetching (not implemented; planned for M2).
- Browser E2E flows (planned for M4).
- A fresh-venv install from PyPI (packages are already installed here).

## Next

M2 — input understanding:
- ASIN regex `^B0[A-Z0-9]{8}$`.
- Hostname-based URL detection.
- Short-link expansion.
- `/search?q=` with a pick-a-result UI.
- `?q=` handling for the Deals handoff.
- Flipkart fetcher or explicit unsupported state.
- Offline classifier tests.
