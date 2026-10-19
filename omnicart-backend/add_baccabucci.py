import re

# 1. Update app/url_parser.py
with open("app/url_parser.py", "r", encoding="utf-8") as f:
    url_code = f.read()

baccabucci_url_rule = '''    if "baccabucci.com" in domain:
        slug = parsed.path.strip("/").split("/")[-1]
        clean_path = path.split("?")[0]
        canonical = f"https://baccabucci.com{clean_path}"
        return canonical, "Bacca Bucci", slug

    if "redtape.com" in domain:'''

if "baccabucci.com" not in url_code:
    url_code = url_code.replace('    if "redtape.com" in domain:', baccabucci_url_rule)
    with open("app/url_parser.py", "w", encoding="utf-8") as f:
        f.write(url_code)
    print("Added Bacca Bucci to app/url_parser.py")
else:
    print("Bacca Bucci already in app/url_parser.py")

# 2. Update app/universal_scraper.py
with open("app/universal_scraper.py", "r", encoding="utf-8") as f:
    scraper_code = f.read()

# Add Bacca Bucci seller mapping
baccabucci_seller = '''        elif "baccabucci" in parsed_domain:
            seller_name = "Bacca Bucci Official Flagship"
            platform_name = "Bacca Bucci"
        elif "redtape" in parsed_domain:'''

if "baccabucci" not in scraper_code:
    scraper_code = scraper_code.replace('        elif "redtape" in parsed_domain:', baccabucci_seller)

# Also check for Bacca Bucci title priority (og:title preference)
og_check_target = '''        if not title:
            og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
            if og_title and og_title.get("content"):
                title = clean_extracted_title(og_title["content"].strip())'''

og_check_replacement = '''        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
        if og_title and og_title.get("content"):
            og_text = clean_extracted_title(og_title["content"].strip())
            # Prefer og:title if current title is short, generic, or if og:title contains brand
            if not title or len(title.split()) <= 2 or any(k in og_text.lower() for k in ["bacca bucci", "sneaker", "shoes", "trousers"]):
                title = og_text'''

if og_check_target in scraper_code:
    scraper_code = scraper_code.replace(og_check_target, og_check_replacement)

# Also parse Shopify var meta variants for footwear sizes
shopify_var_meta = '''        # 1.5 Shopify var meta variants extraction
        if not purchase_options:
            meta_m = re.search(r'var\s+meta\s*=\s*(\{.+?\});', raw_html)
            if meta_m:
                try:
                    meta_json = json.loads(meta_m.group(1))
                    meta_prod = meta_json.get("product", {})
                    for v in meta_prod.get("variants", []):
                        v_name = v.get("name", "")
                        v_price = (v.get("price") / 100.0) if v.get("price") else live_price
                        v_sku = str(v.get("id", ""))
                        # Clean size label (e.g. "Pickle Series - RED / UK-06" -> "UK-06")
                        clean_label = v_name.split("/")[-1].strip() if "/" in v_name else v_name
                        purchase_options.append({
                            "type": "size",
                            "name": "Size",
                            "value": clean_label,
                            "price": v_price,
                            "is_available": True,
                            "is_selected": len(purchase_options) == 0,
                            "url": f"{url.split('?')[0]}?variant={v_sku}",
                            "stock_info": "In Stock"
                        })
                except Exception:
                    pass
'''

if "1.5 Shopify var meta variants extraction" not in scraper_code:
    scraper_code = scraper_code.replace('        # 2. OpenGraph Meta Tags Fallback', shopify_var_meta + '\n        # 2. OpenGraph Meta Tags Fallback')

with open("app/universal_scraper.py", "w", encoding="utf-8") as f:
    f.write(scraper_code)
print("Updated app/universal_scraper.py with Bacca Bucci and Shopify variants support")
