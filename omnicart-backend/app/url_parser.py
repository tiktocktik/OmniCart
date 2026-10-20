"""Input classification and URL normalisation.

Rules:
- A bare ASIN is only accepted when it matches ^B0[A-Z0-9]{8}$.
- A URL is detected from its parsed hostname, never from ".in"/".com" substrings.
- Store hosts match exactly or by dot-suffix (amazon.in != notamazon.in).
- Known short links are expanded once, with a timeout.
"""

import re
import urllib.parse
import urllib.request
from typing import Optional, Tuple

ASIN_RE = re.compile(r"^B0[A-Z0-9]{8}$", re.I)
AMAZON_PATH_ASIN_RE = re.compile(
    r"/(?:dp|gp/product|d)/([A-Z0-9]{10})(?:[/?]|$)", re.I
)

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "tag",
    "affid",
    "clickid",
    "gclid",
    "fbclid",
}

SHORT_LINK_HOSTS = ("amzn.to", "dl.flipkart.com", "fkrt.it", "fkrt.co")

# platform, domains, canonical host
STORE_RULES = [
    ("Amazon.in", ("amazon.in", "amazon.com"), "www.amazon.in"),
    ("Flipkart", ("flipkart.com",), "www.flipkart.com"),
    ("Myntra", ("myntra.com",), "www.myntra.com"),
    ("AJIO", ("ajio.com",), "www.ajio.com"),
    ("Nykaa Fashion", ("nykaafashion.com",), "www.nykaafashion.com"),
    ("Nykaa", ("nykaa.com",), "www.nykaa.com"),
    ("Tata CliQ", ("tatacliq.com",), "www.tatacliq.com"),
    ("Tata Simply Better", ("tatasimplybetter.com",), "www.tatasimplybetter.com"),
    ("Croma", ("croma.com",), "www.croma.com"),
    ("Reliance Digital", ("reliancedigital.in",), "www.reliancedigital.in"),
    ("Vijay Sales", ("vijaysales.com",), "www.vijaysales.com"),
    ("Uniqlo", ("uniqlo.com",), "www.uniqlo.com"),
    ("Snitch", ("snitch.co.in", "snitch.com"), "www.snitch.co.in"),
    ("Style Union", ("styleunion.in",), "styleunion.in"),
    ("The Souled Store", ("thesouledstore.com",), "www.thesouledstore.com"),
    ("Pantaloons", ("pantaloons.com",), "www.pantaloons.com"),
    ("Ani Clothing", ("aniclothing.in",), "aniclothing.in"),
    ("Fabindia", ("fabindia.com",), "www.fabindia.com"),
    ("Lifestyle", ("lifestylestores.com",), "www.lifestylestores.com"),
    ("Max Fashion", ("maxfashion.in", "maxfashion.com"), "www.maxfashion.in"),
    ("Westside", ("westside.com",), "www.westside.com"),
    ("Meesho", ("meesho.com",), "www.meesho.com"),
    ("Bacca Bucci", ("baccabucci.com",), "baccabucci.com"),
    ("Red Tape", ("redtape.com",), "redtape.com"),
    ("Bata", ("bata.com", "bata.in"), "www.bata.com"),
    ("Woodland", ("woodlandworldwide.com",), "www.woodlandworldwide.com"),
    ("Campus Shoes", ("campusshoes.com",), "www.campusshoes.com"),
    ("Metro Shoes", ("metroshoes.com", "metroshoes.net"), "metroshoes.com"),
    ("Mochi", ("mochishoes.com",), "mochishoes.com"),
    ("Puma", ("puma.com",), "in.puma.com"),
    ("Nike", ("nike.com",), "www.nike.com"),
    ("Adidas", ("adidas.co.in", "adidas.com"), "www.adidas.co.in"),
    ("Zepto", ("zeptonow.com", "zepto.com"), None),
    ("Blinkit", ("blinkit.com",), None),
]


def _host_matches(host: str, domain: str) -> bool:
    host = (host or "").lower().rstrip(".")
    domain = (domain or "").lower().rstrip(".")
    return host == domain or host.endswith("." + domain)


def _match_store(host: str) -> Optional[Tuple[str, Optional[str]]]:
    for platform, domains, canonical_host in STORE_RULES:
        for domain in domains:
            if _host_matches(host, domain):
                return platform, canonical_host
    return None


def _expand_short_url(url: str, timeout: float = 6.0) -> Optional[str]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            final_url = response.geturl()
            return final_url or None
    except Exception:
        return None


def _clean_url(parsed: urllib.parse.ParseResult) -> str:
    query = urllib.parse.parse_qs(parsed.query)
    filtered = {
        k: v for k, v in query.items() if k.lower() not in TRACKING_PARAMS
    }
    new_query = urllib.parse.urlencode(filtered, doseq=True)
    return urllib.parse.urlunparse(
        (
            parsed.scheme or "https",
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            "",
        )
    )


def _last_path_id(path: str) -> Optional[str]:
    segments = [s for s in path.strip("/").split("/") if s]
    if not segments:
        return None
    last = segments[-1]
    last = re.sub(r"\.(html?|php)$", "", last, flags=re.I)
    return last or None


def _has_product_identity(url: str, host: str) -> bool:
    """A short link must land on a product page, not a homepage or search page."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or ""
    lower_host = host.lower()
    if "amazon." in lower_host:
        return bool(
            re.search(r"/(?:dp|gp/product|gp/aw/d)/[A-Z0-9]{10}", path, re.I)
        )
    if "flipkart." in lower_host:
        query = urllib.parse.parse_qs(parsed.query)
        return bool(re.search(r"/p/itm[a-zA-Z0-9]+", path)) or bool(query.get("pid"))
    if not path or path == "/":
        return False
    return not path.lower().startswith(("/search", "/s"))


def clean_and_normalize_url(raw_input: str) -> Tuple[str, str, Optional[str]]:
    """Return (cleaned_url_or_query, platform, item_id).

    Text that is not a URL or a valid ASIN is returned as ``SEARCH_QUERY``.
    """
    text = (raw_input or "").strip()
    if not text:
        return "", "SEARCH_QUERY", None

    # Direct ASIN: only the B0... form, so words like "headphones" are searches.
    if ASIN_RE.fullmatch(text):
        asin = text.upper()
        return f"https://www.amazon.in/dp/{asin}", "Amazon.in", asin

    candidate = text if "://" in text else "https://" + text
    parsed = urllib.parse.urlparse(candidate)
    host = (parsed.hostname or "").strip().lower().rstrip(".")

    # A real URL needs a dotted hostname and no whitespace.
    if not host or "." not in host or " " in host:
        return text, "SEARCH_QUERY", None

    # Expand known short links once. If expansion fails, say so explicitly.
    if any(_host_matches(host, h) for h in SHORT_LINK_HOSTS):
        final_url = _expand_short_url(candidate)
        if not final_url:
            return candidate, "SHORT_LINK", None
        parsed = urllib.parse.urlparse(final_url)
        host = (parsed.hostname or "").strip().lower().rstrip(".")
        # An expired/invalid short link can redirect to a store homepage. That
        # is not a product, so keep the original short link and say so.
        if not _has_product_identity(final_url, host):
            return candidate, "SHORT_LINK", None

    store = _match_store(host)

    # Amazon: extract the ASIN from the path.
    if store and store[0] == "Amazon.in":
        asin_match = AMAZON_PATH_ASIN_RE.search(parsed.path)
        if asin_match:
            asin = asin_match.group(1).upper()
            return f"https://www.amazon.in/dp/{asin}", "Amazon.in", asin
        return _clean_url(parsed), "Amazon.in", None

    # Flipkart: preserve the pid when present, otherwise the /p/itm... id.
    if store and store[0] == "Flipkart":
        query = urllib.parse.parse_qs(parsed.query)
        pid = (query.get("pid") or [None])[0]
        itm_match = re.search(r"/(?:p/)?(itm[a-zA-Z0-9]+)", parsed.path)
        item_id = pid or (itm_match.group(1) if itm_match else None)
        canonical = f"https://www.flipkart.com{parsed.path}"
        if pid:
            canonical += f"?pid={pid}"
        return canonical, "Flipkart", item_id

    if store:
        platform, canonical_host = store
        if canonical_host is None:
            canonical_host = parsed.netloc.lower()
        canonical = f"https://{canonical_host}{parsed.path}"
        return canonical, platform, _last_path_id(parsed.path)

    # Any other site: keep the real host, strip tracking only.
    return _clean_url(parsed), "Universal", _last_path_id(parsed.path)
