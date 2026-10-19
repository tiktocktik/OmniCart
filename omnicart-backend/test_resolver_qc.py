import pytest
from app.resolver import resolve_product_pipeline
from app.qc_pool import get_qc_pool
import app.resolver as resolver


def test_qc_pool_fixture_listings():
    pool = get_qc_pool()
    listings = pool.get_fixture_listings()
    assert len(listings) > 0
    # BB, Swiggy, and Blinkit items should all be loaded
    stores = {l.listing.store.value for l in listings}
    assert "bbnow" in stores
    assert "swiggy_instamart" in stores
    assert "blinkit" in stores


def test_resolver_injects_quick_commerce_competitors(monkeypatch):
    fake_amazon_product = {
        "title": "Amul Taaza Milk 500ml",
        "live_price": 35.0,
        "regular_price": 35.0,
        "category": "Dairy & Milk",
        "image_url": "https://example.com/amul.jpg",
        "gallery_images": [],
        "rating": 4.5,
        "ratings_count": 500,
        "seller_name": "Cloudtail Fresh",
        "delivery_promise": "Tomorrow morning",
        "purchase_options": [],
        "specifications": {"Brand": "Amul"},
        "highlights": ["Toned Milk"],
    }

    monkeypatch.setattr(
        resolver,
        "fetch_live_amazon_product",
        lambda item_id, url, pincode: fake_amazon_product,
    )

    # Resolve an amazon ASIN url
    res = resolve_product_pipeline(
        "https://www.amazon.in/dp/B00FAKEAMU", pincode="110001"
    )

    assert res is not None
    assert res.platform == "Amazon.in"
    # Verify competitors list was populated with quick-commerce items
    competitor_platforms = [c.platform for c in res.competitors]
    has_qc = any(
        p in ["BigBasket Now", "Swiggy Instamart", "Blinkit"]
        for p in competitor_platforms
    )
    assert has_qc, f"Expected quick-commerce competitors, got: {competitor_platforms}"
