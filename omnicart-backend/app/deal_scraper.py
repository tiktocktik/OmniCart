import urllib.request
import re
import time
from typing import List, Dict, Any
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

_CACHE_DEALS: List[Dict[str, Any]] = []
_CACHE_TIMESTAMP: float = 0.0
CACHE_TTL_SECONDS = 600.0  # 10 minutes

def infer_deal_category(title: str) -> str:
    """Infer a category from whole words in the title.

    Substring matching used to classify "Stainless Steel" as Fashion (because of
    "tee") and a cleaning spray as Beauty. Whole-word matching keeps the label
    tied to the product type.
    """
    t = title.lower()

    def has(words) -> bool:
        return any(re.search(rf"\b{re.escape(word)}\b", t) for word in words)

    if has([
        "tv", "television", "speaker", "headphone", "earbud", "earphone",
        "power bank", "powerbank", "charger", "cable", "laptop", "ideapad",
        "tablet", "smartwatch", "soundbar", "camera", "monitor", "pc",
    ]):
        return "Electronics & Gadgets"
    if has([
        "mattress", "bed", "pillow", "carpet", "cleaner", "rack", "utensil",
        "cooker", "pressure cooker", "induction", "stove", "mixer", "juicer",
        "blender", "fryer", "knife", "towel", "mat", "sofa", "toaster", "iron",
        "pan", "refrigerator", "fridge", "washing machine", "air conditioner",
        "ac",
    ]):
        return "Home & Kitchen"
    if has([
        "perfume", "deodorant", "deo", "body spray", "lotion", "cream",
        "face wash", "facewash", "shampoo", "serum", "trimmer", "grooming",
    ]):
        return "Beauty & Grooming"
    if has([
        "pant", "trouser", "shirt", "t-shirt", "tshirt", "tee shirt", "dress",
        "jean", "kurta", "kurti", "shoe", "flats", "slipper", "kolhapuri",
        "bag", "luggage", "trolley", "jacket", "clothing", "cotton", "watch",
    ]):
        return "Fashion & Apparel"
    if has([
        "oil", "rice", "tea", "coffee", "food", "snack", "chocolate", "biscuit",
        "almond", "kaju", "dry fruit", "atta", "flour", "milk", "ghee",
    ]):
        return "Grocery & Essentials"
    return "General Goods"

def classify_flash_deal(deal_price: float, regular_price: float, discount: int, heat_score: int = 0, store: str = "") -> Dict[str, Any]:
    savings = round(regular_price - deal_price, 2)
    is_glitch = False
    is_mega = False
    urgency = "NORMAL"
    badge = f"{discount}% OFF"

    # No real struck-through price means no verified discount. Never imply one.
    if discount <= 0 or regular_price <= deal_price:
        return {
            "isGlitch": False,
            "isMegaDrop": False,
            "urgencyLevel": "NORMAL",
            "badge": "DEAL",
            "heatScore": heat_score,
            "savings": 0.0,
        }

    # 1. Digit Boundary Drop Rules
    if regular_price >= 1800 and deal_price < 1000:
        badge = "⚡ 3-DIGIT DROP"
        is_glitch = True
        is_mega = True
        urgency = "EXTREME"
    elif regular_price >= 450 and deal_price < 100:
        badge = "⚡ 2-DIGIT DROP"
        is_glitch = True
        is_mega = True
        urgency = "EXTREME"
    elif regular_price >= 10000 and deal_price < 6000:
        badge = "🔥 4-DIGIT LOOT"
        is_mega = True
        urgency = "HIGH"

    # 2. Extreme Discount Thresholds
    if discount >= 75:
        badge = f"🚨 {discount}% MEGA DROP"
        is_mega = True
        is_glitch = True
        urgency = "EXTREME"
    elif discount >= 60 and not is_glitch:
        badge = f"🔥 {discount}% OFF"
        is_mega = True
        urgency = "HIGH"

    # 3. Community Heat Velocity (DesiDime temp >= 100°)
    if heat_score >= 200:
        urgency = "EXTREME"
        if not is_glitch:
            badge = f"🔥 {heat_score}° HOT LOOT"
            is_mega = True
    elif heat_score >= 100 and not is_glitch:
        badge = f"⚡ {heat_score}° HOT"
        is_mega = True
        if urgency == "NORMAL":
            urgency = "HIGH"

    return {
        "isGlitch": is_glitch,
        "isMegaDrop": is_mega,
        "urgencyLevel": urgency,
        "badge": badge,
        "heatScore": heat_score,
        "savings": savings
    }

def fetch_desidime_deals(limit: int = 20) -> List[Dict[str, Any]]:
    """Scrapes recent community deals from DesiDime. Prices come from the cards."""
    deals = []
    try:
        req = urllib.request.Request("https://www.desidime.com/deals", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=7) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            cards = soup.find_all(class_=re.compile(r"\bdeal-card\b"))
            
            for c in cards:
                a_tag = c.find("a", href=re.compile(r"/deals/[a-z0-9-]+-\d+$"))
                if not a_tag:
                    continue
                raw_title = a_tag.get_text(strip=True)
                title = re.sub(r"^\d+[\s°\u00b0\ufffd\?]*\s*(Check out\s*)?", "", raw_title, flags=re.I).strip()
                if not title or len(title) < 10 or title.startswith("View") or title.startswith("Show"):
                    continue
                
                # Temperature / Upvote extraction from card text
                c_text = c.get_text()
                temp_m = re.findall(r"(\d+)[\u00b0\ufffd\?]", c_text)
                heat_score = int(temp_m[0]) if temp_m else 0

                img_tag = c.find("img")
                if not img_tag:
                    continue
                img_url = img_tag.get("src") or img_tag.get("data-src")
                if not img_url or "placeholder" in img_url or "hotness-" in img_url:
                    continue

                p_tag = c.find(class_=re.compile(r"font-bold.*text-primary"))
                s_tag = c.find(class_=re.compile(r"line-through"))
                if not p_tag:
                    continue
                
                p_digits = re.sub(r"[^\d.]", "", p_tag.get_text())
                if not p_digits:
                    continue
                deal_price = float(p_digits)
                
                s_digits = re.sub(r"[^\d.]", "", s_tag.get_text()) if s_tag else ""
                regular_price = float(s_digits) if s_digits else deal_price
                if regular_price < deal_price:
                    regular_price = deal_price

                discount = (
                    int(round((1 - (deal_price / regular_price)) * 100))
                    if regular_price > deal_price
                    else 0
                )

                st_tag = c.find("a", href=re.compile(r"/stores/"))
                # If the card does not name a store, say where the deal came from,
                # not "Online Store" (which is not a store).
                store_name = st_tag.get_text(strip=True) if st_tag else "DesiDime"

                deal_url = "https://www.desidime.com" + a_tag["href"]
                m_id = re.search(r"-(\d+)$", a_tag["href"])
                deal_id = f"desidime-{m_id.group(1)}" if m_id else f"dd-{len(deals)}"

                flash_meta = classify_flash_deal(
                    deal_price, regular_price, discount, heat_score, store_name
                )

                deals.append({
                    "id": deal_id,
                    "title": title[:90],
                    "store": store_name,
                    "dealPrice": deal_price,
                    "regularPrice": regular_price,
                    "savings": flash_meta["savings"],
                    "discount": discount,
                    "category": infer_deal_category(title),
                    "timeAgo": "",
                    "image": img_url,
                    "badge": flash_meta["badge"],
                    "isMegaDrop": flash_meta["isMegaDrop"],
                    "isGlitch": flash_meta["isGlitch"],
                    "urgencyLevel": flash_meta["urgencyLevel"],
                    "heatScore": heat_score,
                    "url": deal_url,
                    "source": "DesiDime Community"
                })
                
                if len(deals) >= limit:
                    break
    except Exception:
        pass
    return deals

def fetch_dealsmagnet_deals(limit: int = 20) -> List[Dict[str, Any]]:
    """Scrapes recent deals from Dealsmagnet. Prices come from the cards."""
    deals = []
    try:
        req = urllib.request.Request("https://www.dealsmagnet.com/", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=7) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            
            for im in soup.find_all("img", attrs={"data-src": re.compile(r"/images/")}):
                img_src = im["data-src"]
                alt_title = im.get("alt", "").strip()
                
                a_tag = im.find_parent("a") or im.find_next("a", href=re.compile(r"/deal/"))
                if not a_tag or not a_tag.get("href"):
                    continue
                
                p = im
                prices = []
                # "Online" is not a store. Fall back to the aggregator name.
                store_name = "Dealsmagnet"
                for _ in range(5):
                    if p:
                        t = p.get_text(" ", strip=True)
                        m_p = re.findall(r"₹\s*([0-9,]+)", t)
                        if m_p:
                            prices = m_p
                            m_store = re.search(r"\b(Amazon|Flipkart|Myntra|AJIO|Tata\s*CliQ|Nykaa|JioMart|Croma)\b", t, re.I)
                            if m_store:
                                store_name = m_store.group(1).title()
                            break
                        p = p.parent
                
                if not prices:
                    continue
                
                deal_price = float(prices[0].replace(",", ""))
                regular_price = (
                    float(prices[1].replace(",", ""))
                    if len(prices) > 1
                    else deal_price
                )
                if regular_price < deal_price:
                    regular_price = deal_price

                discount = (
                    int(round((1 - (deal_price / regular_price)) * 100))
                    if regular_price > deal_price
                    else 0
                )
                title = alt_title or (a_tag.get_text(strip=True) if a_tag else "Special Deal")
                if len(title) < 10:
                    continue
                
                href = a_tag["href"]
                full_url = href if href.startswith("http") else "https://www.dealsmagnet.com" + href
                slug = href.strip("/").split("/")[-1]

                flash_meta = classify_flash_deal(
                    deal_price, regular_price, discount, 0, store_name
                )

                deals.append({
                    "id": f"dm-{slug[:20]}",
                    "title": title[:90],
                    "store": store_name,
                    "dealPrice": deal_price,
                    "regularPrice": regular_price,
                    "savings": flash_meta["savings"],
                    "discount": discount,
                    "category": infer_deal_category(title),
                    "timeAgo": "",
                    "image": img_src,
                    "badge": flash_meta["badge"],
                    "isMegaDrop": flash_meta["isMegaDrop"],
                    "isGlitch": flash_meta["isGlitch"],
                    "urgencyLevel": flash_meta["urgencyLevel"],
                    "heatScore": 0,
                    "url": full_url,
                    "source": "Dealsmagnet Drops"
                })
                
                if len(deals) >= limit:
                    break
    except Exception:
        pass
    return deals

def get_live_deals(limit: int = 40, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Aggregates and caches deals from public Indian deal aggregators."""
    global _CACHE_DEALS, _CACHE_TIMESTAMP
    
    now = time.time()
    if not force_refresh and _CACHE_DEALS and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return _CACHE_DEALS[:limit]
    
    dm_deals = fetch_dealsmagnet_deals(limit=limit)
    dd_deals = fetch_desidime_deals(limit=limit)
    
    combined = []
    max_len = max(len(dm_deals), len(dd_deals))
    for i in range(max_len):
        if i < len(dm_deals):
            combined.append(dm_deals[i])
        if i < len(dd_deals):
            combined.append(dd_deals[i])
            
    # Include Reddit stream if credentials exist
    try:
        from .social_ingest import fetch_reddit_deals
        reddit_deals = fetch_reddit_deals(limit=8)
        if reddit_deals:
            combined.extend(reddit_deals)
    except Exception:
        pass

    # The same card can appear twice on a source page. Keep one copy.
    seen_ids = set()
    deduped = []
    for deal in combined:
        deal_id = deal.get("id")
        if deal_id:
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)
        deduped.append(deal)
    combined = deduped

    if combined:
        _CACHE_DEALS = combined
        _CACHE_TIMESTAMP = now
        return combined[:limit]
    
    if _CACHE_DEALS:
        return _CACHE_DEALS[:limit]
    
    return []
