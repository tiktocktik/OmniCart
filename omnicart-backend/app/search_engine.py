"""Live product search across Amazon.in and Flipkart.

Results contain only fields read from the search page. Delivery promises, card
offers and ratings are intentionally not invented here; the selected product is
resolved separately and its own page is the source of truth.
"""

from __future__ import annotations

import hashlib
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
}

ROBOT_MARKERS = (
    "api-services-support@amazon.com",
    "robot check",
    "type the characters you see",
    "enter the characters you see",
    "/errors/validatecaptcha",
)

# Words that carry no product identity. A query of only these is not filtered.
STOPWORDS = {
    "a", "an", "and", "the", "of", "in", "on", "to", "for", "with", "by",
    "at", "is", "it", "or", "as", "be", "my", "me", "we", "you", "your",
    "our", "this", "that", "these", "those", "from", "up", "down", "off",
    "out", "new", "buy", "online", "india", "indian", "latest", "best",
    "deal", "deals", "price", "cheap", "under", "over", "combo", "pack",
}


def _tokens(value: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (value or "").lower()) if t]


def _is_relevant(title: str, query: str) -> bool:
    """Require at least one meaningful query token in the result title.

    Store search pages return fuzzy matches for nonsense queries (Flipkart once
    returned a cigarette lighter for "zzzqqq nonexistent gadget xyz"). This
    keeps the candidate list tied to what the user actually asked for.
    """
    query_tokens = [
        t for t in _tokens(query) if len(t) >= 2 and t not in STOPWORDS
    ]
    if not query_tokens:
        return True
    title_tokens = set(_tokens(title))
    return any(token in title_tokens for token in query_tokens)


def _fetch(url: str, timeout: float = 6.0) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _is_robot(html: str) -> bool:
    lower = html.lower()
    return any(marker in lower for marker in ROBOT_MARKERS)


def _parse_price(text: str, require_currency: bool = False) -> Optional[float]:
    pattern = (
        r"₹\s*([0-9][0-9,]*(?:\.[0-9]+)?)"
        if require_currency
        else r"([0-9][0-9,]*(?:\.[0-9]+)?)"
    )
    match = re.search(pattern, text or "")
    if not match:
        return None
    try:
        value = float(match.group(1).replace(",", ""))
        return value if value > 0 else None
    except ValueError:
        return None


def _search_amazon(query: str, limit: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    url = f"https://www.amazon.in/s?k={urllib.parse.quote(query)}"
    try:
        html = _fetch(url)
    except Exception as exc:
        return [], f"Amazon search failed: {exc}"

    if _is_robot(html):
        return [], "Amazon returned a robot-check page."

    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []
    seen = set()

    for div in soup.select("div[data-asin]"):
        asin = (div.get("data-asin") or "").strip().upper()
        if len(asin) != 10 or asin in seen:
            continue

        h2 = div.find("h2")
        title = h2.get_text(" ", strip=True) if h2 else ""
        if not title:
            continue

        price_el = div.select_one(".a-price .a-offscreen") or div.select_one(
            ".a-price-whole"
        )
        price = _parse_price(price_el.get_text(" ", strip=True)) if price_el else None

        img = div.select_one("img.s-image")
        image = (img.get("src") or "").strip() if img else None

        seen.add(asin)
        results.append(
            {
                "id": asin,
                "title": title,
                "price": price,
                "image": image or None,
                "platform": "Amazon.in",
                "url": f"https://www.amazon.in/dp/{asin}",
            }
        )
        if len(results) >= limit:
            break

    return results, None


def _search_flipkart(query: str, limit: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    url = f"https://www.flipkart.com/search?q={urllib.parse.quote(query)}"
    try:
        html = _fetch(url)
    except Exception as exc:
        return [], f"Flipkart search failed: {exc}"

    if _is_robot(html):
        return [], "Flipkart returned a bot-check page."

    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []
    seen = set()

    for link in soup.find_all("a", href=re.compile(r"/p/itm")):
        href = (link.get("href") or "").strip()
        if not href:
            continue
        clean_url = "https://www.flipkart.com" + href.split("?")[0]
        if clean_url in seen:
            continue

        parent = link.find_parent("div") or link
        title = (link.get("title") or "").strip()
        if not title:
            titled = parent.find(["div", "a"], title=True)
            title = (titled.get("title") if titled else "").strip()
        if not title:
            title = link.get_text(" ", strip=True)
        if not title:
            continue

        text = parent.get_text(" ", strip=True)
        price = _parse_price(text, require_currency=True)

        img = parent.find("img")
        image = None
        if img:
            image = (img.get("src") or img.get("data-src") or "").strip() or None

        seen.add(clean_url)
        results.append(
            {
                "id": hashlib.sha1(clean_url.encode("utf-8")).hexdigest()[:10],
                "title": title,
                "price": price,
                "image": image,
                "platform": "Flipkart",
                "url": clean_url,
            }
        )
        if len(results) >= limit:
            break

    return results, None


def search_products(query: str, limit: int = 8) -> Dict[str, Any]:
    text = (query or "").strip()
    if not text:
        raise ValueError("Search query is empty.")
    if len(text) > 120:
        text = text[:120]

    with ThreadPoolExecutor(max_workers=2) as pool:
        amazon_future = pool.submit(_search_amazon, text, limit)
        flipkart_future = pool.submit(_search_flipkart, text, limit)
        amazon_results, amazon_error = amazon_future.result()
        flipkart_results, flipkart_error = flipkart_future.result()

    amazon_results = [
        item for item in amazon_results if _is_relevant(item.get("title", ""), text)
    ]
    flipkart_results = [
        item for item in flipkart_results if _is_relevant(item.get("title", ""), text)
    ]

    sources = {
        "amazon": "ok" if not amazon_error else amazon_error,
        "flipkart": "ok" if not flipkart_error else flipkart_error,
    }

    results = amazon_results + flipkart_results
    deduped: List[Dict[str, Any]] = []
    seen_keys = set()
    for item in results:
        key = (
            item.get("platform"),
            (item.get("title") or "").strip().lower(),
            item.get("price"),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(item)
    results = deduped
    if results:
        message = None
        if amazon_error or flipkart_error:
            message = "Some sources could not be read; showing the readable results."
        return {
            "status": "ok",
            "results": results,
            "message": message,
            "sources": sources,
        }

    if amazon_error and flipkart_error:
        return {
            "status": "unavailable",
            "results": [],
            "message": (
                "Search is unavailable right now: both Amazon and Flipkart "
                "blocked the request. Paste a product link instead, or retry."
            ),
            "sources": sources,
        }

    empty_message = (
        f'No relevant products found for "{text}". '
        "Try a more specific name, or paste a product link."
    )
    if amazon_error or flipkart_error:
        empty_message += " One source could not be read."
    return {
        "status": "empty",
        "results": [],
        "message": empty_message,
        "sources": sources,
    }
