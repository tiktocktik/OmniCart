from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PricePoint(BaseModel):
    date: str
    price: float
    label: Optional[str] = None
    is_glitch: Optional[bool] = False

class CompetitorPrice(BaseModel):
    platform: str # "Amazon.in" | "Myntra" | "AJIO" | "Flipkart" | "Tata CliQ" | "Official Store"
    title: str
    price: float
    delivery_info: str
    delivery_fee: float = 0.0
    combined_discount_text: str
    effective_final_price: float
    store_url: str
    is_cheaper: bool = False
    badge: Optional[str] = None
    match_tier: str = "exact" # "exact" (100% 1:1 identical) | "similar_style" (different neck/pattern)
    mismatch_attributes: List[str] = [] # e.g. ["Polo Collar instead of Crew", "Striped Pattern"]

class SellerInfo(BaseModel):
    id: str
    name: str
    price: float
    rating: float
    reviews_count: int
    delivery_days: str
    delivery_charge: float = 0.0
    badge: str
    is_best_seller: bool
    score: int
    store_url: str

class PurchaseOption(BaseModel):
    type: str # "size" | "color" | "pack" | "variant"
    name: str # e.g. "Size", "Color"
    value: str # e.g. "30", "XL", "Navy Blue", "Pack of 2"
    price: Optional[float] = None
    is_available: bool = True
    is_selected: bool = False
    url: Optional[str] = None
    image_url: Optional[str] = None
    stock_info: Optional[str] = None

class CouponInfo(BaseModel):
    code: str
    source: str
    discount_text: str
    discount_amount: float
    success_rate: Optional[float] = None

class PaymentOption(BaseModel):
    title: str
    type: str # "Voucher" | "Card" | "UPI" | "Wallet"
    effective_savings: float
    final_price: float
    explanation: str
    is_recommended: bool = False

class SmartStackCombo(BaseModel):
    store_coupon_code: str = ""
    store_coupon_source: str = ""
    store_coupon_savings: float = 0.0
    card_title: str = ""
    card_type: str = ""
    card_savings: float = 0.0
    combined_total_savings: float = 0.0
    final_stacked_price: float = 0.0
    discount_percentage: float = 0.0
    execution_steps: List[str] = Field(default_factory=list)

class PricePrediction(BaseModel):
    badge: str = "BUY NOW" # "BUY NOW" | "WAIT" | "FAIR PRICE" | "VERIFY ON STORE"
    detail: str = ""
    drop_likelihood: str = "LOW"
    confidence: int = 80

class ProductResolution(BaseModel):
    id: str
    canonical_url: str
    platform: str
    title: str
    category: str
    image_url: str
    gallery_images: List[str] = []
    rating: float
    ratings_count: int
    live_price: float
    regular_price: float
    pincode: str = "110001"
    pincode_delivery_status: str = "In Stock for Delivery"
    delivery_charge: float = 0.0
    all_time_low: float
    all_time_high: float
    prediction: PricePrediction
    history: Dict[str, List[PricePoint]]
    sellers: List[SellerInfo]
    competitors: List[CompetitorPrice] = []
    similar_styles: List[CompetitorPrice] = []
    purchase_options: List[PurchaseOption] = []
    specifications: Dict[str, str] = Field(default_factory=dict)
    highlights: List[str] = Field(default_factory=list)
    coupons: List[CouponInfo]
    payment_options: List[PaymentOption]
    smart_stack: Optional[SmartStackCombo] = None
    is_loot_deal: bool = False
    loot_drop_percentage: float = 0.0
    history_source: str = "UNAVAILABLE"
    history_data_points: int = 0
    status: str = "ok"  # "ok" | "partial" | "unavailable"
    status_message: Optional[str] = None

class ResolveRequest(BaseModel):
    query_or_url: str
    pincode: str = "110001"
