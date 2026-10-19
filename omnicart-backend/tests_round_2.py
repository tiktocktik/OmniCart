import unittest
import urllib.parse
from app.url_parser import clean_and_normalize_url
from app.intelligence import compute_price_prediction, calculate_payment_arbitrage
from app.resolver import resolve_product_pipeline

class TestOmniCartBackendRound2(unittest.TestCase):
    
    # Test Edge Case 1: Complex URL with nested tracking & anchor fragments
    def test_amazon_complex_anchor_and_mobile_share(self):
        url = "https://www.amazon.in/dp/B09XS7JWHH/ref=as_li_ss_tl?ie=UTF8&linkCode=ll1&tag=dealbeedeals-21#customerReviews"
        cleaned, platform, asin = clean_and_normalize_url(url)
        self.assertEqual(platform, "Amazon.in")
        self.assertEqual(asin, "B09XS7JWHH")
        self.assertEqual(cleaned, "https://www.amazon.in/dp/B09XS7JWHH")
        self.assertNotIn("#customerReviews", cleaned)

    # Test Edge Case 2: Flipkart mobile app share link with weird pathing
    def test_flipkart_mobile_share_format(self):
        url = "https://www.flipkart.com/pigeon-by-stovekraft-healthifry-digital-air-fryer/p/itm6c0f8373b40e7?pid=CPTGGY8E79796Y8Z&lid=LSTCPTGGY8E79796Y8Z020&marketplace=FLIPKART"
        cleaned, platform, pid = clean_and_normalize_url(url)
        self.assertEqual(platform, "Flipkart")
        self.assertEqual(pid, "CPTGGY8E79796Y8Z")
        self.assertIn("pid=CPTGGY8E79796Y8Z", cleaned)

    # Test Edge Case 3: Blinkit & Zepto quick commerce deep links
    def test_quick_commerce_dark_store_links(self):
        zepto_url = "https://www.zeptonow.com/pn/pigeon-digital-air-fryer-42l/pvid/9821a7c"
        cleaned, platform, slug = clean_and_normalize_url(zepto_url)
        self.assertEqual(platform, "Zepto")
        
        blinkit_url = "https://blinkit.com/prn/tata-simply-better-extra-virgin-olive-oil-2l/prid/34129"
        cleaned_b, platform_b, slug_b = clean_and_normalize_url(blinkit_url)
        self.assertEqual(platform_b, "Blinkit")

    # Test Edge Case 4: Zero or negative prices / Division by zero safety
    def test_prediction_edge_cases_safety(self):
        # 100% discount / freebie edge case
        pred_free = compute_price_prediction(live_price=0.0, all_time_low=0.0, regular_price=1000.0)
        self.assertEqual(pred_free.badge, "BUY NOW")
        
        # Zero regular price edge case (prevent ZeroDivisionError)
        pred_zero = compute_price_prediction(live_price=500.0, all_time_low=500.0, regular_price=0.0)
        self.assertIsNotNone(pred_zero)

    # Test Edge Case 5: Different Pincode Resolution (Mumbai 400001 vs Bengaluru 560001)
    def test_pincode_dependent_resolution(self):
        res_delhi = resolve_product_pipeline("pigeon air fryer", pincode="110001")
        self.assertIn("Hub #110", res_delhi.sellers[0].name)
        
        res_mumbai = resolve_product_pipeline("pigeon air fryer", pincode="400001")
        self.assertIn("Hub #400", res_mumbai.sellers[0].name)

    # Test Edge Case 6: Payment Arbitrage Calculation on High vs Low Value SKUs
    def test_payment_arbitrage_high_value_laptop(self):
        # High value product (e.g. ₹50,000)
        options = calculate_payment_arbitrage(50000.0, "Amazon.in")
        amz_opt = next(o for o in options if o.title == "Amazon Pay ICICI Credit Card")
        self.assertEqual(amz_opt.effective_savings, 2500.0)
        self.assertEqual(amz_opt.final_price, 47500.0)

    # Test Edge Case 7: Search with messy typo spacing and case variations
    def test_messy_search_queries(self):
        res1 = resolve_product_pipeline("   TATA   COLD   PRESSED   OLIVE   OIL  ")
        self.assertEqual(res1.platform, "Tata Simply Better")
        self.assertEqual(res1.live_price, 1249.0)

        res2 = resolve_product_pipeline("   pIgEon   AiR   FrYeR   ")
        self.assertEqual(res2.platform, "Zepto")
        self.assertEqual(res2.live_price, 999.0)

if __name__ == "__main__":
    unittest.main()
