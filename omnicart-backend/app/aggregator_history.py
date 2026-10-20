import hashlib
import json
import time
import base64
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .models import PricePoint

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

SECRET_STR = os.environ.get("PRICEHISTORY_SECRET", "").strip()
KEY = hashlib.sha256(SECRET_STR.encode("utf-8")).digest() if SECRET_STR else None
aesgcm = AESGCM(KEY) if KEY else None

# Optional operator-provided slugs. Empty by default: the signed API resolves
# real URLs without shipping demo-product mappings.
CURATED_SLUG_MAP: Dict[str, str] = {}

def generate_signature(url_str: str, body: str = "") -> Optional[str]:
    """Generates AES-GCM encrypted signature for PriceHistoryApp API."""
    if not aesgcm:
        return None
    iv = os.urandom(12)
    payload = json.dumps({
        "u": len(url_str),
        "b": len(body),
        "t": int(time.time() * 1000)
    }, separators=(',', ':')).encode("utf-8")
    
    ciphertext = aesgcm.encrypt(iv, payload, None)
    iv_b64 = base64.b64encode(iv).decode("utf-8")
    ct_b64 = base64.b64encode(ciphertext).decode("utf-8")
    return f"{iv_b64}.{ct_b64}"

def get_product_slug_from_api(canonical_url: str) -> Optional[str]:
    """Queries PriceHistoryApp slug endpoint with signed authorization."""
    try:
        encoded_param = urllib.parse.quote(canonical_url, safe='')
        url_path = f"/api/products/slug-from-url?url={encoded_param}"
        sig = generate_signature(url_path, "")
        if not sig:
            return None
        
        full_url = f"https://pricehistoryapp.com{url_path}"
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'X-Req-Signature': sig,
            'Referer': 'https://pricehistoryapp.com/'
        }
        
        req = urllib.request.Request(full_url, headers=req_headers)
        resp = urllib.request.urlopen(req, timeout=5)
        res_data = json.loads(resp.read().decode('utf-8'))
        return res_data.get("slug")
    except Exception as e:
        return None

def extract_price_history_from_html(html: str) -> List[Dict[str, Any]]:
    """Extracts raw priceHistory JSON array from page HTML."""
    idx = html.find('priceHistory')
    if idx == -1:
        return []
    start = html.find('[', idx)
    if start == -1:
        return []
    
    depth = 0
    end = -1
    for i in range(start, len(html)):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    if end != -1:
        raw_json = html[start:end]
        raw_json = raw_json.replace('\\"', '"').replace('\\\\', '\\')
        try:
            return json.loads(raw_json)
        except Exception:
            pass
    return []

def sample_time_series(raw_points: List[Dict[str, Any]], days_limit: Optional[int], max_samples: int = 15) -> List[PricePoint]:
    """Downsamples high-density daily recordings to structured time-series points."""
    parsed = []
    for pt in raw_points:
        try:
            d = datetime.strptime(pt['date'], "%Y-%m-%d")
            p = float(pt['price'])
            parsed.append((d, p))
        except Exception:
            continue

    parsed.sort(key=lambda x: x[0])
    if not parsed:
        return []

    if days_limit:
        cutoff = parsed[-1][0] - timedelta(days=days_limit)
        filtered = [pt for pt in parsed if pt[0] >= cutoff]
        if not filtered:
            filtered = parsed[-days_limit:]
    else:
        filtered = parsed

    if len(filtered) <= max_samples:
        selected = filtered
    else:
        step = len(filtered) / (max_samples - 1)
        selected = [filtered[int(i * step)] for i in range(max_samples - 1)]
        if filtered[-1] not in selected:
            selected.append(filtered[-1])

    result: List[PricePoint] = []
    all_prices = [p for _, p in selected]
    min_price = min(all_prices) if all_prices else 0

    for idx, (dt, pr) in enumerate(selected):
        if days_limit and days_limit <= 30:
            date_str = dt.strftime("%b %d")
        elif days_limit and days_limit <= 365:
            date_str = dt.strftime("%b %Y")
        else:
            date_str = dt.strftime("%b %Y")

        if idx == len(selected) - 1:
            date_str = "Live Now"

        label = None
        if pr == min_price and pr < max(all_prices):
            label = "All-Time Low"
        elif idx == len(selected) - 1:
            label = f"Live Now (Rs {int(pr)})"

        result.append(PricePoint(
            date=date_str,
            price=pr,
            label=label,
            is_glitch=False
        ))

    return result

def fetch_real_aggregator_history(query_or_url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches genuine real historical price points from Indian aggregator.
    """
    slug = None
    lower_query = query_or_url.lower()

    # 1. Check any operator-provided curated map (empty by default).
    for k, s in CURATED_SLUG_MAP.items():
        if k in lower_query:
            slug = s
            break

    # 2. Try signed API for Amazon / Flipkart URLs
    if not slug and ("amazon.in" in lower_query or "flipkart.com" in lower_query):
        slug = get_product_slug_from_api(query_or_url)

    if not slug:
        return None

    pha_url = f"https://pricehistoryapp.com/product/{slug}"
    try:
        req = urllib.request.Request(pha_url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
        raw_points = extract_price_history_from_html(html)
        if not raw_points:
            return None

        prices = [float(p['price']) for p in raw_points if 'price' in p and p['price'] > 0]
        if not prices:
            return None

        all_time_low = min(prices)
        all_time_high = max(prices)
        first_recorded_date = raw_points[0].get("date", "Unknown")

        history = {
            "1M": sample_time_series(raw_points, days_limit=30, max_samples=8),
            "6M": sample_time_series(raw_points, days_limit=180, max_samples=10),
            "1Y": sample_time_series(raw_points, days_limit=365, max_samples=12),
            "3Y": sample_time_series(raw_points, days_limit=1095, max_samples=14),
            "ALL": sample_time_series(raw_points, days_limit=None, max_samples=16),
        }

        return {
            "all_time_low": all_time_low,
            "all_time_high": all_time_high,
            "history": history,
            "source_url": pha_url,
            "total_points": len(raw_points),
            "first_recorded_date": first_recorded_date,
            "is_real_history": True,
            "history_source": "VERIFIED_AGGREGATOR"
        }
    except Exception as e:
        print(f"Error fetching real price history for {slug}: {e}")
        return None
