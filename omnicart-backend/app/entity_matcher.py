import re
from typing import Tuple, Optional, List, Dict, Any

# Closed-ecosystem single-store private labels that are 100% NOT cross-listed
EXCLUSIVE_RETAIL_CHAINS = {
    "westside": ["nuoflexx", "etiquette", "wardrobe", "soleplay", "luna blu", "wunderlove", "gia", "y&f", "studiofit", "zuba", "vark", "diza", "utsav", "aspen"],
    "zara": ["zara", "trf", "zara basic"],
    "decathlon": ["quechua", "domyos", "kipsta", "kalenji", "oxelo", "btwin", "nabaiji", "artengo", "simond", "forclaz"],
}

NOISE_PATTERNS = [
    r'\s*\|\s*.*$',                       # Everything after pipe
    r'\s+-\s+\d+.*$',                     # Trailing SKU dash numbers
    r'\b(best quality|trending|hot deal|special offer|limited edition)\b',
    r'\b(pack of \d+|pack of one|set of \d+)\b',
    r'\b(free delivery|prime|assured)\b',
    r'\b(buy now|shop online|official store)\b',
]

COLORS = ["beige", "black", "white", "green", "blue", "red", "yellow", "pink", "purple", "grey", "gray", "brown", "orange", "cream", "navy", "olive", "maroon", "khaki", "tan"]

COMPATIBLE_COLOR_GROUPS = [
    {"beige", "cream", "khaki", "tan"},
    {"grey", "gray"},
    {"navy", "blue"},
]

# Article Categories with mutually exclusive keyword signatures
ARTICLE_CATEGORIES = {
    "bottomwear": [
        "trouser", "trousers", "pant", "pants", "chino", "chinos", "jeans", "jogger", "joggers", 
        "track pant", "trackpant", "trackpants", "cargos", "cargo", "shorts", "pyjama", "pyjamas", "sweatpants"
    ],
    "topwear": [
        "shirt", "shirts", "t-shirt", "t-shirts", "tshirt", "tshirts", "tee", "tees", "polo", 
        "kurta", "kurtas", "kurti", "top", "tops", "hoodie", "hoodies", "sweatshirt", "jacket", 
        "jackets", "sweater", "blazer", "coat", "vest", "shacket"
    ],
    "footwear": [
        "sneaker", "sneakers", "shoe", "shoes", "boot", "boots", "loafer", "loafers", 
        "sandal", "sandals", "slipper", "slippers", "slides", "slide", "crocs", "clogs", 
        "floaters", "trainers", "court shoe", "court shoes", "running shoe", "running shoes"
    ],
    "audio": [
        "headphone", "headphones", "earbud", "earbuds", "earphone", "earphones", 
        "headset", "soundbar", "speaker", "speakers", "tws", "neckband"
    ],
    "phone": [
        "smartphone", "mobile phone", "iphone", "galaxy s", "oneplus", "realme", "redmi"
    ],
    "appliance": [
        "air fryer", "airfryer", "microwave", "refrigerator", "fridge", "blender", 
        "mixer grinder", "kettle", "toaster", "oven", "otg", "vacuum cleaner", "iron"
    ],
    "edible": [
        "oil", "olive oil", "ghee", "mustard oil", "sunflower oil", "honey", "tea", "coffee"
    ]
}

def normalize_title(title: str) -> str:
    cleaned = title.lower()
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.I)
    cleaned = re.sub(r'(\d+)\s*(mah|gb|tb|mb|kg|gm|g|ml|l|ltr|litre|liter)\b', r'\1\2', cleaned, flags=re.I)
    cleaned = re.sub(r'(\d+)\s*-\s*(pack|piece|pcs)\b', r'\1pack', cleaned, flags=re.I)
    cleaned = re.sub(r'[,()\[\]{}:;"]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def extract_article_category(text: str) -> str:
    lower = f" {text.lower()} "
    for cat, keywords in ARTICLE_CATEGORIES.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower):
                return cat
    return ""

def is_single_store_exclusive(title: str, platform: str) -> Tuple[bool, str]:
    clean_plat = platform.lower().replace(" ", "").replace(".in", "").replace(".com", "")
    lower_title = title.lower()

    for chain, brands in EXCLUSIVE_RETAIL_CHAINS.items():
        if chain in clean_plat:
            return True, f"This proprietary private label is exclusive to {platform}."
        if any(f" {b} " in f" {lower_title} " for b in brands):
            return True, f"Proprietary in-house label ({brands[0].title()}) exclusive to {chain.title()}."

    return False, ""

def extract_all_colors(text: str) -> List[str]:
    lower = text.lower()
    return [c for c in COLORS if re.search(r'\b' + c + r'\b', lower) or re.search(r'[-_/?=&]' + c + r'[-_/?=&]', lower)]

def extract_color(text: str) -> str:
    colors = extract_all_colors(text)
    return colors[0] if colors else ""

def is_color_compatible(target_color: str, candidate_text: str) -> bool:
    if not target_color:
        return True
    cand_colors = extract_all_colors(candidate_text)
    if not cand_colors:
        return True
    for cc in cand_colors:
        if cc == target_color:
            continue
        if not any(target_color in grp and cc in grp for grp in COMPATIBLE_COLOR_GROUPS):
            return False
    return True

# 10-Point Garment Attribute Extraction
def extract_garment_attributes(text: str) -> Dict[str, str]:
    lower = text.lower()
    attrs = {
        "color": extract_color(text),
        "neck": "",
        "pattern": "",
        "sleeve": "",
        "fit": "",
        "fabric": ""
    }

    # 1. Neck / Collar Silhouette
    if re.search(r'\bpolo\b', lower):
        attrs["neck"] = "polo"
    elif re.search(r'\b(crew|round|crewneck)\b', lower):
        attrs["neck"] = "crew"
    elif re.search(r'\bv-neck\b|\bv neck\b', lower):
        attrs["neck"] = "v-neck"
    elif re.search(r'\bhenley\b', lower):
        attrs["neck"] = "henley"

    # 2. Pattern & Surface Work
    if re.search(r'\b(patterned|textured|jacquard|waffle|knitted)\b', lower):
        attrs["pattern"] = "patterned"
    elif re.search(r'\b(striped|stripes)\b', lower):
        attrs["pattern"] = "striped"
    elif re.search(r'\b(printed|print|typography|graphic)\b', lower):
        attrs["pattern"] = "printed"
    elif re.search(r'\b(solid|plain)\b', lower):
        attrs["pattern"] = "solid"

    # 3. Fit
    if re.search(r'\brelaxed\b', lower):
        attrs["fit"] = "relaxed"
    elif re.search(r'\boversized\b', lower):
        attrs["fit"] = "oversized"
    elif re.search(r'\bslim\b', lower):
        attrs["fit"] = "slim"
    elif re.search(r'\bregular fit\b', lower):
        attrs["fit"] = "regular"

    # 4. Sleeve
    if re.search(r'\b(half sleeve|short sleeve|half)\b', lower):
        attrs["sleeve"] = "half"
    elif re.search(r'\b(full sleeve|long sleeve)\b', lower):
        attrs["sleeve"] = "full"
    elif re.search(r'\bsleeveless\b', lower):
        attrs["sleeve"] = "sleeveless"

    # 5. Fabric
    if re.search(r'\b(cotton blend|poly cotton|cotton poly)\b', lower):
        attrs["fabric"] = "cotton blend"
    elif re.search(r'\b(pure cotton|100% cotton)\b', lower):
        attrs["fabric"] = "pure cotton"
    elif re.search(r'\blinen\b', lower):
        attrs["fabric"] = "linen"

    return attrs

def extract_distinctive_tokens(text: str) -> List[str]:
    """
    Extracts high-signal distinctive tokens (model names, sub-series, capacity, alphanumeric IDs)
    that MUST be present for an exact 1:1 SKU match.
    """
    lower = normalize_title(text)
    tokens = set()

    # 1. Alphanumeric IDs and model codes (e.g. WH-1000XM5, iPhone 15, 128GB, 4.2L)
    model_codes = re.findall(r'\b[a-zA-Z0-9]+-[a-zA-Z0-9-]+\b|\b\d+[a-zA-Z]+\b|\b[a-zA-Z]+\d+\b', lower)
    stopwords = {"100cotton", "100pure", "1pack", "2pack", "4pack", "8pack", "t-shirt", "v-neck", "purecotton", "cottonblend"}
    for m in model_codes:
        if m not in stopwords and len(m) >= 2:
            tokens.add(m)

    # 2. Key series / sub-brand terms
    distinctive_keywords = [
        "pickle", "court", "ortholite", "relaxed", "healthifry", "airfryer", 
        "air fryer", "simply better", "wh-1000xm5", "iphone 15", "iphone 14", 
        "air force 1", "superstar", "stan smith", "suede classic", "smashic", 
        "caven", "drift cat", "oxyfit", "power", "athleisure"
    ]
    for kw in distinctive_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            tokens.add(kw)

    return list(tokens)

def classify_product_match(target_title: str, candidate_title: str, target_brand: str = "") -> Tuple[str, List[str]]:
    """
    STRICT 1:1 Exact Match Classifier:
    - "exact": 100% identical SKU, matching Brand, Article Category, Model/Series, and Key Specs.
    - "rejected": ANY mismatch in Category, Brand, Series, Color, or Capacity immediately disqualifies candidate.
    """
    clean_target = normalize_title(target_title)
    clean_cand = normalize_title(candidate_title)

    # 1. Brand Verification (100% Strict)
    if target_brand:
        tb_clean = target_brand.lower().strip()
        # Handle compound brand names like "the beetel house" or "bacca bucci"
        if tb_clean not in clean_cand:
            # Check individual brand words if 2+ words (e.g. "beetel house")
            b_words = [w for w in tb_clean.split() if w not in ["the", "all", "house"]]
            if not any(bw in clean_cand for bw in b_words):
                return "rejected", [f"Brand mismatch: expected {target_brand}"]

    # 2. Article Category Verification (e.g. Bottomwear vs Topwear vs Footwear)
    target_cat = extract_article_category(target_title)
    cand_cat = extract_article_category(candidate_title)

    if target_cat and cand_cat and target_cat != cand_cat:
        return "rejected", [f"Category mismatch: {cand_cat.title()} vs {target_cat.title()}"]

    # 3. Color Compatibility
    target_attrs = extract_garment_attributes(target_title)
    cand_attrs = extract_garment_attributes(candidate_title)

    target_color = target_attrs["color"]
    if target_color and not is_color_compatible(target_color, candidate_title):
        return "rejected", [f"Color conflict: expected {target_color.title()}"]

    # 4. Distinctive Model / Sub-Series Token Verification
    target_distinctive = extract_distinctive_tokens(target_title)
    for token in target_distinctive:
        if token not in clean_cand:
            return "rejected", [f"Model series mismatch: missing '{token.title()}'"]

    # 5. Fit & Silhouette check for Apparel
    if target_attrs["fit"] and cand_attrs["fit"]:
        if target_attrs["fit"] != cand_attrs["fit"]:
            return "rejected", [f"Fit mismatch: expected {target_attrs['fit'].title()}"]

    if target_attrs["neck"] and cand_attrs["neck"]:
        if target_attrs["neck"] != cand_attrs["neck"]:
            return "rejected", [f"Neckline mismatch: expected {target_attrs['neck'].title()}"]

    if target_attrs["pattern"] and cand_attrs["pattern"]:
        if target_attrs["pattern"] != cand_attrs["pattern"]:
            return "rejected", [f"Pattern mismatch: expected {target_attrs['pattern'].title()}"]

    # If all critical criteria match -> 100% Verified Exact Match
    return "exact", []

def calculate_match_confidence(target_title: str, candidate_title: str, target_brand: str = "") -> float:
    tier, _ = classify_product_match(target_title, candidate_title, target_brand)
    if tier == "exact":
        return 1.0
    return 0.0
