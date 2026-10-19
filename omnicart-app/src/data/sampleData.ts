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

export const PRODUCTS_DB: Record<string, ProductDetail> = {
  "tata-olive-oil": {
    id: "tata-olive-oil",
    title: "Tata Simply Better 100% Pure Cold Pressed Extra Virgin Olive Oil (2 Litre Pet Jar)",
    category: "Grocery & Gourmet Cooking Oils",
    store: "Tata Simply Better",
    storeUrl: "https://www.tatasimplybetter.com",
    rating: 4.7,
    ratingsCount: 1420,
    livePrice: 1249,
    regularPrice: 2899,
    allTimeLow: 1199,
    allTimeHigh: 2899,
    productImages: [
      "https://m.media-amazon.com/images/I/61YgI8jF7-L._SL1500_.jpg",
      "https://m.media-amazon.com/images/I/71R2oI0fAAL._SL1500_.jpg",
      "https://m.media-amazon.com/images/I/71L5T4eT8kL._SL1500_.jpg",
    ],
    prediction: {
      badge: "BUY NOW",
      detail: "Historic 57% markdown. Stacked manufacturer code overlapping with brand anniversary sale.",
      dropLikelihood: "Lowest in 3 years • Expected to expire within 4 hours",
    },
    history: {
      "1M": [
        { date: "Oct 01", price: 2199 },
        { date: "Oct 05", price: 2199 },
        { date: "Oct 10", price: 1999 },
        { date: "Oct 14", price: 1899 },
        { date: "Oct 17", price: 1499 },
        { date: "Live Now", price: 1249, label: "Flash Loot (₹1,249)", isGlitch: true },
      ],
      "6M": [
        { date: "May 2026", price: 2799 },
        { date: "Jun 2026", price: 2899 },
        { date: "Jul 2026", price: 2499 },
        { date: "Aug 2026", price: 2699 },
        { date: "Sep 2026", price: 2299 },
        { date: "Oct 2026", price: 1249, label: "Historic Drop", isGlitch: true },
      ],
      "1Y": [
        { date: "Nov 2025", price: 2699 },
        { date: "Jan 2026", price: 2899 },
        { date: "Mar 2026", price: 2799 },
        { date: "May 2026", price: 2799 },
        { date: "Jul 2026", price: 2499 },
        { date: "Oct 2026", price: 1249, isGlitch: true },
      ],
      "3Y": [
        { date: "2023 Launch", price: 2499 },
        { date: "Diwali 2023", price: 1999 },
        { date: "Mid 2024", price: 2799 },
        { date: "Diwali 2024", price: 1899 },
        { date: "Mid 2025", price: 2899 },
        { date: "Diwali 2025", price: 1999 },
        { date: "Live 2026", price: 1249, label: "All-Time Lowest Recorded", isGlitch: true },
      ],
      ALL: [
        { date: "2023", price: 2499 },
        { date: "2024", price: 2799 },
        { date: "2025", price: 2899 },
        { date: "Current", price: 1249, isGlitch: true },
      ],
    },
    sellers: [
      {
        id: "s1",
        name: "Tata Consumer Direct (Official Flagship)",
        price: 1249,
        rating: 4.8,
        reviewsCount: 14200,
        deliveryDays: "Tomorrow, 11 AM",
        badge: "Brand Direct",
        isBestSeller: true,
        score: 99,
        storeUrl: "https://www.tatasimplybetter.com",
      },
      {
        id: "s2",
        name: "Cloudtail Grocery (Amazon India)",
        price: 1899,
        rating: 4.4,
        reviewsCount: 3100,
        deliveryDays: "2 Business Days",
        badge: "Amazon Prime",
        isBestSeller: false,
        score: 78,
        storeUrl: "https://amazon.in",
      },
      {
        id: "s3",
        name: "Supermart Express (Flipkart)",
        price: 2149,
        rating: 4.1,
        reviewsCount: 940,
        deliveryDays: "3-4 Days",
        badge: "Flipkart Assured",
        isBestSeller: false,
        score: 69,
        storeUrl: "https://flipkart.com",
      },
    ],
    coupons: [
      {
        code: "SIMPLYBETTER50",
        source: "Brand Direct Promotion",
        discountText: "Flat ₹500 off on cold pressed range above ₹1,500",
        discountAmount: 500,
        successRate: 98,
      },
      {
        code: "TATAPAY10",
        source: "Tata Neu App",
        discountText: "10% Instant discount on first grocery order",
        discountAmount: 125,
        successRate: 92,
      },
    ],
    paymentOptions: [
      {
        title: "GyFTR HDFC SmartBuy Voucher + SIMPLYBETTER50",
        type: "Voucher",
        effectiveSavings: 581,
        finalPrice: 1168,
        explanation: "Stack ₹500 coupon code with 6.5% voucher points via HDFC Infinia / DCB.",
        isRecommended: true,
      },
      {
        title: "Tata Neu Infinity HDFC Credit Card",
        type: "Card",
        effectiveSavings: 125,
        finalPrice: 1124,
        explanation: "10% NeuCoins cashback on all Tata brand orders.",
      },
      {
        title: "SBI Cashback Credit Card",
        type: "Card",
        effectiveSavings: 62,
        finalPrice: 1187,
        explanation: "Flat 5% direct cashback credited to next month statement.",
      },
    ],
  },

  "pigeon-air-fryer": {
    id: "pigeon-air-fryer",
    title: "Pigeon Healthifry Digital 4.2L Air Fryer (360° High Speed Rapid Air Convection)",
    category: "Kitchen & Home Appliances",
    store: "Zepto",
    storeUrl: "https://www.zepto.com",
    rating: 4.5,
    ratingsCount: 4200,
    livePrice: 999,
    regularPrice: 3495,
    allTimeLow: 999,
    allTimeHigh: 3495,
    productImages: [
      "https://m.media-amazon.com/images/I/616A9-D97qL._SL1500_.jpg",
      "https://m.media-amazon.com/images/I/71K2X-2-xJL._SL1500_.jpg",
      "https://m.media-amazon.com/images/I/71zT51Y4eKL._SL1500_.jpg",
    ],
    prediction: {
      badge: "BUY NOW",
      detail: "Ultra-rare 3-digit price glitch. Dark-store batch stock clearance across metro hubs.",
      dropLikelihood: "Lowest in 4 years • Selling out in under 15 minutes",
    },
    history: {
      "1M": [
        { date: "Oct 01", price: 2499 },
        { date: "Oct 06", price: 2199 },
        { date: "Oct 11", price: 1899 },
        { date: "Oct 15", price: 1799 },
        { date: "Live Now", price: 999, label: "3-DIGIT DROP (₹999)", isGlitch: true },
      ],
      "6M": [
        { date: "May 2026", price: 2999 },
        { date: "Jun 2026", price: 2899 },
        { date: "Jul 2026", price: 2799 },
        { date: "Aug 2026", price: 2499 },
        { date: "Sep 2026", price: 2199 },
        { date: "Oct 2026", price: 999, isGlitch: true },
      ],
      "1Y": [
        { date: "Nov 2025", price: 3199 },
        { date: "Jan 2026", price: 2999 },
        { date: "Mar 2026", price: 2899 },
        { date: "Jun 2026", price: 2799 },
        { date: "Sep 2026", price: 2199 },
        { date: "Oct 2026", price: 999, isGlitch: true },
      ],
      "3Y": [
        { date: "2023", price: 3495 },
        { date: "2024 Big Billion", price: 2299 },
        { date: "2025 Great Indian", price: 1999 },
        { date: "2026 Current", price: 999, label: "Historic Low", isGlitch: true },
      ],
      ALL: [
        { date: "Launch 2022", price: 3999 },
        { date: "2023", price: 3495 },
        { date: "2024", price: 2299 },
        { date: "2025", price: 1999 },
        { date: "Current", price: 999, isGlitch: true },
      ],
    },
    sellers: [
      {
        id: "z1",
        name: "Zepto DarkStore Hub #12 (1.2 km away)",
        price: 999,
        rating: 4.9,
        reviewsCount: 16400,
        deliveryDays: "10-15 Minutes Delivery",
        badge: "DarkStore Verified",
        isBestSeller: true,
        score: 100,
        storeUrl: "https://www.zepto.com",
      },
      {
        id: "amz1",
        name: "RetailNet (Flipkart)",
        price: 1899,
        rating: 4.3,
        reviewsCount: 8400,
        deliveryDays: "Tomorrow",
        badge: "Flipkart Assured",
        isBestSeller: false,
        score: 77,
        storeUrl: "https://flipkart.com",
      },
      {
        id: "amz2",
        name: "Appario Retail (Amazon India)",
        price: 1999,
        rating: 4.4,
        reviewsCount: 12100,
        deliveryDays: "Tomorrow",
        badge: "Amazon Prime",
        isBestSeller: false,
        score: 75,
        storeUrl: "https://amazon.in",
      },
    ],
    coupons: [
      {
        code: "ZEPTOCLEAR100",
        source: "App Notification",
        discountText: "Flat ₹100 instant discount on electronics clearance",
        discountAmount: 100,
        successRate: 100,
      },
    ],
    paymentOptions: [
      {
        title: "Amazon Pay Balance / UPI Auto-Pay",
        type: "Wallet",
        effectiveSavings: 100,
        finalPrice: 899,
        explanation: "Sub-second 0.5s auto-checkout with zero OTP friction before stock expires.",
        isRecommended: true,
      },
      {
        title: "SBI Cashback Credit Card",
        type: "Card",
        effectiveSavings: 50,
        finalPrice: 949,
        explanation: "5% online shopping cashback credited directly.",
      },
    ],
  },
};

export const TRENDING_LOOTS = [
  {
    id: "tata-olive-oil",
    title: "Tata Simply Better Cold Pressed Olive Oil (2L)",
    store: "Tata Simply Better",
    dealPrice: 1249,
    regularPrice: 2899,
    discount: 57,
    timeAgo: "4m ago",
    image: "https://m.media-amazon.com/images/I/61YgI8jF7-L._SL1500_.jpg",
    badge: "57% OFF",
  },
  {
    id: "pigeon-air-fryer",
    title: "Pigeon Healthifry Digital 4.2L Air Fryer",
    store: "Zepto DarkStore",
    dealPrice: 999,
    regularPrice: 3495,
    discount: 71,
    timeAgo: "11m ago",
    image: "https://m.media-amazon.com/images/I/616A9-D97qL._SL1500_.jpg",
    badge: "3-DIGIT DROP",
  },
];
