"""Product resolution pipeline.

This module deliberately does not invent product data. Every field shown to the
user comes from the live store page, from a verified history source, or is left
empty and reported through ``status`` / ``status_message``.
"""

import hashlib
import os
from typing import Optional

from .models import (
    ProductResolution,
    SellerInfo,
    PurchaseOption,
    PricePrediction,
)
from .url_parser import clean_and_normalize_url
from .intelligence import (
    compute_price_prediction,
    calculate_payment_arbitrage,
    calculate_smart_stack_combination,
)
from .amazon_scraper import fetch_live_amazon_product
from .universal_scraper import fetch_live_web_product
from .competitor_engine import find_cross_platform_competitors
from .aggregator_history import fetch_real_aggregator_history
from .offers_engine import get_marketplace_offers
from .qc_pool import get_qc_pool


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha1(value.encode()).hexdigest()[:8]}"


def _unavailable(cleaned_url: str, platform: str, message: str) -> ProductResolution:
    """An explicit "we could not read this" result. Never a substitute product."""
    return ProductResolution(
        id=_stable_id("unavailable", cleaned_url or platform),
        canonical_url=cleaned_url,
        platform=platform,
        title=f"{platform} listing",
        category="",
        image_url="",
        gallery_images=[],
        rating=0.0,
        ratings_count=0,
        live_price=0.0,
        regular_price=0.0,
        all_time_low=0.0,
        all_time_high=0.0,
        prediction=PricePrediction(
            badge="VERIFY ON STORE",
            detail=message,
            drop_likelihood="UNKNOWN",
            confidence=0,
        ),
        history={},
        sellers=[],
        coupons=[],
        payment_options=[],
        status="unavailable",
        status_message=message,
        history_source="UNAVAILABLE",
        history_data_points=0,
    )


def _optional_fixtures():
    """Quick-commerce fixtures are test-only and must be opted into explicitly."""
    if os.environ.get("OMNICART_ALLOW_FIXTURES") != "1":
        return []
    try:
        return get_qc_pool().get_fixture_listings()
    except Exception:
        return []


def _verified_history(cleaned_url, live_price, regular_price):
    try:
        real = fetch_real_aggregator_history(cleaned_url)
    except Exception:
        real = None

    if not real:
        # No verified history. Do not synthesize a trajectory.
        return {}, live_price, regular_price, "UNAVAILABLE", 0

    return (
        real.get("history") or {},
        float(real.get("all_time_low") or live_price),
        float(real.get("all_time_high") or regular_price),
        real.get("history_source") or "VERIFIED_AGGREGATOR",
        int(real.get("total_points") or 0),
    )


def _prediction(live_price, low, regular, source, points):
    if source == "UNAVAILABLE":
        return PricePrediction(
            badge="NO HISTORY",
            detail="Live price loaded. No verified price history is available for this product yet.",
            drop_likelihood="UNKNOWN",
            confidence=0,
        )
    return compute_price_prediction(live_price, low, regular, source, points)


def _competitors(title, platform, price):
    try:
        exact, similar = find_cross_platform_competitors(
            title=title or "",
            current_platform=platform,
            current_price=price,
            quick_commerce_candidates=_optional_fixtures(),
        )
        return exact or [], similar or []
    except Exception:
        # Comparison is optional; a failure must not break the main result.
        return [], []


def _build_amazon(item_id: str, cleaned_url: str, pincode: str, live: dict) -> ProductResolution:
    live_price = float(live.get("live_price") or 0.0)
    regular_price = float(live.get("regular_price") or live_price)
    history, low, high, source, points = _verified_history(
        cleaned_url, live_price, regular_price
    )
    prediction = _prediction(live_price, low, regular_price, source, points)
    delivery = live.get("delivery_promise") or "Delivery estimate unavailable"

    sellers = []
    seller_name = live.get("seller_name")
    if seller_name:
        sellers.append(
            SellerInfo(
                id=f"amz-{item_id}",
                name=seller_name,
                price=live_price,
                rating=float(live.get("rating") or 0.0),
                reviews_count=int(live.get("ratings_count") or 0),
                delivery_days=delivery,
                delivery_charge=0.0 if live_price >= 499 else 40.0,
                badge="Amazon",
                is_best_seller=True,
                score=100,
                store_url=cleaned_url,
            )
        )

    coupons = get_marketplace_offers(
        "Amazon.in", live_price, live.get("category") or "", live.get("coupons") or []
    )
    payment_options = calculate_payment_arbitrage(
        live_price, "Amazon.in", live.get("category") or "", bank_offers=coupons
    )
    smart_stack = calculate_smart_stack_combination(
        live_price, coupons, payment_options
    )
    exact, similar = _competitors(live.get("title") or "", "Amazon.in", live_price)

    drop = 0.0
    if regular_price > 0:
        drop = round(((regular_price - live_price) / regular_price) * 100, 1)

    return ProductResolution(
        id=f"amazon-{item_id}",
        canonical_url=cleaned_url,
        platform="Amazon.in",
        title=live.get("title") or f"Amazon listing ({item_id})",
        category=live.get("category") or "",
        image_url=live.get("image_url") or "",
        gallery_images=live.get("gallery_images") or [],
        rating=float(live.get("rating") or 0.0),
        ratings_count=int(live.get("ratings_count") or 0),
        live_price=live_price,
        regular_price=regular_price,
        all_time_low=low,
        all_time_high=high,
        prediction=prediction,
        history=history,
        history_source=source,
        history_data_points=points,
        sellers=sellers,
        competitors=exact,
        similar_styles=similar,
        purchase_options=[
            PurchaseOption(**o) for o in (live.get("purchase_options") or [])
        ],
        specifications=live.get("specifications") or {},
        highlights=live.get("highlights") or [],
        coupons=coupons,
        pincode=pincode,
        pincode_delivery_status=delivery,
        delivery_charge=0.0 if live_price >= 499 else 40.0,
        payment_options=payment_options,
        smart_stack=smart_stack,
        is_loot_deal=drop >= 50.0,
        loot_drop_percentage=drop,
        status="ok",
    )


def _build_web(cleaned_url: str, platform: str, pincode: str, live: dict) -> ProductResolution:
    live_price = float(live.get("live_price") or 0.0)
    regular_price = float(live.get("regular_price") or live_price)
    history, low, high, source, points = _verified_history(
        cleaned_url, live_price, regular_price
    )
    prediction = _prediction(live_price, low, regular_price, source, points)
    store = live.get("platform") or platform
    delivery = live.get("delivery_promise") or "Delivery estimate unavailable"

    sellers = []
    seller_name = live.get("seller_name")
    if seller_name:
        sellers.append(
            SellerInfo(
                id=_stable_id("seller", cleaned_url),
                name=seller_name,
                price=live_price,
                rating=float(live.get("rating") or 0.0),
                reviews_count=int(live.get("ratings_count") or 0),
                delivery_days=delivery,
                delivery_charge=0.0 if live_price >= 499 else 40.0,
                badge=store,
                is_best_seller=True,
                score=100,
                store_url=cleaned_url,
            )
        )

    coupons = get_marketplace_offers(
        store, live_price, live.get("category") or "", live.get("coupons") or []
    )
    payment_options = calculate_payment_arbitrage(
        live_price, store, live.get("category") or "", bank_offers=coupons
    )
    smart_stack = calculate_smart_stack_combination(
        live_price, coupons, payment_options
    )
    exact, similar = _competitors(live.get("title") or "", store, live_price)

    drop = 0.0
    if regular_price > 0:
        drop = round(((regular_price - live_price) / regular_price) * 100, 1)

    return ProductResolution(
        id=_stable_id("web", cleaned_url),
        canonical_url=cleaned_url,
        platform=store,
        title=live.get("title") or f"{store} listing",
        category=live.get("category") or "",
        image_url=live.get("image_url") or "",
        gallery_images=live.get("gallery_images") or [],
        rating=float(live.get("rating") or 0.0),
        ratings_count=int(live.get("ratings_count") or 0),
        live_price=live_price,
        regular_price=regular_price,
        all_time_low=low,
        all_time_high=high,
        prediction=prediction,
        history=history,
        history_source=source,
        history_data_points=points,
        sellers=sellers,
        competitors=exact,
        similar_styles=similar,
        purchase_options=[
            PurchaseOption(**o) for o in (live.get("purchase_options") or [])
        ],
        specifications=live.get("specifications") or {},
        highlights=live.get("highlights") or [],
        coupons=coupons,
        pincode=pincode,
        pincode_delivery_status=delivery,
        delivery_charge=0.0 if live_price >= 499 else 40.0,
        payment_options=payment_options,
        smart_stack=smart_stack,
        is_loot_deal=drop >= 50.0,
        loot_drop_percentage=drop,
        status="ok",
    )


def resolve_product_pipeline(
    query_or_url: str, pincode: str = "110001"
) -> ProductResolution:
    """Resolve a product URL (or Amazon ASIN) to a truthful product record.

    Text search is handled separately by the /search endpoint. If the input is
    neither a link nor an ASIN, this raises ValueError and the API returns 400.
    """
    cleaned_url, platform, item_id = clean_and_normalize_url(query_or_url)

    if platform == "SEARCH_QUERY":
        raise ValueError(
            "OmniCart resolves product links. Paste a product URL or an Amazon ASIN."
        )

    if platform == "Amazon.in":
        if not item_id:
            return _unavailable(
                cleaned_url,
                "Amazon.in",
                "This Amazon link does not contain a product ID (ASIN). "
                "Open the product page and copy its link.",
            )
        live = fetch_live_amazon_product(item_id, cleaned_url, pincode)
        if not live:
            return _unavailable(
                cleaned_url,
                "Amazon.in",
                "Amazon did not return a readable product page. "
                "Open the store to check the current price.",
            )
        if live.get("status") == "unavailable":
            return _unavailable(
                cleaned_url,
                "Amazon.in",
                live.get("status_message")
                or "Amazon blocked the request or exposed no price.",
            )
        return _build_amazon(item_id, cleaned_url, pincode, live)

    live = fetch_live_web_product(cleaned_url, pincode)
    if not live:
        return _unavailable(
            cleaned_url,
            platform,
            f"Could not read this {platform} page. "
            "Open the store to check the current price.",
        )
    if live.get("status") == "unavailable":
        return _unavailable(
            cleaned_url,
            live.get("platform") or platform,
            live.get("status_message")
            or "No readable product data was found on this page.",
        )
    if not live.get("live_price"):
        return _unavailable(
            cleaned_url,
            live.get("platform") or platform,
            "No live price was found on this page. "
            "Open the store to check the current price.",
        )
    return _build_web(cleaned_url, platform, pincode, live)
