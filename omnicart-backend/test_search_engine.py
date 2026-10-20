"""Offline tests for search-result relevance filtering."""

from app.search_engine import _is_relevant, _parse_price


def test_model_number_query_matches_title():
    assert _is_relevant(
        "Sony WH-1000XM5 Wireless Noise Cancelling Headphones", "sony wh-1000xm5"
    )


def test_unrelated_fuzzy_result_is_rejected():
    assert not _is_relevant(
        "Jagyq USB Rechargeable Dual Arc Flameless Cigarette Lighter",
        "zzzqqq nonexistent gadget xyz",
    )


def test_two_letter_brand_matches():
    assert _is_relevant("HP 15s Ryzen 5 5500U 15.6 inch Laptop", "hp laptop")


def test_stopword_only_query_is_not_filtered():
    assert _is_relevant("Anything at all", "the best deal")


def test_flipkart_price_requires_currency_symbol():
    assert _parse_price("Sony WH-1000XM5", require_currency=True) is None
    assert _parse_price("₹19,989", require_currency=True) == 19989.0
