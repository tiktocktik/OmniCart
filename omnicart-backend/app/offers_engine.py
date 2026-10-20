"""Marketplace offers.

Only coupons that were actually found on the store page are returned. OmniCart
does not invent platform-wide promo codes, bank offers, or success rates.
"""

from typing import List, Dict, Any, Optional

from .models import CouponInfo


def get_marketplace_offers(
    platform: str,
    live_price: float,
    category: str = "",
    scraped_coupons: Optional[List[Dict[str, Any]]] = None,
) -> List[CouponInfo]:
    if not scraped_coupons:
        return []

    offers: List[CouponInfo] = []
    seen_codes = set()

    for c in scraped_coupons:
        code = (c.get("code") or "").strip().upper()
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        amount = float(c.get("discount_amount") or 0.0)
        discount_text = c.get("discount_text") or (
            f"₹{int(amount)} off" if amount > 0 else "Offer found on the store page"
        )

        offers.append(
            CouponInfo(
                code=code,
                source=c.get("source") or "Store page",
                discount_text=discount_text,
                discount_amount=amount,
                # The page does not tell us a verified success rate.
                success_rate=None,
            )
        )

    return offers
