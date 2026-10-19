"""Quick-Commerce Provider Pool for OmniCart.

Loads and queries normalized listings from PriceAggregator providers:
- BigBasket (BBNOW)
- Swiggy Instamart
- Blinkit

Caches provider instances and falls back gracefully to offline fixtures if live network/headless scrapers fail.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Paths
PRICE_AGGREGATOR_DIR = Path("D:/Workspace/Projects/PriceAggregator")
FIXTURES_DIR = PRICE_AGGREGATOR_DIR / "tests" / "fixtures"

if str(PRICE_AGGREGATOR_DIR) not in sys.path:
    sys.path.insert(0, str(PRICE_AGGREGATOR_DIR))

try:
    from pricekit.models import NormalizedListing
except ImportError:
    NormalizedListing = None  # Graceful fallback if PriceAggregator is not present

logger = logging.getLogger(__name__)


class QuickCommercePool:
    def __init__(self, fixtures_dir: Optional[Path] = None):
        self.fixtures_dir = fixtures_dir or FIXTURES_DIR

    def get_fixture_listings(self) -> List[NormalizedListing]:
        """Load normalized listings from verified replay fixtures (instant, deterministic)."""
        listings: List[NormalizedListing] = []

        # 1. BigBasket
        bb_fixture = self.fixtures_dir / "bbnow_api.json"
        if bb_fixture.exists():
            try:
                from src.providers.bigbasket import BigBasketProvider

                bb_prov = BigBasketProvider()
                with open(bb_fixture, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                listings.extend(bb_prov._parse_payloads([payload], pincode="110001"))
            except Exception as e:
                logger.warning(f"Failed to parse BigBasket fixture: {e}")

        # 2. Swiggy
        swiggy_fixture = self.fixtures_dir / "swiggy_captured.json"
        if swiggy_fixture.exists():
            try:
                from src.providers.swiggy import SwiggyInstamartProvider

                sw_prov = SwiggyInstamartProvider()
                with open(swiggy_fixture, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                listings.extend(sw_prov._parse_payloads([payload], pincode="110001"))
            except Exception as e:
                logger.warning(f"Failed to parse Swiggy fixture: {e}")

        # 3. Blinkit
        blinkit_fixture = self.fixtures_dir / "blinkit_search.json"
        if blinkit_fixture.exists():
            try:
                from src.providers.blinkit import BlinkitProvider

                bl_prov = BlinkitProvider()
                with open(blinkit_fixture, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                listings.extend(bl_prov._parse_payloads([payload], pincode="110001"))
            except Exception as e:
                logger.warning(f"Failed to parse Blinkit fixture: {e}")

        return listings


_qc_pool: Optional[QuickCommercePool] = None


def get_qc_pool() -> QuickCommercePool:
    global _qc_pool
    if _qc_pool is None:
        _qc_pool = QuickCommercePool()
    return _qc_pool
