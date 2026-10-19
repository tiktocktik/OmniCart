# OmniCart - Agent & Developer Guide

## 1. Stack & Architecture
- **Backend**: FastAPI (Python 3.14), Uvicorn, SQLite (`omnicart.db` with WAL mode enabled).
- **Frontend**: Next.js 16.4.2 (App Router, Turbopack, React 19, Tailwind CSS).
- **Port Allocations**:
  - Backend: `http://127.0.0.1:8000`
  - Frontend: `http://localhost:3000`

## 2. Dev & Test Commands
- **Start Backend**:
  ```powershell
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```
  *(Never use `--reload` inside background agent tasks on Windows)*
- **Start Frontend**:
  ```powershell
  cd omnicart-app; npm run dev
  ```
- **Backend Health Check**:
  ```powershell
  curl http://127.0.0.1:8000/health
  ```

## 3. Data Ingestion & Scraper Guidelines
- Prefer structured data in pages (`JSON-LD`, `__NEXT_DATA__`, embedded JSON) before falling back to regex or raw HTML.
- Entity resolution constraint: normalized quantity & unit (e.g. 500g vs 1kg) is a hard filter, not a fuzzy feature.
- Use atomic commits per feature milestone.

## 4. Current Milestone & Plan
- Reference: `PLAN.md`
- Active acceptance check: `curl http://127.0.0.1:8000/deals?limit=5`
