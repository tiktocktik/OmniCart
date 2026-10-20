import html

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from .models import ProductResolution, ResolveRequest
from .resolver import resolve_product_pipeline
from .search_engine import search_products
from .deal_scraper import get_live_deals, resolve_deal_product_url

app = FastAPI(
    title="OmniCart Local Intelligence API",
    version="1.0.0",
    description="Live product resolution, verified price history, and transparent unavailable states."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "mode": "local_encrypted", "version": "1.0.0"}

@app.get("/deals")
def get_deals(
    limit: int = Query(40, ge=1, le=100),
    refresh: bool = Query(False, description="Force refresh cache from sources")
):
    """Fetches community deals from public Indian aggregators (DesiDime, Dealsmagnet)."""
    try:
        return get_live_deals(limit=limit, force_refresh=refresh)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deals/go")
def go_to_deal_product(url: str = Query(..., max_length=2000, description="Deal post URL")):
    """Resolve a deal post to its retailer product page and redirect there.

    The deal feed keeps third-party post URLs as source attribution. The user
    click goes through this endpoint so the final page is the actual product,
    not the aggregator post. Only known deal hosts and retailer hosts are
    accepted (see resolve_deal_product_url).
    """
    product_url = resolve_deal_product_url(url)
    if not product_url:
        safe_deal_url = html.escape(url, quote=True)
        return HTMLResponse(
            status_code=404,
            content=(
                "<!doctype html><html><head><meta charset=\"utf-8\">"
                "<title>Product page unavailable</title></head>"
                "<body style=\"font-family: system-ui, sans-serif; max-width: 640px; "
                "margin: 60px auto; padding: 0 20px; line-height: 1.5;\">"
                "<h1>Product page unavailable</h1>"
                "<p>OmniCart could not resolve this deal to a retailer product page. "
                "The deal post is still available, or use <strong>Find Product</strong> "
                "on the Deals page.</p>"
                f"<p><a href=\"{safe_deal_url}\" rel=\"noopener noreferrer\">"
                "Open the deal post</a></p>"
                "</body></html>"
            ),
        )
    return RedirectResponse(product_url, status_code=302)

@app.get("/search")
def search(
    q: str = Query("", max_length=120, description="Product name to search"),
    limit: int = Query(8, ge=1, le=20),
):
    """Live product search. Returns candidates to pick from; never sample data."""
    if not q.strip():
        return {
            "status": "empty",
            "results": [],
            "message": "Type a product name to search.",
            "sources": {},
        }
    try:
        return search_products(q, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resolve", response_model=ProductResolution)
def resolve_get(query: str = Query(..., description="Product URL or Amazon ASIN"), pincode: str = Query("110001")):
    try:
        return resolve_product_pipeline(query, pincode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/resolve", response_model=ProductResolution)
def resolve_post(req: ResolveRequest):
    try:
        return resolve_product_pipeline(req.query_or_url, req.pincode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

