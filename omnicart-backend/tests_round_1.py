import unittest
import urllib.parse
from app.url_parser import clean_and_normalize_url
from app.intelligence import compute_price_prediction, calculate_payment_arbitrage
from app.resolver import resolve_product_pipeline

class TestOmniCartBackend(unittest.TestCase):
    
    # 1. URL Normalization & Parameter Stripping Tests
    def test_amazon_url_cleaning(self):
        url = "https://www.amazon.in/dp/B09XS7JWHH?tag=affiliate123-21&ref=sr_1_1&keywords=sony+xm5"
        cleaned, platform, asin = clean_and_normalize_url(url)
        self.assertEqual(platform, "Amazon.in")
        self.assertEqual(asin, "B09XS7JWHH")
        self.assertEqual(cleaned, "https://www.amazon.in/dp/B09XS7JWHH")
        self.assertNotIn("tag=", cleaned)
        self.assertNotIn("ref=", cleaned)

    def test_flipkart_url_cleaning(self):
        url = "https://www.flipkart.com/pigeon-air-fryer/p/itm12345abcdef?pid=FRY123456789&affid=fakeaffil"
        cleaned, platform, pid = clean_and_normalize_url(url)
        self.assertEqual(platform, "Flipkart")
        self.assertEqual(pid, "FRY123456789")
        self.assertNotIn("affid=", cleaned)

    def test_generic_url_tracking_removal(self):
        url = "https://www.boat-lifestyle.com/products/airdopes-141?utm_source=facebook&utm_medium=cpc&utm_campaign=diwali"
        cleaned, platform, _ = clean_and_normalize_url(url)
        self.assertEqual(platform, "Universal")
        self.assertNotIn("utm_source", cleaned)
        self.assertNotIn("utm_campaign", cleaned)

    def test_plain_search_query(self):
        query = "pigeon digital air fryer 4.2l"
        cleaned, platform, _ = clean_and_normalize_url(query)
        self.assertEqual(platform, "SEARCH_QUERY")
        self.assertEqual(cleaned, query)

    # 2. Price Prediction & Glitch Detection Logic
    def test_price_prediction_extreme_glitch(self):
        # 3495 down to 999 is > 70% drop
        pred = compute_price_prediction(live_price=999.0, all_time_low=999.0, regular_price=3495.0)
        self.assertEqual(pred.badge, "BUY NOW")
        self.assertGreaterEqual(pred.confidence, 95)

    def test_price_prediction_near_mrp(self):
        pred = compute_price_prediction(live_price=3400.0, all_time_low=1999.0, regular_price=3495.0)
        self.assertEqual(pred.badge, "WAIT")

    # 3. Payment Stacking Arbitrage
    def test_payment_arbitrage_tata(self):
        options = calculate_payment_arbitrage(1249.0, "Tata Simply Better")
        # Should have voucher arbitrage as top recommended option
        voucher_opt = next((o for o in options if o.type == "Voucher"), None)
        self.assertIsNotNone(voucher_opt)
        self.assertTrue(voucher_opt.is_recommended)
        self.assertGreater(voucher_opt.effective_savings, 0)

    # 4. End-to-End Resolver Pipeline Tests
    def test_resolve_tata_olive_oil(self):
        res = resolve_product_pipeline("https://www.tatasimplybetter.com/products/cold-pressed-olive-oil-2l?ref=share")
        self.assertEqual(res.platform, "Tata Simply Better")
        self.assertEqual(res.live_price, 1249.0)
        self.assertIn("1M", res.history)
        self.assertIn("3Y", res.history)
        self.assertIn("ALL", res.history)
        self.assertTrue(len(res.sellers) > 0)
        self.assertTrue(len(res.coupons) > 0)

    def test_resolve_pigeon_air_fryer(self):
        res = resolve_product_pipeline("pigeon air fryer 4.2L", pincode="110001")
        self.assertEqual(res.platform, "Zepto")
        self.assertEqual(res.live_price, 999.0)
        self.assertTrue(res.is_loot_deal)
        self.assertGreaterEqual(res.loot_drop_percentage, 65.0)

    def test_resolve_sony_headphones(self):
        res = resolve_product_pipeline("https://www.amazon.in/dp/B09XS7JWHH?tag=affil-21")
        self.assertEqual(res.platform, "Amazon.in")
        self.assertEqual(res.live_price, 21990.0)
        self.assertFalse(res.is_loot_deal)

if __name__ == "__main__":
    unittest.main()
