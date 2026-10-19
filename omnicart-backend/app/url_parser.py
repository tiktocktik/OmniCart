import re
import urllib.parse
from typing import Tuple, Optional

def clean_and_normalize_url(raw_input: str) -> Tuple[str, str, Optional[str]]:
    """
    Identifies if input is a URL or search query.
    If URL, strips all tracking & affiliate query parameters (ref, utm_*, tag, etc.)
    Returns (cleaned_url_or_query, platform_type, item_id)
    """
    raw_input = raw_input.strip()
    
    # Check if raw input is a direct Amazon ASIN (e.g. B0GJV4XW2B)
    if re.match(r'^[A-Z0-9]{10}$', raw_input, re.I):
        asin = raw_input.upper()
        return f"https://www.amazon.in/dp/{asin}", "Amazon.in", asin

    # Check if input is a URL
    if not (raw_input.startswith("http://") or raw_input.startswith("https://") or "www." in raw_input or ".com" in raw_input or ".in" in raw_input):
        return raw_input, "SEARCH_QUERY", None

    # Handle missing scheme
    if not (raw_input.startswith("http://") or raw_input.startswith("https://")):
        raw_input = "https://" + raw_input

    parsed = urllib.parse.urlparse(raw_input)
    domain = parsed.netloc.lower()
    path = parsed.path
    
    # 1. Amazon India
    if "amazon.in" in domain or "amzn.to" in domain:
        # Match ASIN regex (10 uppercase alphanumeric chars following /dp/ or /gp/product/)
        asin_match = re.search(r'(?:/dp/|/gp/product/|/d/)([A-Z0-9]{10})', path + "?" + parsed.query)
        if asin_match:
            asin = asin_match.group(1)
            canonical = f"https://www.amazon.in/dp/{asin}"
            return canonical, "Amazon.in", asin
        return raw_input, "Amazon.in", None

    # 2. Flipkart
    if "flipkart.com" in domain:
        # Check query params for 'pid='
        query_dict = urllib.parse.parse_qs(parsed.query)
        pid = query_dict.get("pid", [None])[0]
        
        # Check path for /p/itm...
        itm_match = re.search(r'/(?:p/)?(itm[a-zA-Z0-9]+)', path)
        item_id = pid or (itm_match.group(1) if itm_match else None)
        
        clean_path = path.split("?")[0]
        canonical = f"https://www.flipkart.com{clean_path}"
        if item_id:
            canonical += f"?pid={item_id}"
        return canonical, "Flipkart", item_id

    # 3. Myntra
    if "myntra.com" in domain:
        id_match = re.search(r'/(\d{6,})(?:/buy)?', path)
        item_id = id_match.group(1) if id_match else None
        clean_path = path.split("?")[0]
        canonical = f"https://www.myntra.com{clean_path}"
        return canonical, "Myntra", item_id

    # 4. AJIO
    if "ajio.com" in domain:
        id_match = re.search(r'/p/([0-9a-zA-Z_]+)', path)
        item_id = id_match.group(1) if id_match else None
        clean_path = path.split("?")[0]
        canonical = f"https://www.ajio.com{clean_path}"
        return canonical, "AJIO", item_id

    # 5. Nykaa Fashion & Nykaa
    if "nykaafashion.com" in domain:
        id_match = re.search(r'/p/(\d+)', path)
        item_id = id_match.group(1) if id_match else None
        clean_path = path.split("?")[0]
        canonical = f"https://www.nykaafashion.com{clean_path}"
        return canonical, "Nykaa Fashion", item_id
    if "nykaa.com" in domain:
        id_match = re.search(r'/p/(\d+)', path)
        item_id = id_match.group(1) if id_match else None
        clean_path = path.split("?")[0]
        canonical = f"https://www.nykaa.com{clean_path}"
        return canonical, "Nykaa", item_id

    # 6. Tata CliQ & Tata Simply Better
    if "tatacliq.com" in domain:
        clean_url = f"https://www.tatacliq.com{parsed.path}"
        slug = parsed.path.strip("/").split("/")[-1]
        return clean_url, "Tata CliQ", slug
    if "tatasimplybetter.com" in domain:
        clean_url = f"https://www.tatasimplybetter.com{parsed.path}"
        slug = parsed.path.strip("/").split("/")[-1]
        return clean_url, "Tata Simply Better", slug

    # 7. Croma
    if "croma.com" in domain:
        id_match = re.search(r'/p/(\d+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.croma.com{clean_path}"
        return canonical, "Croma", item_id

    # 8. Reliance Digital
    if "reliancedigital.in" in domain:
        id_match = re.search(r'/p/(\d+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.reliancedigital.in{clean_path}"
        return canonical, "Reliance Digital", item_id

    # 9. Vijay Sales
    if "vijaysales.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.vijaysales.com{clean_path}"
        return canonical, "Vijay Sales", slug

    # 10. Uniqlo India
    if "uniqlo.com" in domain:
        id_match = re.search(r'/products/([A-Z0-9_-]+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.uniqlo.com{clean_path}"
        return canonical, "Uniqlo", item_id

    # 11. Snitch
    if "snitch.co.in" in domain or "snitch.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.snitch.co.in{clean_path}"
        return canonical, "Snitch", slug

    # 12. Style Union
    if "styleunion.in" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://styleunion.in{clean_path}"
        return canonical, "Style Union", slug

    # 13. The Souled Store
    if "thesouledstore.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.thesouledstore.com{clean_path}"
        return canonical, "The Souled Store", slug

    # 14. Pantaloons
    if "pantaloons.com" in domain:
        id_match = re.search(r'-(\d+)\.html', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.pantaloons.com{clean_path}"
        return canonical, "Pantaloons", item_id

    # 15. Ani Clothing
    if "aniclothing.in" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://aniclothing.in{clean_path}"
        return canonical, "Ani Clothing", slug

    # 16. Fabindia
    if "fabindia.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.fabindia.com{clean_path}"
        return canonical, "Fabindia", slug

    # 17. Lifestyle Stores
    if "lifestylestores.com" in domain:
        id_match = re.search(r'/p/(\d+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.lifestylestores.com{clean_path}"
        return canonical, "Lifestyle", item_id

    # 18. Max Fashion & Westside
    if "maxfashion" in domain:
        clean_path = path.split("?")[0]
        canonical = f"https://www.maxfashion.in{clean_path}"
        slug = clean_path.strip("/").split("/")[-1]
        return canonical, "Max Fashion", slug
    if "westside" in domain:
        clean_path = path.split("?")[0]
        canonical = f"https://www.westside.com{clean_path}"
        slug = clean_path.strip("/").split("/")[-1]
        return canonical, "Westside", slug

    # 19. Meesho
    if "meesho.com" in domain:
        id_match = re.search(r'/p/([0-9a-zA-Z]+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.meesho.com{clean_path}"
        return canonical, "Meesho", item_id

    # 20. Footwear & Shoe Stores
    if "baccabucci.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://baccabucci.com{clean_path}"
        return canonical, "Bacca Bucci", slug

    if "redtape.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://redtape.com{clean_path}"
        return canonical, "Red Tape", slug

    if "bata.com" in domain or "bata.in" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.bata.com{clean_path}"
        return canonical, "Bata", slug

    if "woodlandworldwide.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.woodlandworldwide.com{clean_path}"
        return canonical, "Woodland", slug

    if "campusshoes.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.campusshoes.com{clean_path}"
        return canonical, "Campus Shoes", slug

    if "metroshoes.com" in domain or "metroshoes.net" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://metroshoes.com{clean_path}"
        return canonical, "Metro Shoes", slug

    if "mochishoes.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://mochishoes.com{clean_path}"
        return canonical, "Mochi", slug

    if "puma.com" in domain:
        id_match = re.search(r'/pd/[^/]+/([0-9a-zA-Z_]+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://in.puma.com{clean_path}"
        return canonical, "Puma", item_id

    if "nike.com" in domain:
        id_match = re.search(r'/t/[^/]+/([0-9a-zA-Z_-]+)', path)
        item_id = id_match.group(1) if id_match else parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.nike.com{clean_path}"
        return canonical, "Nike", item_id

    if "adidas.co.in" in domain or "adidas.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://www.adidas.co.in{clean_path}"
        return canonical, "Adidas", slug

    # 21. Quick Commerce
    if "zepto" in domain or "zeptonow.com" in domain:
        clean_url = f"https://{parsed.netloc}{parsed.path}"
        slug = parsed.path.strip("/").split("/")[-1]
        return clean_url, "Zepto", slug

    if "blinkit.com" in domain:
        clean_url = f"https://{parsed.netloc}{parsed.path}"
        slug = parsed.path.strip("/").split("/")[-1]
        return clean_url, "Blinkit", slug

    # 6. Universal / Any other store
    # Strip tracking query params
    tracking_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "tag", "affid", "clickid"}
    query_dict = urllib.parse.parse_qs(parsed.query)
    filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in tracking_params}
    new_query_string = urllib.parse.urlencode(filtered_query, doseq=True)
    
    clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query_string, parsed.fragment))
    return clean_url, "Universal", None
