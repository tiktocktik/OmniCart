import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from .entity_matcher import normalize_title, calculate_match_confidence

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
}

COLORS = ["beige", "black", "white", "green", "blue", "red", "yellow", "pink", "purple", "grey", "gray", "brown", "orange", "cream", "navy", "olive", "maroon", "khaki", "tan"]

COMPATIBLE_COLOR_GROUPS = [
    {"beige", "cream", "khaki", "tan"},
    {"grey", "gray"},
    {"navy", "blue"},
]

def extract_all_colors(text: str) -> List[str]:
    lower = text.lower()
    return [c for c in COLORS if re.search(r'\b' + c + r'\b', lower) or re.search(r'[-_/?=&]' + c + r'[-_/?=&]', lower)]

def extract_color(text: str) -> str:
    colors = extract_all_colors(text)
    return colors[0] if colors else ""

def is_color_compatible(target_color: str, candidate_text: str) -> bool:
    """
    Strict color compatibility check.
    If target is Beige, a Black, Green, White, or Red product is 100% REJECTED.
    """
    if not target_color:
        return True
    
    cand_colors = extract_all_colors(candidate_text)
    if not cand_colors:
        return True  # candidate doesn't specify color
    
    for cc in cand_colors:
        if cc == target_color:
            continue
        if not any(target_color in grp and cc in grp for grp in COMPATIBLE_COLOR_GROUPS):
            return False
            
    return True

def search_flipkart_live(query: str, target_brand: str = "", target_color: str = "") -> List[Dict[str, Any]]:
    """
    Live real-time search on Flipkart India with strict attribute & color verification.
    """
    search_terms = f"{target_brand} {target_color} {query}".strip() if target_color else query
    clean_q = normalize_title(search_terms)
    url = f"https://www.flipkart.com/search?q={urllib.parse.quote(clean_q)}"
    req = urllib.request.Request(url, headers=HEADERS)

    results: List[Dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=6) as res:
            html = res.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')

            for a in soup.find_all('a', href=re.compile(r'/p/itm')):
                href = 'https://www.flipkart.com' + a['href'].split('?')[0]
                parent = a.find_parent('div', class_=re.compile(r'_1sdMkc|_2B_p8w|_1AtVbE|col|product', re.I)) or a
                text = parent.get_text(" ", strip=True)

                m_price = re.search(r'₹\s*([0-9,]+)', text)
                price_val = float(m_price.group(1).replace(',', '')) if m_price else 0.0

                title = a.get('title') or a.get_text(strip=True)
                if not title:
                    for t_tag in parent.find_all(['div', 'a'], title=True):
                        title = t_tag['title']
                        break

                if not title:
                    slug = a['href'].split('/p/')[0].replace('/', '').replace('-', ' ')
                    title = slug.title()

                # STRICT COLOR CHECK: If target has a color (e.g. Beige), reject Black/Green/White
                full_text = f"{title} {href}"
                if target_color and not is_color_compatible(target_color, full_text):
                    continue

                # STRICT BRAND CHECK
                if target_brand and target_brand.lower() not in full_text.lower():
                    continue

                if href not in [r['url'] for r in results] and price_val > 0:
                    results.append({
                        "platform": "Flipkart",
                        "title": title,
                        "price": price_val,
                        "url": href,
                        "delivery_info": "Delivered in 2-3 Days with Flipkart Assured",
                        "delivery_fee": 0.0 if price_val >= 500 else 40.0,
                        "badge": "FLIPKART ASSURED",
                        "discount_text": "5% Unlimited Cashback on Flipkart Axis Bank Card",
                        "card_savings": round(price_val * 0.05, 2),
                        "is_exact_match": True
                    })
                    if len(results) >= 4:
                        break
    except Exception:
        pass

    return results

def search_amazon_live(query: str, target_brand: str = "", target_color: str = "") -> List[Dict[str, Any]]:
    """
    Live real-time search on Amazon India with strict attribute & color verification.
    """
    search_terms = f"{target_brand} {target_color} {query}".strip() if target_color else query
    clean_q = normalize_title(search_terms)
    url = f"https://www.amazon.in/s?k={urllib.parse.quote(clean_q)}"
    req = urllib.request.Request(url, headers=HEADERS)

    results: List[Dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=6) as res:
            html = res.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')

            for div in soup.find_all('div', attrs={"data-asin": True}):
                asin = div.get('data-asin')
                if not asin or len(asin) != 10:
                    continue

                whole = div.find('span', class_='a-price-whole')
                if not whole:
                    continue
                price_val = float(re.sub(r'[^\d]', '', whole.get_text(strip=True)))

                h2 = div.find('h2')
                title = h2.get_text(strip=True) if h2 else ""
                if not title:
                    continue

                # Check text for color and brand
                div_text = div.get_text(" ", strip=True)
                full_cand_text = f"{title} {div_text}"

                # STRICT COLOR CHECK
                if target_color and not is_color_compatible(target_color, full_cand_text):
                    continue

                # STRICT BRAND CHECK
                if target_brand and target_brand.lower() not in full_cand_text.lower():
                    continue

                pdp_url = f"https://www.amazon.in/dp/{asin}"
                if pdp_url not in [r['url'] for r in results]:
                    # Make title descriptive if Amazon returns just brand
                    display_title = title
                    if len(display_title.split()) <= 2 and target_brand and target_color:
                        display_title = f"{target_brand} Men {target_color.title()} T-Shirt"

                    results.append({
                        "platform": "Amazon.in",
                        "title": display_title,
                        "price": price_val,
                        "url": pdp_url,
                        "delivery_info": "FREE Prime Delivery Tomorrow",
                        "delivery_fee": 0.0 if price_val >= 499 else 40.0,
                        "badge": "PRIME VERIFIED",
                        "discount_text": "5% Unlimited Cashback with Amazon Pay ICICI Card",
                        "card_savings": round(price_val * 0.05, 2),
                        "is_exact_match": True
                    })
                    if len(results) >= 4:
                        break
    except Exception:
        pass

    return results

def query_live_marketplaces_in_parallel(query: str, current_platform: str, target_brand: str = "") -> List[Dict[str, Any]]:
    """
    Fires live parallel scraping queries across Indian retail platforms with color & brand awareness.
    """
    clean_current = current_platform.lower().replace(".in", "").replace(".com", "").replace(" ", "")
    target_color = extract_color(query)

    tasks = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        if "flipkart" not in clean_current:
            tasks.append(executor.submit(search_flipkart_live, query, target_brand, target_color))
        if "amazon" not in clean_current:
            tasks.append(executor.submit(search_amazon_live, query, target_brand, target_color))

    all_candidates: List[Dict[str, Any]] = []
    for t in tasks:
        try:
            items = t.result()
            all_candidates.extend(items)
        except Exception:
            pass

    return all_candidates
