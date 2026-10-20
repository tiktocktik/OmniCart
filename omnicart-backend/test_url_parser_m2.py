"""Offline regression tests for input classification and URL normalisation (M2)."""

import pytest

import app.url_parser as url_parser
from app.resolver import resolve_product_pipeline
from app.url_parser import clean_and_normalize_url


@pytest.mark.parametrize("text", ["headphones", "smartphone", "Sunglasses"])
def test_product_names_are_search_queries(text):
    cleaned, platform, item_id = clean_and_normalize_url(text)
    assert platform == "SEARCH_QUERY"
    assert cleaned == text
    assert item_id is None


def test_direct_asin_is_accepted():
    cleaned, platform, item_id = clean_and_normalize_url("B0GJV4XW2B")
    assert platform == "Amazon.in"
    assert item_id == "B0GJV4XW2B"
    assert cleaned == "https://www.amazon.in/dp/B0GJV4XW2B"


def test_amazon_url_strips_tracking_and_keeps_asin():
    cleaned, platform, item_id = clean_and_normalize_url(
        "https://www.amazon.in/Sony-Headphones/dp/B0GJV4XW2B/ref=sr_1_1"
        "?tag=affiliate-21&th=1&utm_source=test"
    )
    assert platform == "Amazon.in"
    assert item_id == "B0GJV4XW2B"
    assert cleaned == "https://www.amazon.in/dp/B0GJV4XW2B"


def test_amazon_gp_product_path_is_accepted():
    cleaned, platform, item_id = clean_and_normalize_url(
        "https://www.amazon.in/gp/product/B0GJV4XW2B"
    )
    assert platform == "Amazon.in"
    assert item_id == "B0GJV4XW2B"
    assert cleaned == "https://www.amazon.in/dp/B0GJV4XW2B"


def test_lookalike_host_is_not_amazon():
    cleaned, platform, item_id = clean_and_normalize_url("https://notamazon.in/dp/B0GJV4XW2B")
    assert platform == "Universal"
    assert item_id == "B0GJV4XW2B"
    assert "notamazon.in" in cleaned


def test_amazon_suffix_attack_is_not_amazon():
    _, platform, _ = clean_and_normalize_url("https://amazon.in.evil.com/dp/B0GJV4XW2B")
    assert platform == "Universal"


def test_flipkart_url_preserves_pid():
    cleaned, platform, item_id = clean_and_normalize_url(
        "https://www.flipkart.com/sony-wh-1000xm5/p/itmabcdef123"
        "?pid=HEADPHONE123&utm_source=test"
    )
    assert platform == "Flipkart"
    assert item_id == "HEADPHONE123"
    assert cleaned == (
        "https://www.flipkart.com/sony-wh-1000xm5/p/itmabcdef123?pid=HEADPHONE123"
    )


def test_short_link_is_expanded_to_flipkart(monkeypatch):
    monkeypatch.setattr(
        url_parser,
        "_expand_short_url",
        lambda url, timeout=6.0: "https://www.flipkart.com/sony/p/itm123?pid=ABC123",
    )
    cleaned, platform, item_id = clean_and_normalize_url("https://dl.flipkart.com/s/abc")
    assert platform == "Flipkart"
    assert item_id == "ABC123"
    assert cleaned == "https://www.flipkart.com/sony/p/itm123?pid=ABC123"


def test_short_link_expansion_failure_is_explicit(monkeypatch):
    monkeypatch.setattr(url_parser, "_expand_short_url", lambda url, timeout=6.0: None)
    _, platform, item_id = clean_and_normalize_url("https://amzn.to/3abcDEF")
    assert platform == "SHORT_LINK"
    assert item_id is None


def test_short_link_to_store_homepage_is_rejected(monkeypatch):
    monkeypatch.setattr(
        url_parser,
        "_expand_short_url",
        lambda url, timeout=6.0: "https://www.amazon.com/",
    )
    cleaned, platform, item_id = clean_and_normalize_url("https://amzn.to/3abcDEF")
    assert platform == "SHORT_LINK"
    assert item_id is None
    assert cleaned == "https://amzn.to/3abcDEF"


def test_text_query_is_not_resolved_as_a_product():
    with pytest.raises(ValueError):
        resolve_product_pipeline("headphones", pincode="110001")
