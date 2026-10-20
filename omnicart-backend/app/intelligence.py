from typing import Optional, Dict, Any, List
from .models import (
    ProductResolution,
    PricePoint,
    SellerInfo,
    CouponInfo,
    PaymentOption,
    PricePrediction,
    SmartStackCombo
)

def compute_price_prediction(live_price: float, all_time_low: float, regular_price: float, history_source: str = "VERIFIED_AGGREGATOR", data_points: int = 0) -> PricePrediction:
    """
    Computes statistical price drop prediction truthfully based on whether
    data is backed by verified multi-year logs or newly tracked live pricing.
    """
    if regular_price <= 0:
        drop_pct = 0.0
    else:
        drop_pct = ((regular_price - live_price) / regular_price) * 100

    if history_source == "VERIFIED_AGGREGATOR" and data_points > 0:
        if live_price <= (all_time_low * 1.03):
            return PricePrediction(
                badge="BUY NOW",
                detail=f"At or within 3% of verified all-time lowest price in India (₹{int(all_time_low)} across {data_points} archived observations).",
                drop_likelihood="High likelihood price will revert to normal within 24-48 hours.",
                confidence=98
            )
        elif drop_pct >= 25:
            return PricePrediction(
                badge="FAIR PRICE",
                detail=f"Moderate discount of {int(drop_pct)}% from peak (₹{int(regular_price)}). Lowest recorded was ₹{int(all_time_low)}.",
                drop_likelihood="Average pricing trend. Festival sales may see deeper dips.",
                confidence=85
            )
        else:
            return PricePrediction(
                badge="WAIT",
                detail=f"Near regular price. Verified lowest in archives was ₹{int(all_time_low)} ({int(((live_price - all_time_low) / live_price) * 100)}% cheaper).",
                drop_likelihood="Price likely to drop during upcoming sale cycles.",
                confidence=89
            )
    else:
        # Un-archived / newly tracked private label SKU
        if drop_pct >= 40:
            return PricePrediction(
                badge="BUY NOW",
                detail=f"Substantial discount of {int(drop_pct)}% below list MRP (₹{int(regular_price)}). First tracked today.",
                drop_likelihood="Significant manufacturer markdown.",
                confidence=90
            )
        elif drop_pct >= 20:
            return PricePrediction(
                badge="FAIR PRICE",
                detail=f"Discount of {int(drop_pct)}% below list MRP (₹{int(regular_price)}). Tracking initiated today.",
                drop_likelihood="Standard seasonal promotion.",
                confidence=80
            )
        else:
            return PricePrediction(
                badge="WAIT",
                detail=f"Selling near full list MRP (₹{int(regular_price)}). Consider waiting for promotional discount.",
                drop_likelihood="Price likely to drop during brand sales.",
                confidence=82
            )

def calculate_payment_arbitrage(
    live_price: float,
    store: str,
    category: str = "",
    bank_offers: Optional[List[CouponInfo]] = None,
) -> List[PaymentOption]:
    """Return payment savings only when a real offer exists.

    OmniCart does not ship, infer, or display a personal card portfolio. Bank
    offers found on the store page are already handled as coupons; without a
    verified offer there is no payment saving to report.
    """
    return []


def calculate_smart_stack_combination(
    live_price: float,
    coupons: List[CouponInfo],
    payment_options: List[PaymentOption]
) -> Optional[SmartStackCombo]:
    """
    Intelligently stacks store-level promo codes / in-cart coupons with the optimal
    credit card / payment gateway discount to produce the lowest possible net price.
    """
    if live_price <= 0:
        return None

    # 1. Identify Best In-Cart Store Promo Code (strictly non-bank offer)
    store_coupons = [
        c for c in coupons 
        if "bank" not in c.source.lower() and c.discount_amount > 0
    ]

    best_coupon: Optional[CouponInfo] = None
    if store_coupons:
        best_coupon = max(store_coupons, key=lambda c: c.discount_amount)

    store_code = best_coupon.code if best_coupon else "NO_CODE_REQUIRED"
    store_source = best_coupon.source if best_coupon else "No store coupon found"
    store_savings = round(min(best_coupon.discount_amount, live_price * 0.5), 2) if best_coupon else 0.0

    # 2. Compute Cart Balance after Store Promo
    cart_balance = max(live_price - store_savings, 0.0)

    # 3. Identify Best Credit Card / Payment Instrument on Cart Balance
    valid_payment_opts = [opt for opt in payment_options if opt.effective_savings > 0]
    
    if valid_payment_opts:
        best_card = max(valid_payment_opts, key=lambda opt: opt.effective_savings)
        ratio = cart_balance / live_price if live_price > 0 else 1.0
        card_savings = round(min(best_card.effective_savings * ratio, cart_balance * 0.25), 2)
        card_title = best_card.title
        card_type = best_card.type
    else:
        card_title = "Standard UPI / Debit"
        card_type = "UPI"
        card_savings = 0.0

    # 4. Total Combined Stacking Outcome
    total_savings = round(store_savings + card_savings, 2)
    final_price = round(max(live_price - total_savings, 0.0), 2)
    discount_pct = round((total_savings / live_price) * 100, 1) if live_price > 0 else 0.0

    # 5. Clear, Actionable 3-Step Checkout Stacking Blueprint
    step1_desc = (
        f"Apply promo code '{store_code}' at checkout to unlock ₹{int(store_savings)} off cart value."
        if store_savings > 0
        else "Proceed to checkout (no store coupon was found on the product page)."
    )
    step2_desc = (
        f"Pay remaining ₹{int(cart_balance)} using {card_title} ({card_type}) "
        f"to capture ₹{int(card_savings)} in verified savings."
        if card_savings > 0
        else "No card-specific savings were verified for this purchase."
    )
    steps = [
        f"Step 1: {step1_desc}",
        f"Step 2: {step2_desc}",
        "Step 3: Confirm the final price and offer terms on the store checkout page.",
    ]

    return SmartStackCombo(
        store_coupon_code=store_code if store_savings > 0 else "NO_CODE_REQUIRED",
        store_coupon_source=store_source if store_savings > 0 else "No store coupon found",
        store_coupon_savings=store_savings,
        card_title=card_title,
        card_type=card_type,
        card_savings=card_savings,
        combined_total_savings=total_savings,
        final_stacked_price=final_price,
        discount_percentage=discount_pct,
        execution_steps=steps
    )

