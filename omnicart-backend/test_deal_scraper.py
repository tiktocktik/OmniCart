"""Offline tests for deal categorisation, discounts, and product-link resolution."""

from app.deal_scraper import (
    classify_flash_deal,
    clean_product_url,
    extract_deal_redirect,
    infer_deal_category,
    resolve_deal_product_url,
)


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


def test_desidime_buy_now_link_is_extracted():
    html = """
    <html><body>
      <a href="https://www.desidime.com/stores/flipkart">Flipkart</a>
      <a href="https://visit.desidime.com/visit/deals-1/2184866">Buy Now</a>
    </body></html>
    """
    assert (
        extract_deal_redirect(
            "https://www.desidime.com/deals/mokobara-grey-men-women-2184866",
            html,
        )
        == "https://visit.desidime.com/visit/deals-1/2184866"
    )


def test_dealsmagnet_buy_button_code_is_extracted():
    html = """
    <html><body>
      <button class="btn buy-button" data-code="d=1dc8D3lE&amp;utm_content=abc">
        Buy Now
      </button>
    </body></html>
    """
    assert (
        extract_deal_redirect(
            "https://www.dealsmagnet.com/deal/titan-raga-1dc8D3lE",
            html,
        )
        == "https://www.dealsmagnet.com/buy?d=1dc8D3lE&utm_content=abc"
    )


def test_amazon_product_url_is_canonicalised():
    messy = (
        "https://www.amazon.in/dealsmagnet.com/dp/B0CLRD5HWT"
        "?&&&tag=dealsmagnet-21&ascsubtag=abc"
    )
    assert clean_product_url(messy) == "https://www.amazon.in/dp/B0CLRD5HWT"


def test_flipkart_affiliate_parameters_are_removed():
    messy = (
        "https://www.flipkart.com/mokobara-grey-sling-bag/p/itm3eb6766f8797c"
        "?affid=salescueli&affExtParam1=1&affExtParam2=20261021&pid=ABC123"
    )
    assert (
        clean_product_url(messy)
        == "https://www.flipkart.com/mokobara-grey-sling-bag/p/itm3eb6766f8797c?pid=ABC123"
    )


def test_non_retailer_and_aggregator_urls_are_rejected():
    assert clean_product_url("https://www.desidime.com/deals/example") is None
    assert clean_product_url("https://example.com/product/1") is None
    assert clean_product_url("javascript:alert(1)") is None


def test_direct_retailer_url_resolves_without_network():
    assert (
        resolve_deal_product_url("https://www.amazon.in/dp/B0CLRD5HWT?tag=someone-21")
        == "https://www.amazon.in/dp/B0CLRD5HWT"
    )
