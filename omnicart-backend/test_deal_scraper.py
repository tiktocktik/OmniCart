"""Offline tests for deal categorisation and discount honesty."""

from app.deal_scraper import classify_flash_deal, infer_deal_category


def test_appliance_titles_are_home_and_kitchen():
    titles = [
        "Hawkins 5 L Stainless Steel - Induction Bottom Pressure Cooker",
        "SOLARA Triply Outer Lid Pressure Pan 2 Litre | 3-Ply Stainless Steel | Induction & Gas Com",
        "ANMIKA All-Purpose Cleaner Foam Spray, Lemon Fresh Multi-Surface Cleaning Foam",
        "Morphy Richards Windsor Series Digital 2 Slice Pop Up 800 W Toaster",
        "Kurlon 72 x 72 4inch Dual Comfort, Reversible Soft & Firm Sides, Spine Support, Anti-Microbial Mattress",
        "Haier 602 L 3 Star Frost Free Expert Inverter 2-Door Side by Side Refrigerator",
    ]
    for title in titles:
        assert infer_deal_category(title) == "Home & Kitchen", title


def test_electronics_and_fashion_keywords():
    assert (
        infer_deal_category(
            "Lenovo IdeaPad Slim 3, Intel Core Ultra 5 322, Next-Gen AI PC, 16GB RAM, 512GB SSD"
        )
        == "Electronics & Gadgets"
    )
    assert (
        infer_deal_category(
            "French Connection Eclat Teal Round Dial Womens Analogue Watch FCN074SM"
        )
        == "Fashion & Apparel"
    )


def test_grocery_keywords():
    assert (
        infer_deal_category(
            "Zepto - Patanjali Traditional Whole Wheat Atta (100% Atta, 0% Maida) 10kg"
        )
        == "Grocery & Essentials"
    )


def test_no_invented_discount_when_regular_price_is_missing():
    meta = classify_flash_deal(29.0, 29.0, 0)
    assert meta["badge"] == "DEAL"
    assert meta["savings"] == 0.0
    assert meta["isMegaDrop"] is False
    assert meta["isGlitch"] is False


def test_real_discount_is_kept():
    meta = classify_flash_deal(500.0, 1000.0, 50)
    assert meta["badge"] == "50% OFF"
    assert meta["savings"] == 500.0
    assert meta["isMegaDrop"] is False
