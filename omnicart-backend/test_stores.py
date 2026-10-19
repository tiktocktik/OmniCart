from app.resolver import resolve_product_pipeline

test_urls = [
    ("Tata CliQ", "https://www.tatacliq.com/apple-iphone-15-128-gb-black/p-mp000000019688147"),
    ("Westside", "https://www.westside.com/products/lov-light-beige-ribbed-textured-polo-top-301072962"),
    ("Croma", "https://www.croma.com/apple-iphone-15-128gb-black-/p/300652"),
    ("Reliance Digital", "https://www.reliancedigital.in/apple-iphone-15-128-gb-black/p/493839294"),
    ("Vijay Sales", "https://www.vijaysales.com/apple-iphone-15-128-gb-black/23490"),
    ("Uniqlo", "https://www.uniqlo.com/in/en/products/E465185-000"),
    ("Snitch", "https://www.snitch.co.in/products/classic-linen-shirt-white"),
    ("Style Union", "https://styleunion.in/products/men-solid-linen-shirt-beige"),
    ("The Souled Store", "https://www.thesouledstore.com/product/solids-dusty-peach-oversized-t-shirts"),
    ("Pantaloons", "https://www.pantaloons.com/p/men-navy-solid-casual-shirt-837482.html"),
    ("Nykaa Fashion", "https://www.nykaafashion.com/puma-black-solid-running-shoes/p/1238472"),
    ("AJIO", "https://www.ajio.com/puma-men-sneakers/p/460839201_black"),
    ("Ani Clothing", "https://aniclothing.in/products/linen-co-ord-set-beige"),
    ("Fabindia", "https://www.fabindia.com/cotton-silk-printed-long-kurta-10729381"),
    ("Lifestyle", "https://www.lifestylestores.com/in/en/SHOP-Fame-Forever-by-Lifestyle-Navy-Men-Solid-Slim-Fit-Casual-Shirt/p/1000012384"),
    ("Meesho", "https://www.meesho.com/men-stylish-sneakers/p/6k8m2a"),
    ("Red Tape", "https://redtape.com/products/athleisure-shoes-for-men-black-rso3490"),
    ("Bata", "https://www.bata.com/in/power-men-black-running-shoes-8349281.html"),
    ("Woodland", "https://www.woodlandworldwide.com/productinfo/FLC01804928A-BLACK"),
    ("Campus Shoes", "https://www.campusshoes.com/products/oxyfit-black-mens-running-shoes"),
    ("Metro Shoes", "https://metroshoes.com/men-formal-black-leather-shoes-19-2849"),
    ("Puma", "https://in.puma.com/in/en/pd/smashic-unisex-sneakers/392948"),
    ("Nike", "https://www.nike.com/in/t/air-force-1-07-shoes-WrLlWX/CW2288-111"),
]

print("-" * 115)
print(f"{'Store Name':<18} | {'Resolved Platform':<18} | {'Price':<10} | {'Badge':<20} | {'Extracted Title'}")
print("-" * 115)

for store, url in test_urls:
    try:
        p = resolve_product_pipeline(url, "110001")
        price_str = f"Rs {int(p.live_price)}" if p.live_price > 0 else "Verify"
        print(f"{store:<18} | {p.platform:<18} | {price_str:<10} | {p.prediction.badge:<20} | {p.title[:35]}")
    except Exception as e:
        print(f"{store:<18} | FAILED: {e}")
print("-" * 115)
