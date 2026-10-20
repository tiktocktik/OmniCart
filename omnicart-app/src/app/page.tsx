"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  MapPin,
  TrendingDown,
  ShieldCheck,
  Zap,
  Tag,
  CreditCard,
  Bell,
  ExternalLink,
  ShoppingBag,
  Sparkles,
  ChevronRight,
  Copy,
  Flame,
  ArrowRight,
  Heart,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  Check,
  Loader2,
  AlertCircle,
  Crosshair,
  ShoppingCart,
  Trash2,
  X,
  History,
  Truck,
  Layers,
  ArrowDownRight,
  Sun,
  Moon,
  Navigation,
  Camera,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import {
  PRODUCTS_DB,
  TRENDING_LOOTS,
  ProductDetail,
  CompetitorPrice,
  PurchaseOption,
} from "@/data/sampleData";
import { API_BASE } from "@/lib/api";

type TimeRange = "1M" | "6M" | "1Y" | "3Y" | "ALL";

interface CartItem {
  id: string;
  title: string;
  store: string;
  storeUrl: string;
  image: string;
  price: number;
  regularPrice: number;
  deliveryDays: string;
  quantity: number;
}

export default function Home() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [activeProductId, setActiveProductId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [userPincode, setUserPincode] = useState<string>("110001");
  const [pincodeCity, setPincodeCity] = useState<string>("Delhi");
  const [isDetectingLocation, setIsDetectingLocation] =
    useState<boolean>(false);
  const [showLocationModal, setShowLocationModal] = useState<boolean>(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  const [timeRange, setTimeRange] = useState<TimeRange>("1Y");
  const [activeTab, setActiveTab] = useState<
    "comparison" | "history" | "sellers" | "payment" | "specs"
  >("comparison");
  const [isWishlisted, setIsWishlisted] = useState<boolean>(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [isOrdering, setIsOrdering] = useState<boolean>(false);
  const [orderModalOpen, setOrderModalOpen] = useState<boolean>(false);
  const [selectedPoint, setSelectedPoint] = useState<{
    date: string;
    price: number;
  } | null>(null);
  const [isLoadingApi, setIsLoadingApi] = useState<boolean>(false);
  const [liveResolvedProduct, setLiveResolvedProduct] =
    useState<ProductDetail | null>(null);
  const [apiError, setApiError] = useState<{
    message: string;
    storeUrl?: string;
  } | null>(null);

  const [cartOpen, setCartOpen] = useState<boolean>(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [trendingDeals, setTrendingDeals] = useState<any[]>(TRENDING_LOOTS);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  // Fetch live community deals on mount
  useEffect(() => {
    fetch(`${API_BASE}/deals?limit=8`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setTrendingDeals(data);
        }
      })
      .catch(() => {});
  }, []);

  // Load saved theme & location from localStorage on client mount
  useEffect(() => {
    // 1. Theme persistence
    const savedTheme = localStorage.getItem("omnicart_theme") as
      "light" | "dark" | null;
    if (savedTheme) {
      setTheme(savedTheme);
      if (savedTheme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
      document.documentElement.classList.add("dark");
    }

    // 2. Location Check: ALWAYS verify if user explicitly set their location
    const locationChosen = localStorage.getItem("omnicart_location_chosen");
    const savedPin = localStorage.getItem("omnicart_pincode");
    const savedCity = localStorage.getItem("omnicart_city");

    if (locationChosen && savedPin) {
      setUserPincode(savedPin);
      if (savedCity) setPincodeCity(savedCity);
    } else {
      // First visit or not chosen yet: Open the Location Selection Modal
      setShowLocationModal(true);
      // Simultaneously trigger browser geolocation prompt
      requestBrowserLocation();
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("omnicart_theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  // Browser HTML5 Geolocation with reverse geocoding
  const requestBrowserLocation = () => {
    setIsDetectingLocation(true);
    if (typeof window !== "undefined" && "geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const { latitude, longitude } = position.coords;
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`,
            );
            if (res.ok) {
              const geoData = await res.json();
              const pin = geoData.address?.postcode;
              const city =
                geoData.address?.city ||
                geoData.address?.state_district ||
                geoData.address?.suburb ||
                "Local City";

              if (pin) {
                const cleanPin = pin.replace(/\s/g, "").slice(0, 6);
                setUserPincode(cleanPin);
                setPincodeCity(city);
                localStorage.setItem("omnicart_pincode", cleanPin);
                localStorage.setItem("omnicart_city", city);
                localStorage.setItem("omnicart_location_chosen", "true");
                setIsDetectingLocation(false);
                setShowLocationModal(false);
                return;
              }
            }
          } catch {
            // fallback to IP lookup
          }
          fallbackIpLocation();
        },
        () => {
          fallbackIpLocation();
        },
        { timeout: 7000 },
      );
    } else {
      fallbackIpLocation();
    }
  };

  const fallbackIpLocation = async () => {
    try {
      const res = await fetch("https://ipapi.co/json/");
      if (res.ok) {
        const data = await res.json();
        if (data.postal && data.country === "IN") {
          setUserPincode(data.postal);
          const city = data.city || "Local City";
          setPincodeCity(city);
          localStorage.setItem("omnicart_pincode", data.postal);
          localStorage.setItem("omnicart_city", city);
          localStorage.setItem("omnicart_location_chosen", "true");
          setShowLocationModal(false);
        } else if (data.city) {
          setPincodeCity(data.city);
        }
      }
    } catch {
      // Fallback stays default Delhi 110001
    } finally {
      setIsDetectingLocation(false);
    }
  };

  const handlePincodeChange = (pin: string) => {
    setUserPincode(pin);
    localStorage.setItem("omnicart_pincode", pin);
    localStorage.setItem("omnicart_location_chosen", "true");
    const pinMap: Record<string, string> = {
      "110001": "Delhi (NCR)",
      "400001": "Mumbai",
      "560001": "Bengaluru",
      "560049": "Bengaluru East",
      "560077": "Bengaluru North",
      "500001": "Hyderabad",
      "600001": "Chennai",
      "700001": "Kolkata",
      "380001": "Ahmedabad",
      "411001": "Pune",
      "122001": "Gurgaon",
      "201301": "Noida",
    };
    if (pinMap[pin]) {
      setPincodeCity(pinMap[pin]);
      localStorage.setItem("omnicart_city", pinMap[pin]);
    } else if (pin.length === 6) {
      setPincodeCity(`Pincode ${pin}`);
      localStorage.setItem("omnicart_city", `Pincode ${pin}`);
    }
  };

  const confirmLocationChoice = (pin: string, city: string) => {
    setUserPincode(pin);
    setPincodeCity(city);
    localStorage.setItem("omnicart_pincode", pin);
    localStorage.setItem("omnicart_city", city);
    localStorage.setItem("omnicart_location_chosen", "true");
    setShowLocationModal(false);
  };

  const activeProduct: ProductDetail | null =
    liveResolvedProduct ||
    (activeProductId ? PRODUCTS_DB[activeProductId] : null);

  // Real delivery message directly from marketplace API or computed dynamically
  const displayDeliveryStatus = activeProduct
    ? activeProduct.pincodeDeliveryStatus ||
      (activeProduct.sellers && activeProduct.sellers[0]?.deliveryDays) ||
      `Standard Delivery to ${userPincode} in 3-5 business days`
    : "";

  const computedDeliveryCharge = activeProduct
    ? activeProduct.deliveryCharge !== undefined
      ? activeProduct.deliveryCharge
      : activeProduct.livePrice >= 499
        ? 0
        : 40
    : 0;

  // Real-time backend query execution
  const executeQuery = async (queryText: string) => {
    if (!queryText.trim()) return;

    setApiError(null);
    setIsLoadingApi(true);
    setSelectedPoint(null);
    setSelectedImageIndex(0);

    // Save search query to history
    setSearchHistory((prev) => {
      const next = [
        queryText.trim(),
        ...prev.filter((item) => item !== queryText.trim()),
      ];
      return next.slice(0, 6);
    });

    try {
      const res = await fetch(
        `${API_BASE}/resolve?query=${encodeURIComponent(queryText.trim())}&pincode=${userPincode}`,
      );

      if (res.ok) {
        const data = await res.json();

        if (data.status === "unavailable") {
          setLiveResolvedProduct(null);
          setActiveProductId(null);
          setApiError({
            message:
              data.status_message ||
              "We couldn't read this product. Open the store to check the price.",
            storeUrl: data.canonical_url || undefined,
          });
          return;
        }

        const mapped: ProductDetail = {
          id: data.id,
          title: data.title,
          category: data.category,
          store: data.platform,
          storeUrl: data.canonical_url,
          rating: data.rating,
          ratingsCount: data.ratings_count,
          livePrice: data.live_price,
          regularPrice: data.regular_price,
          allTimeLow: data.all_time_low,
          allTimeHigh: data.all_time_high,
          productImages:
            data.gallery_images && data.gallery_images.length > 0
              ? data.gallery_images.filter(Boolean)
              : data.image_url
                ? [data.image_url]
                : [],
          prediction: {
            badge: data.prediction.badge as any,
            detail: data.prediction.detail,
            dropLikelihood: data.prediction.drop_likelihood,
          },
          history: data.history,
          historySource: data.history_source,
          historyDataPoints: data.history_data_points,
          sellers: data.sellers.map((s: any) => ({
            id: s.id,
            name: s.name,
            price: s.price,
            rating: s.rating,
            reviewsCount: s.reviews_count,
            deliveryDays: s.delivery_days,
            badge: s.badge as any,
            isBestSeller: s.is_best_seller,
            score: s.score,
            storeUrl: s.store_url,
          })),
          competitors: (data.competitors || []).map((c: any) => ({
            platform: c.platform,
            title: c.title,
            price: c.price,
            deliveryInfo: c.delivery_info,
            deliveryFee: c.delivery_fee,
            combinedDiscountText: c.combined_discount_text,
            effectiveFinalPrice: c.effective_final_price,
            storeUrl: c.store_url,
            isCheaper: c.is_cheaper,
            badge: c.badge,
            matchTier: c.match_tier,
            mismatchAttributes: c.mismatch_attributes || [],
          })),
          similarStyles: (data.similar_styles || []).map((c: any) => ({
            platform: c.platform,
            title: c.title,
            price: c.price,
            deliveryInfo: c.delivery_info,
            deliveryFee: c.delivery_fee,
            combinedDiscountText: c.combined_discount_text,
            effectiveFinalPrice: c.effective_final_price,
            storeUrl: c.store_url,
            isCheaper: c.is_cheaper,
            badge: c.badge,
            matchTier: c.match_tier,
            mismatchAttributes: c.mismatch_attributes || [],
          })),
          purchaseOptions: (data.purchase_options || []).map((opt: any) => ({
            type: opt.type,
            name: opt.name,
            value: opt.value,
            price: opt.price,
            isAvailable: opt.is_available,
            isSelected: opt.is_selected,
            url: opt.url,
            imageUrl: opt.image_url,
            stockInfo: opt.stock_info,
          })),
          specifications: data.specifications || {},
          highlights: data.highlights || [],
          pincode: data.pincode,
          pincodeDeliveryStatus: data.pincode_delivery_status,
          deliveryCharge: data.delivery_charge,
          coupons: data.coupons.map((c: any) => ({
            code: c.code,
            source: c.source,
            discountText: c.discount_text,
            discountAmount: c.discount_amount,
            successRate: c.success_rate,
          })),
          paymentOptions: data.payment_options.map((p: any) => ({
            title: p.title,
            type: p.type as any,
            effectiveSavings: p.effective_savings,
            finalPrice: p.final_price,
            explanation: p.explanation,
            isRecommended: p.is_recommended,
          })),
          smartStack: data.smart_stack
            ? {
                storeCouponCode: data.smart_stack.store_coupon_code,
                storeCouponSource: data.smart_stack.store_coupon_source,
                storeCouponSavings: data.smart_stack.store_coupon_savings,
                cardTitle: data.smart_stack.card_title,
                cardType: data.smart_stack.card_type,
                cardSavings: data.smart_stack.card_savings,
                combinedTotalSavings: data.smart_stack.combined_total_savings,
                finalStackedPrice: data.smart_stack.final_stacked_price,
                discountPercentage: data.smart_stack.discount_percentage,
                executionSteps: data.smart_stack.execution_steps || [],
              }
            : undefined,
        };

        setSelectedImageIndex(0);
        setLiveResolvedProduct(mapped);
      } else {
        let detail =
          "Could not resolve this product. Check the link and try again.";
        try {
          const body = await res.json();
          if (body?.detail) detail = body.detail;
        } catch {
          // Keep the generic message.
        }
        setLiveResolvedProduct(null);
        setActiveProductId(null);
        setApiError({ message: detail });
      }
    } catch {
      setLiveResolvedProduct(null);
      setActiveProductId(null);
      setApiError({
        message: `Could not reach the OmniCart backend at ${API_BASE}. Start the backend and try again.`,
      });
    } finally {
      setIsLoadingApi(false);
    }
  };

  const handleSearch = (e?: React.FormEvent) => {
    if (e && e.preventDefault) e.preventDefault();
    executeQuery(searchQuery);
  };

  const handleSelectOption = (option: PurchaseOption) => {
    if (!activeProduct) return;

    // Update purchaseOptions
    const updatedOptions = (activeProduct.purchaseOptions || []).map((opt) => {
      if (opt.type === option.type) {
        return { ...opt, isSelected: opt.value === option.value };
      }
      return opt;
    });

    const newPrice =
      option.price && option.price > 0 ? option.price : activeProduct.livePrice;
    const newStoreUrl = option.url || activeProduct.storeUrl;
    const newDeliveryStatus =
      option.type === "channel" && option.stockInfo
        ? option.stockInfo
        : activeProduct.pincodeDeliveryStatus;

    const updated: ProductDetail = {
      ...activeProduct,
      livePrice: newPrice,
      storeUrl: newStoreUrl,
      purchaseOptions: updatedOptions,
      pincodeDeliveryStatus: newDeliveryStatus,
    };

    setLiveResolvedProduct(updated);

    // If the option has a dedicated distinct URL (e.g. Amazon ASIN or Westside URL) and is not a channel toggle, refresh variant details
    if (
      option.url &&
      option.url !== activeProduct.storeUrl &&
      option.type !== "channel"
    ) {
      executeQuery(option.url);
    }
  };

  const selectProduct = (id: string) => {
    setActiveProductId(id);
    setLiveResolvedProduct(null);
    setSelectedImageIndex(0);
    setSelectedPoint(null);
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  // Cart Management
  const addToCart = (product: ProductDetail) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        );
      }
      return [
        ...prev,
        {
          id: product.id,
          title: product.title,
          store: product.store,
          storeUrl: product.storeUrl,
          image: product.productImages[0],
          price: product.livePrice,
          regularPrice: product.regularPrice,
          deliveryDays: displayDeliveryStatus,
          quantity: 1,
        },
      ];
    });
    setCartOpen(true);
  };

  const removeFromCart = (id: string) => {
    setCartItems((prev) => prev.filter((item) => item.id !== id));
  };

  const cartTotal = cartItems.reduce(
    (acc, item) => acc + item.price * item.quantity,
    0,
  );
  const cartRegularTotal = cartItems.reduce(
    (acc, item) => acc + item.regularPrice * item.quantity,
    0,
  );
  const totalCartSavings = cartRegularTotal - cartTotal;

  const executeAutoSnipe = () => {
    setIsOrdering(true);
    setTimeout(() => {
      setIsOrdering(false);
      setOrderModalOpen(true);
    }, 850);
  };

  const chartData = activeProduct
    ? activeProduct.history[timeRange] || activeProduct.history["1Y"] || []
    : [];
  const discountPercent =
    activeProduct &&
    activeProduct.regularPrice > 0 &&
    activeProduct.livePrice > 0
      ? Math.round(
          ((activeProduct.regularPrice - activeProduct.livePrice) /
            activeProduct.regularPrice) *
            100,
        )
      : 0;

  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-emerald-500/20 selection:text-emerald-900 dark:selection:bg-emerald-500/30 dark:selection:text-emerald-200 antialiased transition-colors duration-200">
      {/* 0. Location Request Modal (Prominently asks user on load until resolved/confirmed) */}
      <AnimatePresence>
        {showLocationModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-slate-950/50 backdrop-blur-sm"
              onClick={() => setShowLocationModal(false)}
            />
            <motion.div
              initial={{ scale: 0.96, opacity: 0, y: 8 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.96, opacity: 0, y: 8 }}
              className="relative w-full max-w-md bg-white dark:bg-[#111827] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 shadow-2xl z-10"
            >
              <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/80 dark:border-emerald-800/60 text-emerald-600 dark:text-emerald-400">
                    <MapPin className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-base text-neutral-900 dark:text-neutral-100">
                      Select Delivery Location
                    </h3>
                    <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                      Required for live dark-store & shipping rates
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowLocationModal(false)}
                  className="p-1 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="py-4 space-y-4">
                <button
                  onClick={requestBrowserLocation}
                  disabled={isDetectingLocation}
                  className="w-full py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-neutral-950 font-medium text-sm flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs"
                >
                  {isDetectingLocation ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Navigation className="h-4 w-4" />
                  )}
                  <span>
                    {isDetectingLocation
                      ? "Detecting Precise Location..."
                      : "Use Current GPS Location"}
                  </span>
                </button>

                <div className="flex items-center gap-2 text-xs font-mono text-neutral-400 dark:text-neutral-500">
                  <div className="flex-1 h-px bg-neutral-200 dark:bg-neutral-800" />
                  <span>OR SELECT CITY HUB</span>
                  <div className="flex-1 h-px bg-neutral-200 dark:bg-neutral-800" />
                </div>

                {/* Popular Indian Metro hubs */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { city: "Bengaluru", pin: "560001" },
                    { city: "Bengaluru East", pin: "560049" },
                    { city: "Delhi (NCR)", pin: "110001" },
                    { city: "Mumbai", pin: "400001" },
                    { city: "Hyderabad", pin: "500001" },
                    { city: "Chennai", pin: "600001" },
                  ].map((loc) => (
                    <button
                      key={loc.pin}
                      onClick={() => confirmLocationChoice(loc.pin, loc.city)}
                      className="p-2.5 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-emerald-500 dark:hover:border-emerald-500 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 text-left transition-all cursor-pointer flex flex-col"
                    >
                      <span className="font-semibold text-neutral-900 dark:text-neutral-100">
                        {loc.city}
                      </span>
                      <span className="text-[10px] text-neutral-500 dark:text-neutral-400 font-mono">
                        {loc.pin}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Custom Pincode input in modal */}
                <div className="pt-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      placeholder="Enter 6-digit Pincode..."
                      value={userPincode}
                      onChange={(e) => handlePincodeChange(e.target.value)}
                      className="flex-1 p-2.5 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                    <button
                      onClick={() =>
                        confirmLocationChoice(userPincode, pincodeCity)
                      }
                      className="px-4 py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 rounded-xl font-medium text-xs cursor-pointer transition-colors shadow-xs"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 1. Header Navigation */}
      <nav className="border-b border-neutral-200/80 dark:border-neutral-800 bg-white/80 dark:bg-[#09090B]/80 backdrop-blur-md sticky top-0 z-40 transition-colors duration-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-15 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-neutral-900 text-white dark:bg-white dark:text-neutral-950 flex items-center justify-center font-bold text-xs tracking-tight shadow-xs">
              Ω
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-base tracking-tight text-neutral-950 dark:text-neutral-50">
                OmniCart
              </span>
              <span className="hidden sm:inline-block h-1 w-1 rounded-full bg-neutral-300 dark:bg-neutral-700" />
              <Link
                href="/deals"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-950/60 border border-amber-200/80 dark:border-amber-800/80 text-amber-700 dark:text-amber-300 font-semibold text-xs hover:bg-amber-100 dark:hover:bg-amber-900/60 transition-colors shadow-2xs"
              >
                <Flame className="h-3 w-3 text-amber-500 fill-amber-500" />
                <span>Live Drops</span>
              </Link>
            </div>
          </div>

          {/* User Location, Theme & Cart Controls */}
          <div className="flex items-center gap-2 sm:gap-3 text-xs">
            {/* Pincode Controller */}
            <div
              onClick={() => setShowLocationModal(true)}
              className="flex items-center gap-2 bg-neutral-100 dark:bg-neutral-900 px-3 py-1.5 rounded-full border border-neutral-200/80 dark:border-neutral-800 text-neutral-900 dark:text-neutral-100 cursor-pointer hover:border-emerald-500/50 transition-colors shadow-2xs"
              title="Click to change delivery location"
            >
              <MapPin className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
              <span className="font-medium text-[11px] sm:text-xs truncate max-w-[85px] sm:max-w-none">
                {pincodeCity}
              </span>
              <span className="font-mono font-bold tracking-wider px-1.5 py-0.5 rounded bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-[11px]">
                {userPincode}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  requestBrowserLocation();
                }}
                disabled={isDetectingLocation}
                title="Detect current GPS location"
                className="p-0.5 hover:bg-neutral-200 dark:hover:bg-neutral-800 rounded-full transition-colors cursor-pointer"
              >
                {isDetectingLocation ? (
                  <Loader2 className="h-3 w-3 animate-spin text-emerald-600" />
                ) : (
                  <Navigation className="h-3 w-3 text-neutral-400 hover:text-emerald-600 dark:hover:text-emerald-400" />
                )}
              </button>
            </div>

            {/* Dark / Light Mode Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full border border-neutral-200/80 dark:border-neutral-800 bg-neutral-100 dark:bg-neutral-900 hover:bg-neutral-200 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 transition-colors cursor-pointer"
              title={`Switch to ${theme === "light" ? "Dark" : "Light"} theme`}
            >
              {theme === "light" ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Sun className="h-4 w-4 text-amber-400" />
              )}
            </button>

            {/* Cart Button with Count Badge */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-2 rounded-xl bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 transition-all cursor-pointer flex items-center justify-center shadow-xs"
              title="Open OmniCart Checkout Drawer"
            >
              <ShoppingCart className="h-4 w-4" />
              {cartItems.length > 0 && (
                <span className="absolute -top-1.5 -right-1.5 h-4.5 w-4.5 rounded-full bg-emerald-600 text-white font-mono text-[10px] font-bold flex items-center justify-center border-2 border-white dark:border-neutral-950 shadow-xs">
                  {cartItems.reduce((a, b) => a + b.quantity, 0)}
                </span>
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* 2. Streamlined Search Dock */}
      <section
        className={`px-4 sm:px-6 max-w-4xl mx-auto w-full transition-all duration-300 ${
          activeProduct ? "pt-6 pb-2" : "pt-14 sm:pt-20 pb-8 text-center"
        }`}
      >
        {!activeProduct && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="mb-8"
          >
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200/60 dark:border-emerald-800/50 text-emerald-800 dark:text-emerald-300 text-xs font-medium mb-4">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Universal Price Arbitrage & Real-Time Deal Tracking</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50 mb-3">
              Real prices. Honest answers.
            </h1>
            <p className="text-sm sm:text-base text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto font-normal leading-relaxed">
              Paste a product link or Amazon ASIN. OmniCart shows the live
              price, verified price history when available, and a clear message
              when a store can no longer be read.
            </p>
          </motion.div>
        )}

        {/* Search Bar */}
        <form
          onSubmit={handleSearch}
          className="max-w-2xl mx-auto relative mb-3"
        >
          <div className="flex items-center bg-white dark:bg-[#121215] border border-neutral-200/90 dark:border-neutral-800/80 rounded-2xl p-1.5 sm:p-2 shadow-xs hover:border-neutral-300 dark:hover:border-neutral-700 focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-500 transition-all">
            <Search className="h-4 sm:h-5 w-4 sm:w-5 text-neutral-400 ml-3 flex-shrink-0" />
            <input
              type="text"
              placeholder="Paste any product URL or ASIN (Amazon, Flipkart, Myntra, Westside, Zepto)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-transparent border-none px-3 py-2 text-xs sm:text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500 focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="p-1.5 mr-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 transition-colors"
                title="Clear query"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
            <button
              type="submit"
              disabled={isLoadingApi}
              className="px-5 py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white font-medium text-xs sm:text-sm rounded-xl transition-colors flex-shrink-0 cursor-pointer flex items-center gap-1.5 shadow-xs"
            >
              {isLoadingApi && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {isLoadingApi ? "Analyzing..." : "Inspect Live"}
            </button>
          </div>
        </form>

        {apiError && (
          <div className="max-w-2xl mx-auto mb-3 flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-left text-xs sm:text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <div className="flex-1">
              <p>{apiError.message}</p>
              {apiError.storeUrl && (
                <a
                  href={apiError.storeUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 font-medium underline underline-offset-2"
                >
                  Open store <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
            <button
              type="button"
              onClick={() => setApiError(null)}
              className="rounded p-1 hover:bg-red-100 dark:hover:bg-red-900/40"
              aria-label="Dismiss error"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Recent Search History Chips */}
        {searchHistory.length > 0 && (
          <div className="flex items-center justify-center gap-1.5 text-xs text-neutral-500 dark:text-neutral-400 flex-wrap">
            <span className="flex items-center gap-1 text-[11px] text-neutral-400 mr-1">
              <History className="h-3 w-3" /> Recent:
            </span>
            {searchHistory.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSearchQuery(item);
                  executeQuery(item);
                }}
                className="px-2.5 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800/80 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 text-[11px] truncate max-w-[200px] cursor-pointer transition-colors font-mono"
                title={item}
              >
                {
                  item
                    .replace("https://www.", "")
                    .replace("https://", "")
                    .split("?")[0]
                }
              </button>
            ))}
          </div>
        )}
      </section>

      {/* 3. Main Product Showcase or Clean Empty Home State */}
      <main className="max-w-4xl mx-auto px-6 pb-20 w-full flex-1 flex flex-col gap-6">
        {activeProduct ? (
          <>
            <motion.div
              layout
              initial={{ opacity: 0, scale: 0.99 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25 }}
              className="rounded-2xl p-6 sm:p-8 border border-neutral-200/90 dark:border-neutral-800 bg-white dark:bg-[#121215] shadow-xs relative"
            >
              <div className="flex flex-col md:flex-row gap-8 items-start">
                {/* Product Imagery */}
                <div className="flex flex-col gap-3 w-full md:w-68 flex-shrink-0">
                  <div className="w-full h-68 sm:h-72 rounded-xl overflow-hidden bg-neutral-50/60 dark:bg-neutral-900/40 border border-neutral-200/60 dark:border-neutral-800/60 relative flex items-center justify-center">
                    <img
                      src={
                        activeProduct.productImages[selectedImageIndex] ||
                        activeProduct.productImages[0]
                      }
                      alt={activeProduct.title}
                      className="w-full h-full object-contain p-3 transition-transform duration-200 hover:scale-105"
                    />
                    <a
                      href={activeProduct.storeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="absolute bottom-2.5 left-2.5 inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white/90 dark:bg-neutral-900/90 backdrop-blur-xs text-neutral-800 dark:text-neutral-200 text-[11px] font-medium border border-neutral-200/80 dark:border-neutral-700/80 hover:border-emerald-500 transition-colors shadow-2xs"
                    >
                      <span>{activeProduct.store}</span>
                      <ExternalLink className="h-3 w-3 text-neutral-400" />
                    </a>
                  </div>

                  {/* Thumbnail Row */}
                  {activeProduct.productImages.length > 1 && (
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {activeProduct.productImages.map((img, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedImageIndex(idx)}
                          className={`h-11 w-11 rounded-lg overflow-hidden border transition-all cursor-pointer flex-shrink-0 bg-white dark:bg-neutral-900 ${
                            selectedImageIndex === idx
                              ? "border-emerald-500 ring-2 ring-emerald-500/20"
                              : "border-neutral-200 dark:border-neutral-800 opacity-60 hover:opacity-100"
                          }`}
                        >
                          <img
                            src={img}
                            alt="thumbnail"
                            className="w-full h-full object-contain p-1"
                          />
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Product Info & Direct Actions */}
                <div className="flex-1 flex flex-col justify-between h-full w-full">
                  <div>
                    {/* Top Row: Category + Wishlist */}
                    <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 mb-2">
                      <span className="font-medium tracking-wide uppercase text-[10px] text-neutral-400 dark:text-neutral-500">
                        {activeProduct.category}
                      </span>
                      <button
                        onClick={() => setIsWishlisted(!isWishlisted)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-300 transition-colors cursor-pointer text-xs"
                      >
                        <Heart
                          className={`h-3.5 w-3.5 ${isWishlisted ? "fill-rose-500 text-rose-500" : ""}`}
                        />
                        <span>{isWishlisted ? "Saved" : "Track"}</span>
                      </button>
                    </div>

                    {/* Product Title */}
                    <h2 className="text-xl sm:text-2xl font-semibold text-neutral-950 dark:text-neutral-50 leading-snug tracking-tight">
                      {activeProduct.title}
                    </h2>

                    {/* Rating & Real Delivery Status */}
                    <div className="flex flex-wrap items-center gap-2 mt-2.5 text-xs text-neutral-600 dark:text-neutral-300">
                      <span className="font-semibold text-neutral-900 dark:text-neutral-100">
                        ★ {activeProduct.rating}
                      </span>
                      <span className="text-neutral-400">
                        ({activeProduct.ratingsCount.toLocaleString()})
                      </span>
                      <span className="text-neutral-300 dark:text-neutral-700">
                        •
                      </span>
                      <span className="inline-flex items-center gap-1 text-neutral-700 dark:text-neutral-300">
                        <Truck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>{displayDeliveryStatus}</span>
                      </span>
                      <span className="text-neutral-300 dark:text-neutral-700">
                        •
                      </span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold font-mono">
                        {computedDeliveryCharge === 0
                          ? "FREE Delivery"
                          : `+₹${computedDeliveryCharge}`}
                      </span>
                    </div>

                    {/* Variant & Option Selectors (Clean Inline Layout) */}
                    {activeProduct.purchaseOptions &&
                      activeProduct.purchaseOptions.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-800/80 flex flex-col gap-3">
                          {/* Delivery Channel / Mode */}
                          {(() => {
                            const channelOptions =
                              activeProduct.purchaseOptions.filter(
                                (o) => o.type === "channel",
                              );
                            if (channelOptions.length === 0) return null;
                            const selectedChannel =
                              channelOptions.find((o) => o.isSelected) ||
                              channelOptions[0];

                            return (
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400 w-14 flex-shrink-0">
                                  Mode:
                                </span>
                                <div className="inline-flex p-0.5 rounded-lg bg-neutral-100 dark:bg-neutral-800/80 border border-neutral-200/60 dark:border-neutral-700/60 gap-0.5">
                                  {channelOptions.map((opt, idx) => {
                                    const isSel =
                                      opt.isSelected ||
                                      (selectedChannel &&
                                        opt.value === selectedChannel.value);
                                    const isNow = opt.value
                                      .toLowerCase()
                                      .includes("now");
                                    return (
                                      <button
                                        key={idx}
                                        onClick={() => handleSelectOption(opt)}
                                        className={`px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                                          isSel
                                            ? "bg-white dark:bg-neutral-700 text-neutral-950 dark:text-neutral-50 shadow-xs font-semibold"
                                            : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                                        }`}
                                      >
                                        {isNow ? (
                                          <Zap className="h-3 w-3 fill-emerald-600 text-emerald-600 dark:fill-emerald-400 dark:text-emerald-400" />
                                        ) : (
                                          <Truck className="h-3 w-3 text-neutral-500" />
                                        )}
                                        <span>{opt.value}</span>
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })()}

                          {/* Size Options */}
                          {(() => {
                            const sizeOptions =
                              activeProduct.purchaseOptions.filter(
                                (o) =>
                                  o.type === "size" ||
                                  o.name.toLowerCase().includes("size"),
                              );
                            if (sizeOptions.length === 0) return null;
                            const selectedSize =
                              sizeOptions.find((o) => o.isSelected) ||
                              sizeOptions[0];

                            return (
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400 w-14 flex-shrink-0">
                                  Size:
                                </span>
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  {sizeOptions.map((opt, idx) => {
                                    const isSel =
                                      opt.isSelected ||
                                      (selectedSize &&
                                        opt.value === selectedSize.value);
                                    return (
                                      <button
                                        key={idx}
                                        onClick={() => handleSelectOption(opt)}
                                        className={`min-w-[34px] h-7.5 px-2.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center justify-center gap-1 ${
                                          isSel
                                            ? "bg-neutral-900 text-white dark:bg-white dark:text-neutral-950 font-semibold shadow-xs"
                                            : "bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700"
                                        }`}
                                      >
                                        <span>{opt.value}</span>
                                        {opt.price &&
                                          opt.price !==
                                            activeProduct.livePrice && (
                                            <span className="text-[10px] opacity-70">
                                              ₹{opt.price}
                                            </span>
                                          )}
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })()}

                          {/* Colour Options */}
                          {(() => {
                            const colorOptions =
                              activeProduct.purchaseOptions.filter(
                                (o) =>
                                  o.type === "color" ||
                                  o.name.toLowerCase().includes("col"),
                              );
                            if (colorOptions.length === 0) return null;
                            const selectedColor =
                              colorOptions.find((o) => o.isSelected) ||
                              colorOptions[0];

                            return (
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400 w-14 flex-shrink-0">
                                  Colour:
                                </span>
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  {colorOptions.map((opt, idx) => {
                                    const isSel =
                                      opt.isSelected ||
                                      (selectedColor &&
                                        opt.value === selectedColor.value);
                                    return (
                                      <button
                                        key={idx}
                                        onClick={() => handleSelectOption(opt)}
                                        className={`px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                                          isSel
                                            ? "bg-emerald-50 text-emerald-900 border border-emerald-300 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-700 font-semibold shadow-2xs"
                                            : "bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700"
                                        }`}
                                      >
                                        <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" />
                                        <span>{opt.value}</span>
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                      )}
                  </div>

                  {/* Price Row & Primary Actions */}
                  <div className="pt-6 mt-6 border-t border-neutral-100 dark:border-neutral-800/80 flex flex-wrap items-end justify-between gap-4">
                    <div>
                      <div className="flex items-baseline gap-2.5 flex-wrap">
                        {activeProduct.livePrice > 0 ? (
                          <>
                            <span className="text-3xl sm:text-4xl font-bold text-neutral-950 dark:text-neutral-50 tracking-tight font-mono">
                              ₹{activeProduct.livePrice.toLocaleString()}
                            </span>
                            {activeProduct.regularPrice >
                              activeProduct.livePrice && (
                              <span className="text-base line-through text-neutral-400 dark:text-neutral-500 font-mono">
                                ₹{activeProduct.regularPrice.toLocaleString()}
                              </span>
                            )}
                            {discountPercent > 0 && (
                              <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800 text-xs font-mono font-bold">
                                {discountPercent}% OFF
                              </span>
                            )}
                            {activeProduct.smartStack &&
                              activeProduct.smartStack.combinedTotalSavings >
                                0 && (
                                <button
                                  type="button"
                                  onClick={() => setActiveTab("payment")}
                                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white font-mono text-xs font-bold transition-all cursor-pointer shadow-xs"
                                  title="Click to view store offer + card discount combination"
                                >
                                  <Zap className="h-3 w-3 fill-white" />
                                  <span>
                                    Stack to ₹
                                    {activeProduct.smartStack.finalStackedPrice.toLocaleString()}{" "}
                                    (Save ₹
                                    {activeProduct.smartStack.combinedTotalSavings.toLocaleString()}
                                    )
                                  </span>
                                </button>
                              )}
                          </>
                        ) : (
                          <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                            Check Live Price on Store
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2.5 text-xs text-neutral-400 dark:text-neutral-500 mt-1.5 font-mono">
                        <span>
                          Low: ₹{activeProduct.allTimeLow.toLocaleString()}
                        </span>
                        <span>•</span>
                        <span>
                          High: ₹{activeProduct.allTimeHigh.toLocaleString()}
                        </span>
                      </div>
                    </div>

                    {/* Primary Action Buttons */}
                    <div className="flex items-center gap-2.5">
                      <button
                        onClick={() => addToCart(activeProduct)}
                        className="px-4 py-2.5 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-100 font-medium text-xs sm:text-sm flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                      >
                        <ShoppingCart className="h-4 w-4" />
                        <span>Add to Cart</span>
                      </button>

                      <button
                        onClick={executeAutoSnipe}
                        disabled={isOrdering}
                        className="px-5 py-2.5 rounded-xl bg-neutral-950 hover:bg-neutral-800 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
                      >
                        <Zap className="h-4 w-4 fill-white" />
                        <span>
                          {isOrdering ? "Securing Order..." : "Fast Checkout"}
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Price Advisory Row */}
              <div className="mt-6 pt-4 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400">
                  <TrendingDown className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                  <span className="leading-relaxed">
                    <strong className="text-neutral-900 dark:text-neutral-200">
                      Price Advisory:
                    </strong>{" "}
                    {activeProduct.prediction.detail}
                  </span>
                </div>
                <span className="px-2.5 py-0.5 rounded-md bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 font-mono text-[10px] font-bold flex-shrink-0">
                  {activeProduct.prediction.badge}
                </span>
              </div>
            </motion.div>

            {/* 4. Segmented Tab Navigation Bar */}
            <div className="p-1 rounded-xl bg-neutral-100 dark:bg-neutral-900/90 border border-neutral-200/80 dark:border-neutral-800 flex items-center gap-1 overflow-x-auto text-xs font-medium">
              <button
                onClick={() => setActiveTab("comparison")}
                className={`px-3.5 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 flex-shrink-0 ${
                  activeTab === "comparison"
                    ? "bg-white dark:bg-neutral-800 text-neutral-950 dark:text-white shadow-xs font-semibold"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                <span>Cross-Platform Comparison</span>
                {activeProduct.competitors &&
                  activeProduct.competitors.length > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 text-[10px] font-mono font-bold">
                      {activeProduct.competitors.length}
                    </span>
                  )}
              </button>

              <button
                onClick={() => setActiveTab("history")}
                className={`px-3.5 py-2 rounded-lg transition-all cursor-pointer flex-shrink-0 ${
                  activeTab === "history"
                    ? "bg-white dark:bg-neutral-800 text-neutral-950 dark:text-white shadow-xs font-semibold"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                }`}
              >
                Price History & Analytics
              </button>

              <button
                onClick={() => setActiveTab("sellers")}
                className={`px-3.5 py-2 rounded-lg transition-all cursor-pointer flex-shrink-0 ${
                  activeTab === "sellers"
                    ? "bg-white dark:bg-neutral-800 text-neutral-950 dark:text-white shadow-xs font-semibold"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                }`}
              >
                Marketplace Sellers ({activeProduct.sellers.length})
              </button>

              <button
                onClick={() => setActiveTab("payment")}
                className={`px-3.5 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 flex-shrink-0 ${
                  activeTab === "payment"
                    ? "bg-white dark:bg-neutral-800 text-neutral-950 dark:text-white shadow-xs font-semibold"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                }`}
              >
                <Zap className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Smart Stack & Coupons</span>
              </button>

              <button
                onClick={() => setActiveTab("specs")}
                className={`px-3.5 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 flex-shrink-0 ${
                  activeTab === "specs"
                    ? "bg-white dark:bg-neutral-800 text-neutral-950 dark:text-white shadow-xs font-semibold"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                }`}
              >
                <Tag className="h-3.5 w-3.5" />
                <span>Specifications</span>
              </button>
            </div>

            {/* Dynamic Tab Content with Smooth Transitions */}
            <AnimatePresence mode="wait">
              {/* TAB 0: Cross-Platform Competitor Comparison Matrix */}
              {activeTab === "comparison" && (
                <motion.div
                  key="comparison"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="rounded-2xl p-6 sm:p-7 bg-white dark:bg-[#121215] border border-neutral-200/90 dark:border-neutral-800 flex flex-col gap-5 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
                        Available Elsewhere Cheaper?
                      </h3>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400">
                        Cross-marketplace price comparison for{" "}
                        {activeProduct.title}
                      </p>
                    </div>
                    <span className="text-xs text-neutral-500 dark:text-neutral-400 bg-neutral-100 dark:bg-neutral-800/80 px-3 py-1 rounded-full self-start font-mono">
                      Delivering to {userPincode} ({pincodeCity})
                    </span>
                  </div>

                  {/* TIER 1: 1:1 Verified Exact Match Section */}
                  {activeProduct.competitors &&
                  activeProduct.competitors.length > 0 ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          100% VERIFIED EXACT MATCH
                        </span>
                        <span className="text-xs text-neutral-400 dark:text-neutral-500">
                          Identical SKU verified across retailers
                        </span>
                      </div>
                      {activeProduct.competitors.map((comp, idx) => {
                        const priceDiff =
                          activeProduct.livePrice - comp.effectiveFinalPrice;
                        return (
                          <div
                            key={idx}
                            className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
                              comp.isCheaper
                                ? "bg-emerald-50/20 dark:bg-emerald-950/20 border-emerald-300 dark:border-emerald-800/80 shadow-xs"
                                : "border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#121215] hover:border-neutral-300 dark:hover:border-neutral-700"
                            }`}
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                                  {comp.platform}
                                </span>
                                {comp.badge && (
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200">
                                    {comp.badge}
                                  </span>
                                )}
                                {comp.isCheaper && priceDiff > 0 && (
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-600 text-white">
                                    Save ₹{Math.round(priceDiff)}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-neutral-600 dark:text-neutral-300 mt-1">
                                {comp.title}
                              </p>
                              <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1.5 flex items-center gap-3 font-mono">
                                <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                                  {comp.combinedDiscountText}
                                </span>
                                <span>•</span>
                                <span>{comp.deliveryInfo}</span>
                              </div>
                            </div>

                            <div className="flex items-center justify-between sm:justify-end gap-4 border-t sm:border-t-0 pt-3 sm:pt-0 border-neutral-100 dark:border-neutral-800">
                              <div className="text-right">
                                <div className="text-base font-bold font-mono text-neutral-900 dark:text-neutral-100">
                                  ₹{comp.effectiveFinalPrice.toLocaleString()}
                                </div>
                                <span className="text-[10px] text-neutral-400 dark:text-neutral-500 block font-mono">
                                  Base: ₹{comp.price.toLocaleString()}
                                </span>
                              </div>

                              <a
                                href={comp.storeUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-4 py-2 rounded-xl bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                              >
                                <span>Open on {comp.platform}</span>
                                <ArrowUpRight className="h-3.5 w-3.5" />
                              </a>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="p-8 text-center flex flex-col items-center justify-center gap-2 bg-neutral-50 dark:bg-neutral-900/40 rounded-xl border border-dashed border-neutral-200 dark:border-neutral-800">
                      <div className="h-8 w-8 rounded-full bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 flex items-center justify-center font-bold text-xs">
                        <ShieldCheck className="h-4 w-4" />
                      </div>
                      <h4 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                        No 1:1 Identical Match Found on Other Marketplaces
                      </h4>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 max-w-md leading-relaxed">
                        We scanned Flipkart and Amazon India for an exact SKU
                        match. No identical 1:1 cross-listing exists. The live
                        direct price of ₹
                        {activeProduct.livePrice.toLocaleString()} on{" "}
                        {activeProduct.store} is currently unique.
                      </p>
                    </div>
                  )}
                </motion.div>
              )}

              {/* TAB 1: Price History Curve */}
              {activeTab === "history" && (
                <motion.div
                  key="history"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="rounded-2xl p-6 sm:p-7 bg-white dark:bg-[#121215] border border-neutral-200/90 dark:border-neutral-800 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">
                          Multi-Year Price Curve
                        </h3>
                        {activeProduct.historySource ===
                        "VERIFIED_AGGREGATOR" ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800 flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            VERIFIED DATA (
                            {activeProduct.historyDataPoints?.toLocaleString()}{" "}
                            PTS)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20">
                            ESTIMATED TRAJECTORY
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                        {activeProduct.historySource === "VERIFIED_AGGREGATOR"
                          ? "Directly extracted from Indian Price History archives with verified daily observations."
                          : "Trajectory anchored on live store price and historical price band."}
                      </p>
                    </div>

                    {/* Range Filters */}
                    <div className="flex items-center gap-1 bg-neutral-100 dark:bg-neutral-900 p-1 rounded-xl border border-neutral-200/80 dark:border-neutral-800 self-start">
                      {(["1M", "6M", "1Y", "3Y", "ALL"] as const).map((r) => (
                        <button
                          key={r}
                          onClick={() => {
                            setTimeRange(r);
                            setSelectedPoint(null);
                          }}
                          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer ${
                            timeRange === r
                              ? "bg-white dark:bg-neutral-800 text-neutral-950 dark:text-white shadow-xs font-bold"
                              : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-950 dark:hover:text-white"
                          }`}
                        >
                          {r}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Selected Point Badge */}
                  {selectedPoint && (
                    <div className="mb-4 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800/80 flex items-center justify-between text-xs font-mono">
                      <div>
                        <span className="text-neutral-500">Date:</span>{" "}
                        <strong className="text-neutral-900 dark:text-neutral-100">
                          {selectedPoint.date}
                        </strong>
                      </div>
                      <div>
                        <span className="text-neutral-500">Price:</span>{" "}
                        <strong className="text-neutral-900 dark:text-neutral-100">
                          ₹{selectedPoint.price.toLocaleString()}
                        </strong>
                      </div>
                      <button
                        onClick={() => setSelectedPoint(null)}
                        className="text-xs text-emerald-700 dark:text-emerald-400 cursor-pointer font-medium"
                      >
                        Clear
                      </button>
                    </div>
                  )}

                  {/* Interactive Graph */}
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={chartData}
                        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                        onClick={(e: any) => {
                          if (e && e.activePayload && e.activePayload[0]) {
                            const payload = e.activePayload[0].payload;
                            setSelectedPoint({
                              date: payload.date,
                              price: payload.price,
                            });
                          }
                        }}
                      >
                        <defs>
                          <linearGradient
                            id="priceEmeraldGrad"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor="#10B981"
                              stopOpacity={0.25}
                            />
                            <stop
                              offset="95%"
                              stopColor="#10B981"
                              stopOpacity={0.0}
                            />
                          </linearGradient>
                        </defs>
                        <XAxis
                          dataKey="date"
                          stroke="#A1A1AA"
                          fontSize={11}
                          tickLine={false}
                          fontFamily="monospace"
                        />
                        <YAxis
                          stroke="#A1A1AA"
                          fontSize={11}
                          tickLine={false}
                          domain={["dataMin - 100", "dataMax + 100"]}
                          tickFormatter={(v) => `₹${v}`}
                          fontFamily="monospace"
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor:
                              theme === "dark" ? "#121215" : "#09090B",
                            borderColor:
                              theme === "dark" ? "#27272A" : "#27272A",
                            borderRadius: "0.75rem",
                            fontSize: "12px",
                            color: "#FFFFFF",
                            fontFamily: "monospace",
                            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                          }}
                          formatter={(val: unknown) => [
                            `₹${Number(val).toLocaleString()}`,
                            "Price",
                          ]}
                        />
                        <Area
                          type="monotone"
                          dataKey="price"
                          stroke="#10B981"
                          strokeWidth={2}
                          fill="url(#priceEmeraldGrad)"
                          activeDot={{
                            r: 4,
                            fill: "#10B981",
                            stroke: "#FFFFFF",
                            strokeWidth: 2,
                            cursor: "pointer",
                          }}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </motion.div>
              )}

              {/* TAB 2: Marketplace Sellers */}
              {activeTab === "sellers" && (
                <motion.div
                  key="sellers"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="rounded-2xl p-6 sm:p-7 bg-white dark:bg-[#121215] border border-neutral-200/90 dark:border-neutral-800 flex flex-col gap-4 shadow-xs"
                >
                  <div>
                    <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">
                      Marketplace Sellers Comparison
                    </h3>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">
                      Delivering to pincode {userPincode} ({pincodeCity})
                    </p>
                  </div>

                  <div className="space-y-2.5 mt-1">
                    {activeProduct.sellers.map((seller) => (
                      <div
                        key={seller.id}
                        className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
                          seller.isBestSeller
                            ? "bg-emerald-50/20 dark:bg-emerald-950/20 border-emerald-300 dark:border-emerald-800/80 shadow-xs"
                            : "border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#121215] hover:border-neutral-300 dark:hover:border-neutral-700"
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                              {seller.name}
                            </span>
                            {seller.isBestSeller && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800">
                                RECOMMENDED
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 flex items-center gap-2.5 font-mono">
                            <span>{seller.badge}</span>
                            <span>•</span>
                            <span>{seller.deliveryDays}</span>
                            <span>•</span>
                            <span>
                              ★ {seller.rating} (
                              {seller.reviewsCount.toLocaleString()})
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between sm:justify-end gap-4">
                          <div className="text-right">
                            <div className="text-base font-bold font-mono text-neutral-900 dark:text-neutral-100">
                              ₹{seller.price.toLocaleString()}
                            </div>
                            <span className="text-[10px] text-neutral-400 dark:text-neutral-500 font-mono">
                              Net Price
                            </span>
                          </div>
                          <a
                            href={seller.storeUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="px-4 py-2 rounded-xl bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                          >
                            Visit Store <ArrowUpRight className="h-3.5 w-3.5" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* TAB 3: Tested Coupons & Payment Stacking */}
              {activeTab === "payment" && (
                <motion.div
                  key="payment"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="rounded-2xl p-6 sm:p-7 bg-white dark:bg-[#121215] border border-neutral-200/90 dark:border-neutral-800 flex flex-col gap-7 shadow-xs"
                >
                  {/* ⚡ Smart Stack Arbitrage Combo Card */}
                  {activeProduct.smartStack &&
                    activeProduct.smartStack.combinedTotalSavings > 0 && (
                      <div className="p-5 sm:p-6 rounded-xl bg-neutral-50/70 dark:bg-neutral-900/40 border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-5">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div>
                            <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800 text-[11px] font-semibold mb-1.5">
                              <Zap className="h-3 w-3 text-emerald-600 dark:text-emerald-400 fill-current" />
                              <span>Maximum Savings Stack</span>
                            </div>
                            <h4 className="text-base sm:text-lg font-semibold text-neutral-950 dark:text-neutral-50 tracking-tight">
                              Store Promo + Payment Arbitrage Combo
                            </h4>
                            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                              Calculated lowest possible net checkout price by
                              combining store offers with credit card cashback.
                            </p>
                          </div>

                          {/* Net Price Callout */}
                          <div className="sm:text-right flex-shrink-0">
                            <span className="text-xs text-neutral-400 line-through font-mono block">
                              ₹{activeProduct.livePrice.toLocaleString()}
                            </span>
                            <div className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-emerald-600 dark:text-emerald-400">
                              ₹
                              {activeProduct.smartStack.finalStackedPrice.toLocaleString()}
                            </div>
                            <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 font-mono">
                              Save ₹
                              {activeProduct.smartStack.combinedTotalSavings.toLocaleString()}{" "}
                              ({activeProduct.smartStack.discountPercentage}%
                              OFF)
                            </span>
                          </div>
                        </div>

                        {/* 3-Step Linear Equation Flow */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="p-3.5 rounded-lg bg-white dark:bg-[#121215] border border-neutral-200/70 dark:border-neutral-800">
                            <div className="text-[10px] font-medium text-neutral-400 uppercase tracking-wider">
                              Step 1 • Store Offer
                            </div>
                            <div className="mt-1 flex items-baseline justify-between">
                              <span className="font-mono text-xs font-semibold text-neutral-900 dark:text-neutral-100">
                                {activeProduct.smartStack.storeCouponCode ||
                                  "Store Discount"}
                              </span>
                              <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                                -₹
                                {activeProduct.smartStack.storeCouponSavings.toLocaleString()}
                              </span>
                            </div>
                            <div className="text-[11px] text-neutral-500 mt-1 truncate">
                              {activeProduct.smartStack.storeCouponSource}
                            </div>
                          </div>

                          <div className="p-3.5 rounded-lg bg-white dark:bg-[#121215] border border-neutral-200/70 dark:border-neutral-800">
                            <div className="text-[10px] font-medium text-neutral-400 uppercase tracking-wider">
                              Step 2 • Card Rail
                            </div>
                            <div className="mt-1 flex items-baseline justify-between">
                              <span className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 truncate pr-2">
                                {activeProduct.smartStack.cardTitle}
                              </span>
                              <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400 flex-shrink-0">
                                -₹
                                {activeProduct.smartStack.cardSavings.toLocaleString()}
                              </span>
                            </div>
                            <div className="text-[11px] text-neutral-500 mt-1">
                              {activeProduct.smartStack.cardType} payment method
                            </div>
                          </div>

                          <div className="p-3.5 rounded-lg bg-white dark:bg-[#121215] border border-neutral-200/70 dark:border-neutral-800">
                            <div className="text-[10px] font-medium text-neutral-400 uppercase tracking-wider">
                              Step 3 • Net Checkout
                            </div>
                            <div className="mt-1 flex items-baseline justify-between">
                              <span className="text-xs font-semibold text-neutral-900 dark:text-neutral-100">
                                Pay at Store
                              </span>
                              <span className="font-mono text-sm font-bold text-neutral-950 dark:text-white">
                                ₹
                                {activeProduct.smartStack.finalStackedPrice.toLocaleString()}
                              </span>
                            </div>
                            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium mt-1">
                              Instant net savings
                            </div>
                          </div>
                        </div>

                        {/* Execution Steps */}
                        {activeProduct.smartStack.executionSteps &&
                          activeProduct.smartStack.executionSteps.length >
                            0 && (
                            <div className="pt-2 border-t border-neutral-200/60 dark:border-neutral-800/60 space-y-1.5">
                              <div className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 mb-1 flex items-center gap-1.5">
                                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                                <span>
                                  Execution Steps (Follow at Checkout):
                                </span>
                              </div>
                              {activeProduct.smartStack.executionSteps.map(
                                (step, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-start gap-2 text-xs text-neutral-600 dark:text-neutral-400"
                                  >
                                    <span className="h-4 w-4 rounded-full bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 flex items-center justify-center text-[10px] font-mono font-bold flex-shrink-0 mt-0.5">
                                      {idx + 1}
                                    </span>
                                    <span>{step}</span>
                                  </div>
                                ),
                              )}
                            </div>
                          )}
                      </div>
                    )}

                  {/* Coupons & Marketplace Bank Offers */}
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                      <div>
                        <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
                          <Tag className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                          <span>Store Coupons & Bank Discounts</span>
                        </h3>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">
                          Live validated promo codes, bank card checkout
                          discounts, and prepaid savings.
                        </p>
                      </div>
                      {activeProduct.coupons &&
                        activeProduct.coupons.length > 0 && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 self-start sm:self-auto">
                            {activeProduct.coupons.length} Available
                          </span>
                        )}
                    </div>

                    {activeProduct.coupons &&
                    activeProduct.coupons.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {activeProduct.coupons.map((c) => {
                          const isBank = c.source
                            .toLowerCase()
                            .includes("bank");
                          const isPrepaid =
                            c.source.toLowerCase().includes("prepaid") ||
                            c.source.toLowerCase().includes("upi");
                          return (
                            <div
                              key={c.code}
                              className="p-3.5 rounded-xl border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#121215] flex flex-col justify-between gap-3 hover:border-neutral-300 dark:hover:border-neutral-700 transition-all shadow-xs"
                            >
                              <div>
                                <div className="flex items-center justify-between gap-2">
                                  {isBank ? (
                                    <span className="font-mono text-xs font-semibold text-blue-800 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/60 border border-blue-200/80 dark:border-blue-900/60 px-2.5 py-1 rounded-md">
                                      Bank Card Offer
                                    </span>
                                  ) : (
                                    <span className="font-mono text-xs font-bold text-neutral-900 dark:text-neutral-100 bg-neutral-100 dark:bg-neutral-800 px-2.5 py-1 rounded-md tracking-wider">
                                      {c.code}
                                    </span>
                                  )}
                                  <span
                                    className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                                      isBank
                                        ? "bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300"
                                        : isPrepaid
                                          ? "bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300"
                                          : "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                                    }`}
                                  >
                                    {c.source}
                                  </span>
                                </div>
                                <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-2 leading-relaxed">
                                  {c.discountText}
                                </p>
                              </div>

                              <div className="flex items-center justify-between pt-2 border-t border-neutral-100 dark:border-neutral-800/80">
                                <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                                  Save ₹
                                  {Math.round(
                                    c.discountAmount,
                                  ).toLocaleString()}
                                </span>
                                {isBank ? (
                                  <span className="text-[11px] font-medium text-blue-600 dark:text-blue-400">
                                    Auto-applies at checkout
                                  </span>
                                ) : (
                                  <button
                                    onClick={() => copyCode(c.code)}
                                    className="px-3 py-1 text-xs font-medium rounded-lg bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 transition-colors cursor-pointer flex-shrink-0 shadow-xs"
                                  >
                                    {copiedCode === c.code
                                      ? "Copied!"
                                      : "Copy Code"}
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-xs text-neutral-500 bg-neutral-50 dark:bg-neutral-900/40 rounded-xl border border-dashed border-neutral-200 dark:border-neutral-800">
                        No active sitewide promo codes verified for this listing
                        right now.
                      </div>
                    )}
                  </div>

                  {/* Payment Options */}
                  <div className="border-t border-neutral-100 dark:border-neutral-800/80 pt-6">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
                        <CreditCard className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>Your Synced Cards & Payment Rails</span>
                      </h3>
                      <span className="text-[10px] text-neutral-400 dark:text-neutral-500">
                        Portfolio Connected
                      </span>
                    </div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-3">
                      Calculated dynamically across your HSBC, SBI Black, ICICI,
                      Tata Neu, and UPI accounts.
                    </p>
                    <div className="space-y-2.5">
                      {activeProduct.paymentOptions.map((opt, i) => (
                        <div
                          key={i}
                          className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all ${
                            opt.isRecommended
                              ? "bg-emerald-50/20 dark:bg-emerald-950/20 border-emerald-300 dark:border-emerald-800/80 shadow-xs"
                              : "border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#121215]"
                          }`}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-semibold text-neutral-900 dark:text-neutral-100">
                                {opt.title}
                              </span>
                              {opt.isRecommended && (
                                <span className="text-[10px] px-2 py-0.2 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 font-mono font-bold border border-emerald-200 dark:border-emerald-800">
                                  BEST SAVINGS
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 leading-relaxed">
                              {opt.explanation}
                            </p>
                          </div>
                          <div className="text-right font-mono flex-shrink-0 self-end sm:self-auto">
                            <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100 block">
                              ₹{opt.finalPrice.toLocaleString()}
                            </span>
                            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                              Save ₹{opt.effectiveSavings}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        ) : (
          /* Clean Empty Home State when no search is active */
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="rounded-2xl p-10 sm:p-12 border border-neutral-200/90 dark:border-neutral-800 bg-white dark:bg-[#121215] text-center flex flex-col items-center justify-center gap-4 my-2 shadow-xs"
          >
            <div className="h-12 w-12 rounded-xl bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 flex items-center justify-center">
              <Search className="h-5 w-5" />
            </div>
            <div className="max-w-md">
              <h3 className="text-base font-semibold text-neutral-950 dark:text-neutral-50 tracking-tight">
                Live Retail Price Intelligence
              </h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                Paste any live URL from Amazon India, Westside, Max Fashion,
                Myntra, or Flipkart into the search box above to inspect
                authentic prices, stackable coupons, and payment savings.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 mt-2 flex-wrap justify-center">
              <span className="text-[11px] text-neutral-400">Quick test:</span>
              <button
                onClick={() => {
                  const url =
                    "https://www.maxfashion.in/in/en/SHOP-Max-Beige-Men-Patterned-T-shirt-For-Men/p/1000016778440";
                  setSearchQuery(url);
                  executeQuery(url);
                }}
                className="px-3 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-xs font-medium cursor-pointer transition-colors"
              >
                Max Fashion T-Shirt (₹599)
              </button>
              <button
                onClick={() => {
                  const url =
                    "https://www.westside.com/products/nuoflexx-light-taupe-cargo-style-relaxed-fit-mid-rise-track-pants-301086458?Color=Beige&Size=30";
                  setSearchQuery(url);
                  executeQuery(url);
                }}
                className="px-3 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-xs font-medium cursor-pointer transition-colors"
              >
                Westside Track Pants (₹1,699)
              </button>
            </div>
          </motion.div>
        )}

        {/* TAB 4: Technical Specifications & Full Details */}
        {activeProduct && activeTab === "specs" && (
          <motion.div
            key="specs"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="rounded-2xl p-6 sm:p-7 bg-white dark:bg-[#121215] border border-neutral-200/90 dark:border-neutral-800 flex flex-col gap-6 shadow-xs"
          >
            <div>
              <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100 mb-0.5">
                Product Specifications
              </h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">
                Direct verified technical attributes extracted from{" "}
                {activeProduct.store}.
              </p>
            </div>

            {/* Specifications Table */}
            {activeProduct.specifications &&
            Object.keys(activeProduct.specifications).length > 0 ? (
              <div className="overflow-hidden rounded-xl border border-neutral-200/80 dark:border-neutral-800">
                <table className="w-full text-left text-xs">
                  <tbody className="divide-y divide-neutral-200/80 dark:divide-neutral-800">
                    {Object.entries(activeProduct.specifications).map(
                      ([key, val], idx) => (
                        <tr
                          key={idx}
                          className={
                            idx % 2 === 0
                              ? "bg-white dark:bg-[#121215]"
                              : "bg-neutral-50/60 dark:bg-neutral-900/30"
                          }
                        >
                          <td className="py-2.5 px-4 font-medium text-neutral-500 dark:text-neutral-400 w-1/3 border-r border-neutral-200/80 dark:border-neutral-800">
                            {key}
                          </td>
                          <td className="py-2.5 px-4 text-neutral-900 dark:text-neutral-100 break-words font-mono">
                            {val}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-neutral-500 border border-dashed rounded-xl border-neutral-200 dark:border-neutral-800">
                Specifications available in store leaflet. Inspect live listing
                for complete details.
              </div>
            )}
          </motion.div>
        )}

        {/* 5. Trending Deals Section */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 uppercase tracking-wider">
              <Flame className="h-3.5 w-3.5 text-amber-500" />
              <span>Verified Price Drops</span>
            </h3>
            <Link
              href="/deals"
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 flex items-center gap-1 transition-colors"
            >
              <span>View All Drops ({trendingDeals.length})</span>
              <span>→</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {trendingDeals.map((deal) => (
              <div
                key={deal.id}
                onClick={() => {
                  if (deal.title) {
                    setSearchQuery(deal.title);
                    executeQuery(deal.title);
                  } else if (deal.id) {
                    selectProduct(deal.id);
                  }
                }}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex gap-3.5 items-center bg-white dark:bg-[#121215] shadow-xs hover:border-neutral-300 dark:hover:border-neutral-700 ${
                  activeProductId === deal.id && !liveResolvedProduct
                    ? "border-emerald-500 ring-1 ring-emerald-500/30"
                    : "border-neutral-200/80 dark:border-neutral-800"
                }`}
              >
                <img
                  src={deal.image}
                  alt={deal.title}
                  className="h-13 w-13 rounded-lg object-contain bg-neutral-50 dark:bg-neutral-900 flex-shrink-0 p-1 border border-neutral-200/60 dark:border-neutral-800"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between text-xs text-neutral-400">
                    <span className="text-[11px] font-medium">
                      {deal.store}
                    </span>
                    <span className="px-1.5 py-0.2 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 text-[10px] font-mono font-bold">
                      {deal.badge}
                    </span>
                  </div>
                  <h4 className="text-xs font-medium text-neutral-900 dark:text-neutral-100 truncate mt-0.5">
                    {deal.title}
                  </h4>
                  <div className="flex items-baseline gap-2 mt-0.5 font-mono">
                    <span className="text-xs font-bold text-neutral-900 dark:text-neutral-100">
                      ₹{deal.dealPrice.toLocaleString()}
                    </span>
                    <span className="text-[10px] line-through text-neutral-400">
                      ₹{deal.regularPrice.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* 6. Sliding Cart Drawer (Framer Motion) */}
      <AnimatePresence>
        {cartOpen && (
          <div className="fixed inset-0 z-50 flex justify-end">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setCartOpen(false)}
              className="fixed inset-0 bg-neutral-950/40 backdrop-blur-xs"
            />

            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 220 }}
              className="relative w-full max-w-md bg-white dark:bg-[#121215] h-full shadow-2xl flex flex-col z-10 border-l border-neutral-200 dark:border-neutral-800"
            >
              {/* Drawer Header */}
              <div className="p-5 border-b border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShoppingCart className="h-4.5 w-4.5 text-neutral-900 dark:text-neutral-100" />
                  <h3 className="font-semibold text-base text-neutral-900 dark:text-neutral-100">
                    Your OmniCart
                  </h3>
                  <span className="font-mono text-xs px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 font-semibold">
                    {cartItems.reduce((a, b) => a + b.quantity, 0)} items
                  </span>
                </div>
                <button
                  onClick={() => setCartOpen(false)}
                  className="p-1 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Drawer Items */}
              <div className="flex-1 overflow-y-auto p-5 space-y-3">
                {cartItems.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center text-neutral-400 p-6">
                    <ShoppingBag className="h-10 w-10 stroke-[1.5] text-neutral-300 dark:text-neutral-700 mb-3" />
                    <p className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
                      Your OmniCart is empty
                    </p>
                    <p className="text-xs mt-1">
                      Add items to view cross-store deal stacking.
                    </p>
                  </div>
                ) : (
                  cartItems.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-neutral-900/50 flex gap-3 items-center relative shadow-xs"
                    >
                      <img
                        src={item.image}
                        alt={item.title}
                        className="h-14 w-14 rounded-lg object-contain bg-white dark:bg-neutral-950 border border-neutral-200/60 dark:border-neutral-800 p-1 flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0 pr-6">
                        <div className="text-[10px] text-neutral-400 uppercase font-medium">
                          {item.store}
                        </div>
                        <h4 className="font-medium text-xs text-neutral-900 dark:text-neutral-100 truncate">
                          {item.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-1 font-mono">
                          <span className="text-xs font-bold text-neutral-900 dark:text-neutral-100">
                            ₹{item.price.toLocaleString()}
                          </span>
                          <span className="text-[10px] line-through text-neutral-400">
                            ₹{item.regularPrice.toLocaleString()}
                          </span>
                          <span className="text-[10px] text-neutral-500">
                            Qty: {item.quantity}
                          </span>
                        </div>
                        <div className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5">
                          {item.deliveryDays}
                        </div>
                      </div>
                      <button
                        onClick={() => removeFromCart(item.id)}
                        className="absolute top-2.5 right-2.5 text-neutral-400 hover:text-rose-600 transition-colors cursor-pointer"
                        title="Remove item"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>

              {/* Drawer Footer Checkout Summary */}
              {cartItems.length > 0 && (
                <div className="p-5 border-t border-neutral-200/80 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-900/50 space-y-3">
                  <div className="space-y-1.5 text-xs font-mono">
                    <div className="flex justify-between text-neutral-500">
                      <span>Subtotal (M.R.P):</span>
                      <span>₹{cartRegularTotal.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-bold">
                      <span>Total Savings:</span>
                      <span>-₹{totalCartSavings.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-neutral-900 dark:text-neutral-100 font-bold text-sm pt-2 border-t border-neutral-200/80 dark:border-neutral-800">
                      <span>Final Net Checkout:</span>
                      <span>₹{cartTotal.toLocaleString()}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setCartOpen(false);
                      executeAutoSnipe();
                    }}
                    className="w-full py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white font-medium text-xs rounded-xl flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs"
                  >
                    <Zap className="h-3.5 w-3.5 fill-white" />
                    <span>1-Click Checkout</span>
                  </button>
                  <p className="text-[10px] text-center text-neutral-400">
                    Payment credentials stored strictly on-device
                  </p>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Checkout Modal */}
      <AnimatePresence>
        {orderModalOpen && (
          <div className="fixed inset-0 bg-neutral-950/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              className="bg-white dark:bg-[#121215] border border-neutral-200 dark:border-neutral-800 rounded-2xl max-w-sm w-full p-6 text-center shadow-2xl"
            >
              <div className="h-11 w-11 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200/80 dark:border-emerald-800 mx-auto flex items-center justify-center mb-3">
                <Check className="h-5 w-5 stroke-[2.5]" />
              </div>
              <h3 className="font-semibold text-base text-neutral-900 dark:text-neutral-100 mb-1">
                Order Prepared
              </h3>
              {activeProduct && (
                <>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-4 leading-relaxed">
                    Ready to checkout for{" "}
                    <strong className="text-neutral-800 dark:text-neutral-200">
                      {activeProduct.title}
                    </strong>{" "}
                    on{" "}
                    <strong className="text-neutral-800 dark:text-neutral-200">
                      {activeProduct.store}
                    </strong>{" "}
                    delivering to{" "}
                    <strong className="text-neutral-800 dark:text-neutral-200">
                      {userPincode}
                    </strong>
                    .
                  </p>
                  <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200/80 dark:border-neutral-800 text-left text-xs mb-5 font-mono space-y-1.5">
                    <div className="flex justify-between text-neutral-900 dark:text-neutral-100">
                      <span>Final Net Price:</span>
                      <strong>
                        ₹{activeProduct.livePrice.toLocaleString()}
                      </strong>
                    </div>
                    <div className="flex justify-between text-emerald-600 dark:text-emerald-400">
                      <span>Total Savings:</span>
                      <strong>
                        ₹
                        {(
                          activeProduct.regularPrice - activeProduct.livePrice
                        ).toLocaleString()}
                      </strong>
                    </div>
                    <div className="flex justify-between text-neutral-400 text-[11px]">
                      <span>Method:</span>
                      <span>On-Device 1-Click Vault</span>
                    </div>
                  </div>
                </>
              )}
              <button
                onClick={() => setOrderModalOpen(false)}
                className="w-full py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 font-medium text-xs rounded-xl cursor-pointer shadow-xs transition-colors"
              >
                Done
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <footer className="border-t border-neutral-200/80 dark:border-neutral-800 py-6 bg-white dark:bg-[#09090B] text-center text-xs text-neutral-400 font-mono transition-colors duration-200">
        OmniCart • Universal Price Arbitrage & Real-Time Deal Intelligence for
        India
      </footer>
    </div>
  );
}
