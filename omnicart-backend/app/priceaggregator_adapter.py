"""
OmniCart Adapter for pricekit & PriceAggregator.

Transforms pricekit.NormalizedListing objects (emitted by BigBasket, Swiggy,
and future providers) into OmniCart competitor candidate dictionaries and
models (CompetitorPrice).
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from pricekit import NormalizedListing, Store
from .models import CompetitorPrice


STORE_DISPLAY_NAMES = {
    Store.BBNOW: "BigBasket Now",
    Store.SWIGGY_INSTAMART: "Swiggy Instamart",
    Store.ZEPTO: "Zepto",
    Store.BLINKIT: "Blinkit",
    Store.AMAZON_IN: "Amazon.in",
    Store.FLIPKART: "Flipkart",
    Store.CROMA: "Croma",
    Store.RELIANCE_DIGITAL: "Reliance Digital",
}


def normalized_listing_to_candidate_dict(
    nl: NormalizedListing, current_price: float = 0.0
) -> Dict[str, Any]:
    """
    Transforms a NormalizedListing into the dictionary format expected by
    OmniCart's competitor_engine.
    """
    listing = nl.listing
    obs = nl.observation

    platform_name = STORE_DISPLAY_NAMES.get(
        listing.store, listing.store.value.replace("_", " ").title()
    )

    price_float = float(obs.price)
    mrp_float = float(obs.mrp) if obs.mrp is not None else price_float

    discount_text = ""
    if mrp_float > price_float:
        pct = round(((mrp_float - price_float) / mrp_float) * 100)
        discount_text = f"{pct}% OFF (MRP ₹{int(mrp_float)})"
    elif obs.unit_price:
        u = obs.unit_price
        discount_text = f"₹{u.amount}/{u.per}{u.unit}"

    delivery_fee = 0.0 if price_float >= 499 else 25.0

    return {
        "platform": platform_name,
        "title": listing.title,
        "price": price_float,
        "url": listing.url or "",
        "delivery_info": "15-25 mins (Quick Commerce)",
        "delivery_fee": delivery_fee,
        "badge": "QUICK COMMERCE",
        "discount_text": discount_text,
        "card_savings": 0.0,
        "is_exact_match": True,
        "raw_normalized": nl,
    }


def normalized_listing_to_competitor_price(
    nl: NormalizedListing, current_price: float = 0.0, match_tier: str = "exact"
) -> CompetitorPrice:
    """
    Transforms a NormalizedListing directly into OmniCart's CompetitorPrice model.
    """
    cand = normalized_listing_to_candidate_dict(nl, current_price=current_price)
    effective_price = round(
        cand["price"] + cand["delivery_fee"] - cand["card_savings"], 2
    )

    return CompetitorPrice(
        platform=cand["platform"],
        title=cand["title"],
        price=cand["price"],
        delivery_info=cand["delivery_info"],
        delivery_fee=cand["delivery_fee"],
        combined_discount_text=cand["discount_text"],
        effective_final_price=effective_price,
        store_url=cand["url"],
        is_cheaper=effective_price < current_price if current_price > 0 else False,
        badge=cand["badge"],
        match_tier=match_tier,
        mismatch_attributes=[],
    )


def match_normalized_listings_for_query(
    target_title: str,
    target_brand: str = "",
    candidates: Optional[List[NormalizedListing]] = None,
    current_price: float = 0.0,
    min_similarity: float = 75.0,
) -> List[CompetitorPrice]:
    """
    Evaluates candidate NormalizedListings against target product using
    pricekit hard gates and token similarity.
    Returns sorted list of verified CompetitorPrice models.
    """
    if not candidates:
        return []

    from pricekit.gates import evaluate_gate, GateVerdict
    from pricekit.models import MatchSubject
    from pricekit.units import parse_quantity
    from rapidfuzz import fuzz

    target_qty = parse_quantity(target_title)
    target_subject = MatchSubject(
        title=target_title,
        brand=target_brand or None,
        quantity=target_qty,
        gtins=frozenset(),
    )

    matches: List[CompetitorPrice] = []
    seen_urls = set()

    for cand in candidates:
        cand_subject = cand.listing.subject()
        gate_res = evaluate_gate(target_subject, cand_subject)

        if gate_res.verdict in (GateVerdict.ACCEPT, GateVerdict.ACCEPT_AS_VARIANT):
            sim = fuzz.token_sort_ratio(
                target_title.lower(), cand.listing.title.lower()
            )
            if sim >= min_similarity:
                tier = "exact" if gate_res.verdict == GateVerdict.ACCEPT else "variant"
                comp = normalized_listing_to_competitor_price(
                    cand, current_price=current_price, match_tier=tier
                )
                if comp.store_url and comp.store_url in seen_urls:
                    continue
                seen_urls.add(comp.store_url)
                matches.append(comp)

    matches.sort(key=lambda x: x.effective_final_price)
    return matches
