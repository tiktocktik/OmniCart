import re
import json
import sqlite3
import os
from datetime import datetime
from bs4 import BeautifulSoup
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

DB_PATH = os.path.join(os.path.dirname(__file__), "omnicart.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        price REAL NOT NULL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_glitch INTEGER DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS coupons_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store TEXT NOT NULL,
        code TEXT NOT NULL,
        discount_text TEXT,
        discount_amount REAL,
        success_rate REAL DEFAULT 95.0,
        last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

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
    bank_offers: Optional[List[CouponInfo]] = None
) -> List[PaymentOption]:
    """
    Precision Arbitrage Engine that evaluates the user's specific card portfolio
    against active marketplace bank promotions and rewards:
    1. PhonePe SBI Card SELECT BLACK (SBI Bank instant offers + 5% online)
    2. ICICI Rubyx / Coral (RuPay) & Amazon Pay ICICI (ICICI Bank instant offers + 5% Amazon)
    3. Tata Neu Infinity (RuPay) (5% NeuCoins on Tata + RuPay UPI)
    4. HSBC Live+ Credit Card (10% dining/grocery + 1.5% retail)
    5. HSBC RuPay Cashback Card (ending 0767) (1.5% base)
    6. Sodexo / Pluxee (31.2% meal tax shield)
    7. HDFC EasyShop Platinum Debit Card (1% bill payment settlement)
    """
    options: List[PaymentOption] = []
    lower_store = store.lower()
    lower_cat = category.lower()

    # Detect matching bank offers from marketplace promotion feed
    sbi_offer: Optional[CouponInfo] = None
    icici_offer: Optional[CouponInfo] = None
    hdfc_offer: Optional[CouponInfo] = None
    hsbc_offer: Optional[CouponInfo] = None

    if bank_offers:
        for b in bank_offers:
            text = (b.discount_text + " " + b.code + " " + b.source).lower()
            if "sbi" in text and not sbi_offer:
                sbi_offer = b
            elif "icici" in text and not icici_offer:
                icici_offer = b
            elif "hdfc" in text and not hdfc_offer:
                hdfc_offer = b
            elif "hsbc" in text and not hsbc_offer:
                hsbc_offer = b

    # Category checks
    is_food_or_grocery = (
        any(k in lower_store for k in ["zepto", "blinkit", "instamart", "swiggy", "zomato", "eatclub", "bigbasket", "dmart"]) or
        any(k in lower_cat for k in ["food", "grocery", "gourmet", "dining", "snack"])
    )
    is_entertainment = (
        any(k in lower_store for k in ["bookmyshow", "pvr", "inox"]) or
        any(k in lower_cat for k in ["movie", "cinema", "ticket", "entertainment"])
    )
    is_amazon = "amazon" in lower_store
    is_tata = any(k in lower_store for k in ["tata", "westside", "croma", "1mg", "cliq"])

    # --- CATEGORY & STORE SPECIFIC OPTIMAL INSTRUMENTS ---

    if is_food_or_grocery:
        # 1. Sodexo / Pluxee (31.2% effective tax shield yield)
        sodexo_sav = round(live_price * 0.312, 2)
        options.append(PaymentOption(
            title="Sodexo / Pluxee Card (Tax Shield Yield)",
            type="Card",
            effective_savings=sodexo_sav,
            final_price=round(live_price - sodexo_sav, 2),
            explanation="31.2% effective tax savings from your monthly ₹8,800 non-taxable meal allowance (ANZ flex basket).",
            is_recommended=True
        ))

        # 2. HSBC Live+ Credit Card (10% accelerated cashback)
        hsbc_live_sav = round(min(live_price * 0.10, 1000.0), 2)
        options.append(PaymentOption(
            title="HSBC Live+ Credit Card — 10% Dining & Groceries",
            type="Card",
            effective_savings=hsbc_live_sav,
            final_price=round(live_price - hsbc_live_sav, 2),
            explanation="10% accelerated statement cashback on dining POS swipes, Swiggy, Zomato, and supermarkets (capped at ₹1,000/mo).",
            is_recommended=False
        ))

        # 3. PhonePe SBI Card SELECT BLACK
        phonepe_sav = round(min(live_price * 0.10, 1500.0), 2) if "phonepe" in lower_store else round(min(live_price * 0.05, 1000.0), 2)
        options.append(PaymentOption(
            title="PhonePe SBI Card SELECT BLACK (RuPay)",
            type="Card",
            effective_savings=phonepe_sav,
            final_price=round(live_price - phonepe_sav, 2),
            explanation="10% return (10 RPs/₹100) if ordered through PhonePe app, or 5% online shopping cashback (capped at ₹1,000/mo).",
            is_recommended=False
        ))

    elif is_entertainment:
        # ICICI Rubyx / Coral (RuPay) BookMyShow Offer
        bogo_sav = round(min(live_price * 0.25, 150.0), 2)
        options.append(PaymentOption(
            title="ICICI Rubyx / Coral (RuPay) — BookMyShow 25% Off",
            type="Card",
            effective_savings=bogo_sav,
            final_price=round(live_price - bogo_sav, 2),
            explanation="25% instant discount (up to ₹150 on Rubyx, ₹100 on Coral) on 2 movie tickets twice a month on BookMyShow/INOX.",
            is_recommended=True
        ))

        phonepe_sav = round(min(live_price * 0.10, 1500.0), 2)
        options.append(PaymentOption(
            title="PhonePe SBI Card SELECT BLACK (PhonePe Events)",
            type="Card",
            effective_savings=phonepe_sav,
            final_price=round(live_price - phonepe_sav, 2),
            explanation="10% rewards (10 RPs/₹100) on events and movies booked inside PhonePe.",
            is_recommended=False
        ))

    elif is_amazon:
        # A. PhonePe SBI Card SELECT BLACK with Amazon SBI Bank Offer
        if sbi_offer and sbi_offer.discount_amount > 0:
            options.append(PaymentOption(
                title="PhonePe SBI Card SELECT BLACK — 10% Instant Bank Offer",
                type="Card",
                effective_savings=round(sbi_offer.discount_amount, 2),
                final_price=round(live_price - sbi_offer.discount_amount, 2),
                explanation=f"{sbi_offer.discount_text} automatically deducted at Amazon payment gateway using your SBI card line.",
                is_recommended=True
            ))

        # B. ICICI Amazon Pay
        amz_sav = round(live_price * 0.05, 2)
        options.append(PaymentOption(
            title="ICICI Amazon Pay Credit Card — 5% Uncapped",
            type="Card",
            effective_savings=amz_sav,
            final_price=round(live_price - amz_sav, 2),
            explanation="5% flat unlimited cashback credited directly as Amazon Pay balance for Prime members.",
            is_recommended=not bool(sbi_offer and sbi_offer.discount_amount > amz_sav)
        ))

        # C. PhonePe SBI SELECT BLACK (Standard Online Spend if no bank offer)
        if not sbi_offer or sbi_offer.discount_amount <= 0:
            phonepe_sav = round(min(live_price * 0.05, 1000.0), 2)
            options.append(PaymentOption(
                title="PhonePe SBI Card SELECT BLACK — 5% Online Spend",
                type="Card",
                effective_savings=phonepe_sav,
                final_price=round(live_price - phonepe_sav, 2),
                explanation="5% return (5 RPs per ₹100, 1 RP = ₹1) on online shopping (capped at ₹1,000/mo).",
                is_recommended=False
            ))

        # D. GyFTR HDFC SmartBuy Amazon Voucher Arbitrage
        voucher_sav = round(live_price * 0.065, 2)
        options.append(PaymentOption(
            title="GyFTR HDFC SmartBuy Amazon Voucher Arbitrage",
            type="Voucher",
            effective_savings=voucher_sav,
            final_price=round(live_price - voucher_sav, 2),
            explanation="Buy Amazon Shopping Voucher on HDFC SmartBuy for 5X accelerated reward points (~6.5% return).",
            is_recommended=False
        ))

    elif is_tata:
        # Tata Neu Infinity (RuPay)
        neu_sav = round(live_price * 0.05, 2)
        options.append(PaymentOption(
            title="Tata Neu Infinity (RuPay) — 5% NeuCoins",
            type="Card",
            effective_savings=neu_sav,
            final_price=round(live_price - neu_sav, 2),
            explanation="5% NeuCoins on Tata flagship brands (1 NeuCoin = ₹1). Spend directly on next order.",
            is_recommended=True
        ))

        # ICICI Bank Instant Discount if active on Tata CliQ / Westside
        if icici_offer and icici_offer.discount_amount > 0:
            options.append(PaymentOption(
                title="ICICI Rubyx / Coral (RuPay) — Instant Bank Offer",
                type="Card",
                effective_savings=round(icici_offer.discount_amount, 2),
                final_price=round(live_price - icici_offer.discount_amount, 2),
                explanation=f"{icici_offer.discount_text} automatically applied at checkout via your ICICI card line.",
                is_recommended=icici_offer.discount_amount > neu_sav
            ))

        # PhonePe SBI SELECT BLACK
        phonepe_sav = round(min(live_price * 0.05, 1000.0), 2)
        options.append(PaymentOption(
            title="PhonePe SBI Card SELECT BLACK — 5% Online Spend",
            type="Card",
            effective_savings=phonepe_sav,
            final_price=round(live_price - phonepe_sav, 2),
            explanation="5% return (5 RPs per ₹100) on online non-PhonePe merchant spends.",
            is_recommended=False
        ))

    else:
        # General Online Retail / Fashion / Marketplaces (Flipkart, Myntra, AJIO, D2C)
        # Check active bank offers first
        if sbi_offer and sbi_offer.discount_amount > 0:
            options.append(PaymentOption(
                title="PhonePe SBI Card SELECT BLACK — Instant Sale Offer",
                type="Card",
                effective_savings=round(sbi_offer.discount_amount, 2),
                final_price=round(live_price - sbi_offer.discount_amount, 2),
                explanation=f"{sbi_offer.discount_text} automatically applied at payment gateway via your SBI credit line.",
                is_recommended=True
            ))

        if icici_offer and icici_offer.discount_amount > 0:
            options.append(PaymentOption(
                title="ICICI Rubyx / Coral (RuPay) — Instant Bank Offer",
                type="Card",
                effective_savings=round(icici_offer.discount_amount, 2),
                final_price=round(live_price - icici_offer.discount_amount, 2),
                explanation=f"{icici_offer.discount_text} automatically applied at payment gateway via your ICICI credit line.",
                is_recommended=not any(o.is_recommended for o in options)
            ))

        # Standard portfolio rewards fallback
        phonepe_sav = round(min(live_price * 0.05, 1000.0), 2)
        if not sbi_offer or sbi_offer.discount_amount <= 0:
            options.append(PaymentOption(
                title="PhonePe SBI Card SELECT BLACK — 5% Online Shopping",
                type="Card",
                effective_savings=phonepe_sav,
                final_price=round(live_price - phonepe_sav, 2),
                explanation="5% return (5 Reward Points per ₹100, 1 RP = ₹1) on online shopping (capped at ₹1,000/mo).",
                is_recommended=not any(o.is_recommended for o in options)
            ))

        # HSBC Live+ Credit Card (1.5% Unlimited Base)
        hsbc_live_base = round(live_price * 0.015, 2)
        options.append(PaymentOption(
            title="HSBC Live+ Credit Card — 1.5% Unlimited Base",
            type="Card",
            effective_savings=hsbc_live_base,
            final_price=round(live_price - hsbc_live_base, 2),
            explanation="1.5% unlimited direct statement cashback across all domestic online retail merchants.",
            is_recommended=False
        ))

        # HSBC RuPay Cashback Card (ending 0767) (1.5% Base)
        hsbc_rupay_base = round(live_price * 0.015, 2)
        options.append(PaymentOption(
            title="HSBC RuPay Cashback Card (ending 0767) — 1.5% Base",
            type="Card",
            effective_savings=hsbc_rupay_base,
            final_price=round(live_price - hsbc_rupay_base, 2),
            explanation="1.5% unlimited cashback via existing HSBC RuPay credit line on domestic retail transactions.",
            is_recommended=False
        ))

    # --- UNIVERSAL PAYMENT RAILS & SETTLEMENT STRATEGY ---

    # 1. Tata Neu Infinity (RuPay) on UPI (1.5% NeuCoins)
    neu_upi_sav = round(live_price * 0.015, 2)
    options.append(PaymentOption(
        title="Tata Neu Infinity (RuPay) on UPI — 1.5% NeuCoins",
        type="UPI",
        effective_savings=neu_upi_sav,
        final_price=round(live_price - neu_upi_sav, 2),
        explanation="1.5% NeuCoins on merchant UPI QR transactions with zero OTP friction."
    ))

    # 2. Bill Settlement Loophole: HDFC EasyShop Platinum Debit Card
    billpay_sav = round(min(live_price * 0.01, 750.0), 2)
    options.append(PaymentOption(
        title="HDFC EasyShop Platinum DC — 1% BillPay Settlement",
        type="Card",
        effective_savings=billpay_sav,
        final_price=round(live_price - billpay_sav, 2),
        explanation="When your credit card statement arrives, pay it via HDFC NetBanking BillPay using your HDFC EasyShop Platinum Debit Card for an extra 1% cash back (capped at ₹750/mo pure cash)."
    ))

    # Set single best recommended if none set
    if not any(opt.is_recommended for opt in options):
        max_s = max([o.effective_savings for o in options], default=0)
        for o in options:
            if o.effective_savings == max_s and max_s > 0:
                o.is_recommended = True
                break

    return options

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

    store_code = best_coupon.code if best_coupon else "AUTO_STORE_PROMO"
    store_source = best_coupon.source if best_coupon else "Store Offer"
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
        if store_savings > 0 else "Proceed to payment (no store coupon code needed; savings come directly from card gateway)."
    )
    steps = [
        f"Step 1: {step1_desc}",
        f"Step 2: Pay remaining ₹{int(cart_balance)} using {card_title} ({card_type}) to capture ₹{int(card_savings)} additional instant discount/cashback.",
        f"Step 3: Settle your monthly credit card statement via HDFC BillPay Platinum Debit Card for an extra 1% cash back."
    ]

    return SmartStackCombo(
        store_coupon_code=store_code if store_savings > 0 else "NO_CODE_REQUIRED",
        store_coupon_source=store_source if store_savings > 0 else "Direct Card Gateway",
        store_coupon_savings=store_savings,
        card_title=card_title,
        card_type=card_type,
        card_savings=card_savings,
        combined_total_savings=total_savings,
        final_stacked_price=final_price,
        discount_percentage=discount_pct,
        execution_steps=steps
    )

