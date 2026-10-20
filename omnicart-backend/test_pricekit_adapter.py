"""
Tests for priceaggregator_adapter in OmniCart backend.
"""

import os
import sys
import json
from pathlib import Path
from decimal import Decimal
import pytest

# Paths
OMNICART_DIR = Path(__file__).parent
_env_dir = os.environ.get("PRICE_AGGREGATOR_DIR", "").strip()
PRICE_AGGREGATOR_DIR = Path(_env_dir).expanduser() if _env_dir else None

sys.path.insert(0, str(OMNICART_DIR))
if PRICE_AGGREGATOR_DIR:
    sys.path.insert(0, str(PRICE_AGGREGATOR_DIR))

if not PRICE_AGGREGATOR_DIR or not PRICE_AGGREGATOR_DIR.exists():
    pytest.skip(
        "PRICE_AGGREGATOR_DIR is not configured; skipping PriceAggregator adapter tests",
        allow_module_level=True,
    )

from app.priceaggregator_adapter import (
    normalized_listing_to_candidate_dict,
    normalized_listing_to_competitor_price,
)
from app.models import CompetitorPrice
from src.providers.bigbasket import BigBasketProvider
from src.providers.swiggy import SwiggyInstamartProvider


def test_bb_adapter_conversion():
    bb_fixture = PRICE_AGGREGATOR_DIR / "bbnow_api.json"
    if not bb_fixture.exists():
        pytest.skip(f"Fixture not found: {bb_fixture}")

    payload = json.loads(bb_fixture.read_text(encoding="utf-8"))
    listings = BigBasketProvider._parse_payloads([payload], pincode="560077")
    assert len(listings) > 0

    first = listings[0]
    cand = normalized_listing_to_candidate_dict(first, current_price=100.0)
    assert cand["platform"] == "BigBasket Now"
    assert cand["price"] > 0
    assert cand["badge"] == "QUICK COMMERCE"
    assert "delivery_info" in cand

    comp = normalized_listing_to_competitor_price(first, current_price=100.0)
    assert isinstance(comp, CompetitorPrice)
    assert comp.platform == "BigBasket Now"
    assert comp.price > 0
    assert comp.effective_final_price >= comp.price


def test_swiggy_adapter_conversion():
    swiggy_fixture = PRICE_AGGREGATOR_DIR / "swiggy_captured.json"
    if not swiggy_fixture.exists():
        pytest.skip(f"Fixture not found: {swiggy_fixture}")

    payload = json.loads(swiggy_fixture.read_text(encoding="utf-8"))
    listings = SwiggyInstamartProvider._parse_payloads([payload], pincode="560077")
    assert len(listings) > 0

    first = listings[0]
    cand = normalized_listing_to_candidate_dict(first, current_price=50.0)
    assert cand["platform"] == "Swiggy Instamart"
    assert cand["price"] > 0

    comp = normalized_listing_to_competitor_price(first, current_price=50.0)
    assert isinstance(comp, CompetitorPrice)
    assert comp.platform == "Swiggy Instamart"
    assert comp.price > 0


def test_blinkit_adapter_conversion():
    from src.providers.blinkit import BlinkitProvider

    blinkit_fixture = (
        PRICE_AGGREGATOR_DIR / "tests" / "fixtures" / "blinkit_search.json"
    )
    if not blinkit_fixture.exists():
        pytest.skip(f"Fixture not found: {blinkit_fixture}")

    payload = json.loads(blinkit_fixture.read_text(encoding="utf-8"))
    listings = BlinkitProvider._parse_payloads([payload], pincode="560077")
    assert len(listings) == 12

    first = listings[0]
    cand = normalized_listing_to_candidate_dict(first, current_price=90.0)
    assert cand["platform"] == "Blinkit"
    assert cand["price"] > 0
    assert cand["badge"] == "QUICK COMMERCE"

    comp = normalized_listing_to_competitor_price(first, current_price=90.0)
    assert isinstance(comp, CompetitorPrice)
    assert comp.platform == "Blinkit"
    assert comp.price == 85.0


def test_cross_store_matching_adapter():
    from app.priceaggregator_adapter import match_normalized_listings_for_query
    from src.providers.bigbasket import BigBasketProvider
    from src.providers.blinkit import BlinkitProvider

    bb_fixture = PRICE_AGGREGATOR_DIR / "tests" / "fixtures" / "bbnow_api.json"
    blinkit_fixture = (
        PRICE_AGGREGATOR_DIR / "tests" / "fixtures" / "blinkit_search.json"
    )
    if not bb_fixture.exists() or not blinkit_fixture.exists():
        pytest.skip("Fixtures missing")

    bb_payload = json.loads(bb_fixture.read_text(encoding="utf-8"))
    bl_payload = json.loads(blinkit_fixture.read_text(encoding="utf-8"))

    bb_listings = BigBasketProvider._parse_payloads([bb_payload], pincode="560077")
    bl_listings = BlinkitProvider._parse_payloads([bl_payload], pincode="560077")
    all_candidates = bb_listings + bl_listings

    # Query for "Amul Gold Full Cream Milk 1 L"
    matches = match_normalized_listings_for_query(
        target_title="Amul Gold Full Cream Milk 1 L",
        target_brand="Amul",
        candidates=all_candidates,
        current_price=75.0,
    )

    assert len(matches) >= 2, (
        f"Expected matches from both BB and Blinkit, got {len(matches)}"
    )
    platforms = {m.platform for m in matches}
    assert "BigBasket Now" in platforms or "Blinkit" in platforms
    for m in matches:
        assert "Amul Gold" in m.title
        assert m.price > 0
        assert m.effective_final_price > 0


def test_competitor_engine_with_quick_commerce():
    from app.competitor_engine import find_cross_platform_competitors
    from src.providers.bigbasket import BigBasketProvider
    from src.providers.blinkit import BlinkitProvider

    bb_fixture = PRICE_AGGREGATOR_DIR / "tests" / "fixtures" / "bbnow_api.json"
    bl_fixture = PRICE_AGGREGATOR_DIR / "tests" / "fixtures" / "blinkit_search.json"
    if not bb_fixture.exists() or not bl_fixture.exists():
        pytest.skip("Fixtures missing")

    bb_payload = json.loads(bb_fixture.read_text(encoding="utf-8"))
    bl_payload = json.loads(bl_fixture.read_text(encoding="utf-8"))
    all_candidates = BigBasketProvider._parse_payloads(
        [bb_payload], pincode="560077"
    ) + BlinkitProvider._parse_payloads([bl_payload], pincode="560077")

    exacts, similar = find_cross_platform_competitors(
        title="Amul Cow Milk 500 ml",
        current_platform="Amazon Fresh",
        current_price=60.0,
        brand="Amul",
        quick_commerce_candidates=all_candidates,
    )

    assert len(exacts) > 0
    assert any("Amul Cow Milk" in e.title for e in exacts)
    # Price is 31, which is cheaper than 35.0
    cheaper_ones = [e for e in exacts if e.is_cheaper]
    assert len(cheaper_ones) > 0
