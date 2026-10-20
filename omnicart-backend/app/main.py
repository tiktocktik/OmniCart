from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .models import ProductResolution, ResolveRequest
from .resolver import resolve_product_pipeline
from .deal_scraper import get_live_deals

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
    """Fetches real-time trending loot deals from community sources (DesiDime, Dealsmagnet)."""
    try:
        return get_live_deals(limit=limit, force_refresh=refresh)
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

