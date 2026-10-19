from typing import List, Dict, Any, Tuple, Optional
from .models import CompetitorPrice
from .entity_matcher import normalize_title, classify_product_match
from .live_marketplace_scraper import query_live_marketplaces_in_parallel


def find_cross_platform_competitors(
    title: str,
    current_platform: str,
    current_price: float,
    brand: str = "",
    quick_commerce_candidates: Optional[List[Any]] = None,
) -> Tuple[List[CompetitorPrice], List[CompetitorPrice]]:
    """
    STRICT 1:1 Dynamic Cross-Platform Comparison Engine:
    - Returns ONLY true, 100% verified identical SKU listings on competing Indian marketplaces & dark stores.
    - Loose 'similar styles' or category mismatches are 100% excluded to guarantee exact-match purity.
    """
    clean_title = normalize_title(title)
    words = clean_title.split()
    if brand:
        target_brand = brand
    elif words and words[0] in ["the", "all", "house", "flying", "united"]:
        target_brand = " ".join(words[:3])
    else:
        target_brand = words[0] if words else ""

    live_candidates = query_live_marketplaces_in_parallel(
        title, current_platform, target_brand
    )

    exact_competitors: List[CompetitorPrice] = []
    seen_urls = set()

    # Integrate verified quick-commerce candidate listings if provided
    if quick_commerce_candidates:
        from .priceaggregator_adapter import match_normalized_listings_for_query

        qc_matches = match_normalized_listings_for_query(
            target_title=title,
            target_brand=target_brand,
            candidates=quick_commerce_candidates,
            current_price=current_price,
        )
        for qcm in qc_matches:
            if qcm.store_url not in seen_urls:
                seen_urls.add(qcm.store_url)
                exact_competitors.append(qcm)

    for cand in live_candidates:
        url = cand["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        cand_title = cand["title"]
        tier, mismatch_reasons = classify_product_match(title, cand_title, target_brand)

        # STRICT: Reject anything that is not a 100% verified exact match!
        if tier != "exact":
            continue

        base_p = cand["price"]
        deliv_fee = cand["delivery_fee"]
        card_sav = cand["card_savings"]
        effective_price = round(base_p + deliv_fee - card_sav, 2)

        entry = CompetitorPrice(
            platform=cand["platform"],
            title=cand_title,
            price=base_p,
            delivery_info=cand["delivery_info"],
            delivery_fee=deliv_fee,
            combined_discount_text=cand["discount_text"],
            effective_final_price=effective_price,
            store_url=url,
            is_cheaper=effective_price < current_price if current_price > 0 else False,
            badge="1:1 EXACT MATCH",
            match_tier="exact",
            mismatch_attributes=[],
        )
        exact_competitors.append(entry)

    exact_competitors.sort(key=lambda x: x.effective_final_price)

    # Return verified exact competitors only; similar_styles is empty to avoid false comparisons
    return exact_competitors[:4], []
