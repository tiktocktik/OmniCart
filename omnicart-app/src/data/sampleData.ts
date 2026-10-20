export interface PricePoint {
  date: string;
  price: number;
  label?: string;
  isGlitch?: boolean;
}

export interface Seller {
  id: string;
  name: string;
  price: number;
  rating: number;
  reviewsCount: number;
  deliveryDays: string;
  badge: "Brand Direct" | "Amazon Prime" | "Flipkart Assured" | "DarkStore Verified";
  isBestSeller: boolean;
  score: number;
  storeUrl: string;
}

export interface Coupon {
  code: string;
  source: string;
  discountText: string;
  discountAmount: number;
  successRate: number;
}

export interface PaymentMethod {
  title: string;
  type: "Card" | "Voucher" | "UPI" | "Wallet";
  effectiveSavings: number;
  finalPrice: number;
  explanation: string;
  isRecommended?: boolean;
}

export interface CompetitorPrice {
  platform: string;
  title: string;
  price: number;
  deliveryInfo: string;
  deliveryFee: number;
  combinedDiscountText: string;
  effectiveFinalPrice: number;
  storeUrl: string;
  isCheaper: boolean;
  badge?: string;
  matchTier?: "exact" | "similar_style";
  mismatchAttributes?: string[];
}

export interface PurchaseOption {
  type: string;
  name: string;
  value: string;
  price?: number;
  isAvailable: boolean;
  isSelected: boolean;
  url?: string;
  imageUrl?: string;
  stockInfo?: string;
}

export interface ProductDetail {
  id: string;
  title: string;
  category: string;
  store: string;
  storeUrl: string;
  rating: number;
  ratingsCount: number;
  livePrice: number;
  regularPrice: number;
  allTimeLow: number;
  allTimeHigh: number;
  productImages: string[];
  prediction: {
    badge: "BUY NOW" | "WAIT" | "FAIR PRICE";
    detail: string;
    dropLikelihood: string;
  };
  history: {
    "1M": PricePoint[];
    "6M": PricePoint[];
    "1Y": PricePoint[];
    "3Y": PricePoint[];
    ALL: PricePoint[];
  };
  historySource?: "VERIFIED_AGGREGATOR" | "ESTIMATED_TRAJECTORY";
  historyDataPoints?: number;
  sellers: Seller[];
  competitors?: CompetitorPrice[];
  similarStyles?: CompetitorPrice[];
  purchaseOptions?: PurchaseOption[];
  specifications?: Record<string, string>;
  highlights?: string[];
  pincode?: string;
  pincodeDeliveryStatus?: string;
  deliveryCharge?: number;
  coupons: Coupon[];
  paymentOptions: PaymentMethod[];
  smartStack?: SmartStackCombo;
}

export interface SmartStackCombo {
  storeCouponCode: string;
  storeCouponSource: string;
  storeCouponSavings: number;
  cardTitle: string;
  cardType: string;
  cardSavings: number;
  combinedTotalSavings: number;
  finalStackedPrice: number;
  discountPercentage: number;
  executionSteps: string[];
}

export const PRODUCTS_DB: Record<string, ProductDetail> = {};

export const TRENDING_LOOTS: any[] = [];
