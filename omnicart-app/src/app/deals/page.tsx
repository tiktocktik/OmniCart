"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import {
  Flame,
  ArrowLeft,
  RefreshCw,
  Search,
  ExternalLink,
  ShieldCheck,
  TrendingDown,
  Tag,
  Store,
  SlidersHorizontal,
  Sun,
  Moon,
  Sparkles,
  Layers,
  MapPin,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface LiveDeal {
  id: string;
  title: string;
  store: string;
  dealPrice: number;
  regularPrice: number;
  savings?: number;
  discount: number;
  category?: string;
  timeAgo: string;
  image: string;
  badge: string;
  isMegaDrop?: boolean;
  isGlitch?: boolean;
  urgencyLevel?: "EXTREME" | "HIGH" | "NORMAL";
  heatScore?: number;
  url: string;
  source: string;
}

export default function DealsPage() {
  const router = useRouter();
  const [deals, setDeals] = useState<LiveDeal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [userPincode, setUserPincode] = useState<string>("110001");
  const [userCity, setUserCity] = useState<string>("Delhi (NCR)");

  // Filters & Sorting
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedStore, setSelectedStore] = useState<string>("All");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [onlyCrazyDrops, setOnlyCrazyDrops] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<
    "discount" | "price_asc" | "price_desc" | "savings"
  >("discount");

  const fetchDealsData = async (forceRefresh: boolean = false) => {
    if (forceRefresh) setRefreshing(true);
    else setLoading(true);
    setLoadError(null);

    try {
      const url = `${API_BASE}/deals?limit=50${forceRefresh ? "&refresh=true" : ""}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setDeals(data);
        }
      } else {
        setLoadError(
          `The deals service returned HTTP ${res.status}. Try refreshing.`,
        );
      }
    } catch {
      setLoadError(
        `Could not reach the OmniCart backend at ${API_BASE}. Start the backend and retry.`,
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    // 1. Initial deals load
    fetchDealsData(false);

    // 2. Read theme
    const savedTheme = localStorage.getItem("omnicart_theme") as
      "light" | "dark" | null;
    if (savedTheme) {
      setTheme(savedTheme);
      if (savedTheme === "dark") document.documentElement.classList.add("dark");
      else document.documentElement.classList.remove("dark");
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
      document.documentElement.classList.add("dark");
    }

    // 3. Read location
    const pin = localStorage.getItem("omnicart_pincode");
    const city = localStorage.getItem("omnicart_city");
    if (pin) setUserPincode(pin);
    if (city) setUserCity(city);
  }, []);

  const toggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    localStorage.setItem("omnicart_theme", next);
    if (next === "dark") document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  };

  // Unique stores & categories
  const stores = useMemo(() => {
    const list = Array.from(new Set(deals.map((d) => d.store).filter(Boolean)));
    return ["All", ...list];
  }, [deals]);

  const categories = useMemo(() => {
    const list = Array.from(
      new Set(deals.map((d) => d.category || "General Goods").filter(Boolean)),
    );
    return ["All", ...list];
  }, [deals]);

  // Filtered & sorted deals
  const filteredDeals = useMemo(() => {
    let result = deals.filter((deal) => {
      const matchesSearch =
        !searchQuery.trim() ||
        deal.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        deal.store.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (deal.category &&
          deal.category.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStore =
        selectedStore === "All" ||
        deal.store.toLowerCase() === selectedStore.toLowerCase();
      const matchesCategory =
        selectedCategory === "All" ||
        (deal.category || "General Goods") === selectedCategory;
      const matchesCrazy = !onlyCrazyDrops || deal.isMegaDrop || deal.isGlitch;

      return matchesSearch && matchesStore && matchesCategory && matchesCrazy;
    });

    if (sortBy === "discount") {
      result.sort((a, b) => b.discount - a.discount);
    } else if (sortBy === "price_asc") {
      result.sort((a, b) => a.dealPrice - b.dealPrice);
    } else if (sortBy === "price_desc") {
      result.sort((a, b) => b.dealPrice - a.dealPrice);
    } else if (sortBy === "savings") {
      result.sort(
        (a, b) =>
          (b.savings || b.regularPrice - b.dealPrice) -
          (a.savings || a.regularPrice - a.dealPrice),
      );
    }

    return result;
  }, [deals, searchQuery, selectedStore, selectedCategory, sortBy]);

  const handleInspectDeal = (deal: LiveDeal) => {
    // Deal URLs point at aggregator posts, not store listings. Search the
    // product title so the inspector returns live Amazon/Flipkart candidates.
    const target = deal.title || deal.url;
    router.push(`/?q=${encodeURIComponent(target)}`);
  };

  return (
    <div className="min-h-screen flex flex-col font-sans bg-neutral-50 dark:bg-[#0B0B0E] text-neutral-900 dark:text-neutral-100 selection:bg-emerald-500/20 selection:text-emerald-900 dark:selection:bg-emerald-500/30 dark:selection:text-emerald-200 antialiased transition-colors duration-200">
      {/* 1. Header Bar */}
      <header className="sticky top-0 z-40 w-full border-b border-neutral-200/80 dark:border-neutral-800 bg-white/80 dark:bg-[#0B0B0E]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Inspector</span>
            </Link>

            <Link href="/" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-neutral-900 dark:bg-white flex items-center justify-center font-bold text-white dark:text-neutral-950 font-mono text-sm shadow-xs">
                Ω
              </div>
              <div>
                <span className="font-bold tracking-tight text-base flex items-center gap-1.5">
                  OmniCart
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300 font-semibold uppercase tracking-wider">
                    Deals
                  </span>
                </span>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-100/60 dark:bg-neutral-900/60 text-neutral-600 dark:text-neutral-300 font-mono">
              <MapPin className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>
                {userCity} ({userPincode})
              </span>
            </div>

            <button
              onClick={() => fetchDealsData(true)}
              disabled={refreshing}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 transition-all cursor-pointer shadow-xs disabled:opacity-50"
              title="Force scrape fresh deals"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-emerald-500" : ""}`}
              />
              <span className="hidden sm:inline">
                {refreshing ? "Refreshing..." : "Refresh Feed"}
              </span>
            </button>

            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-300 transition-colors cursor-pointer"
            >
              {theme === "light" ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Sun className="h-4 w-4 text-amber-400" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* 2. Page Hero & Telemetry Banner */}
      <section className="border-b border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#101014] py-8 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/80 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-300 text-xs font-mono font-medium mb-3">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Deal Aggregation • 10-Minute Cache</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
                Indian Marketplace Price Drops
              </h1>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1.5 max-w-2xl">
                Crowdsourced price drops from public Indian deal aggregators.
                Prices and availability change quickly; confirm on the store
                before buying.
              </p>
            </div>

            {/* Source Telemetry Pill Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#141418]">
                <div className="text-[10px] text-neutral-400 uppercase font-semibold">
                  Loaded Drops
                </div>
                <div className="text-base font-bold text-neutral-900 dark:text-neutral-100 mt-0.5">
                  {deals.length} Cached
                </div>
              </div>
              <div className="p-2.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#141418]">
                <div className="text-[10px] text-neutral-400 uppercase font-semibold">
                  Primary Feed
                </div>
                <div className="text-xs font-bold text-neutral-900 dark:text-neutral-100 mt-1 truncate">
                  DesiDime Community
                </div>
              </div>
              <div className="p-2.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#141418]">
                <div className="text-[10px] text-neutral-400 uppercase font-semibold">
                  Lightning Feed
                </div>
                <div className="text-xs font-bold text-neutral-900 dark:text-neutral-100 mt-1 truncate">
                  Dealsmagnet Drops
                </div>
              </div>
              <div className="p-2.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#141418]">
                <div className="text-[10px] text-neutral-400 uppercase font-semibold">
                  Cache TTL
                </div>
                <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  10m In-Memory
                </div>
              </div>
            </div>
          </div>

          {/* 3. Search & Filter Bar */}
          <div className="mt-6 pt-6 border-t border-neutral-200/60 dark:border-neutral-800/60 flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
              {/* Search input */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter by product name, brand, or store..."
                  className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-[#121216] focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-neutral-900 dark:text-neutral-100 placeholder-neutral-400"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
                  >
                    Clear
                  </button>
                )}
              </div>

              {/* Sort by dropdown & Crazy Drops toggle */}
              <div className="flex flex-wrap items-center gap-2 text-xs font-medium self-end sm:self-auto">
                <button
                  onClick={() => setOnlyCrazyDrops((prev) => !prev)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer border ${
                    onlyCrazyDrops
                      ? "bg-amber-500 text-neutral-950 border-amber-400 shadow-sm ring-2 ring-amber-500/30 font-bold"
                      : "bg-white dark:bg-[#121216] text-neutral-700 dark:text-neutral-300 border-neutral-200 dark:border-neutral-700 hover:border-amber-500/50"
                  }`}
                >
                  <Flame
                    className={`h-3.5 w-3.5 ${onlyCrazyDrops ? "fill-neutral-950 text-neutral-950" : "text-amber-500"}`}
                  />
                  <span>Crazy Drops Only</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                      onlyCrazyDrops
                        ? "bg-neutral-950 text-amber-400 font-bold"
                        : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400"
                    }`}
                  >
                    {deals.filter((d) => d.isMegaDrop || d.isGlitch).length}
                  </span>
                </button>

                <div className="flex items-center gap-1.5 text-neutral-400 ml-1">
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                  <span>Sort:</span>
                </div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="px-3 py-1.5 rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-[#121216] text-neutral-900 dark:text-neutral-100 text-xs focus:outline-none focus:border-emerald-500 cursor-pointer font-mono"
                >
                  <option value="discount">Highest Discount %</option>
                  <option value="savings">Max Savings (₹)</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                </select>
              </div>
            </div>

            {/* Filter Pills: Stores & Categories */}
            <div className="flex flex-col gap-2.5">
              {/* Store pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                <span className="text-[11px] font-semibold uppercase text-neutral-400 font-mono mr-1 flex items-center gap-1">
                  <Store className="h-3 w-3" />
                  Source / Store:
                </span>
                {stores.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSelectedStore(s)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer border ${
                      selectedStore.toLowerCase() === s.toLowerCase()
                        ? "bg-neutral-900 text-white dark:bg-white dark:text-neutral-950 border-transparent shadow-xs"
                        : "bg-white dark:bg-[#141418] text-neutral-600 dark:text-neutral-400 border-neutral-200/80 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>

              {/* Category pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                <span className="text-[11px] font-semibold uppercase text-neutral-400 font-mono mr-1 flex items-center gap-1">
                  <Tag className="h-3 w-3" />
                  Category:
                </span>
                {categories.map((c) => (
                  <button
                    key={c}
                    onClick={() => setSelectedCategory(c)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer border ${
                      selectedCategory === c
                        ? "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-neutral-950 border-transparent shadow-xs"
                        : "bg-white dark:bg-[#141418] text-neutral-600 dark:text-neutral-400 border-neutral-200/80 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Deals Grid Section */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-8">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs text-neutral-500 dark:text-neutral-400 font-mono">
            Showing{" "}
            <strong className="text-neutral-900 dark:text-neutral-100">
              {filteredDeals.length}
            </strong>{" "}
            deals
            {selectedStore !== "All" && ` in ${selectedStore}`}
            {selectedCategory !== "All" && ` • ${selectedCategory}`}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="p-4 rounded-2xl border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#121216] animate-pulse h-80"
              />
            ))}
          </div>
        ) : loadError ? (
          <div className="py-20 text-center flex flex-col items-center justify-center border border-dashed border-red-300 dark:border-red-900/60 rounded-3xl bg-red-50/50 dark:bg-red-950/10">
            <div className="h-12 w-12 rounded-2xl bg-red-100 dark:bg-red-900/40 flex items-center justify-center text-red-600 dark:text-red-300 mb-3">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
              Could not load deals
            </h3>
            <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1 max-w-sm">
              {loadError}
            </p>
            <button
              onClick={() => fetchDealsData(true)}
              className="mt-4 px-4 py-2 text-xs font-semibold rounded-xl bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 transition-colors shadow-xs cursor-pointer"
            >
              Retry
            </button>
          </div>
        ) : filteredDeals.length === 0 ? (
          <div className="py-20 text-center flex flex-col items-center justify-center border border-dashed border-neutral-300 dark:border-neutral-800 rounded-3xl bg-white/50 dark:bg-[#101014]/50">
            <div className="h-12 w-12 rounded-2xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-400 mb-3">
              <Search className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
              No deals match your filters
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 max-w-sm">
              Try adjusting your search keywords, switching categories, or
              clearing store filters.
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedStore("All");
                setSelectedCategory("All");
              }}
              className="mt-4 px-4 py-2 text-xs font-semibold rounded-xl bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 text-white dark:text-neutral-950 transition-colors shadow-xs cursor-pointer"
            >
              Reset All Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredDeals.map((deal) => {
              const savingsAmount =
                deal.savings || Math.max(0, deal.regularPrice - deal.dealPrice);

              return (
                <div
                  key={deal.id}
                  className={`group rounded-2xl border bg-white dark:bg-[#121216] hover:shadow-lg transition-all duration-200 flex flex-col overflow-hidden relative ${
                    deal.isGlitch
                      ? "border-amber-400 dark:border-amber-500/80 ring-1 ring-amber-500/30"
                      : "border-neutral-200/80 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700"
                  }`}
                >
                  {/* Top Badges */}
                  <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between pointer-events-none">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold shadow-xs ${
                          deal.isGlitch
                            ? "bg-amber-500 text-neutral-950"
                            : "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-neutral-950"
                        }`}
                      >
                        {deal.badge}
                      </span>
                      {deal.heatScore && deal.heatScore > 0 ? (
                        <span className="px-1.5 py-0.5 rounded-full bg-rose-500/90 text-white text-[9px] font-mono font-bold flex items-center gap-0.5 shadow-xs">
                          <Flame className="h-2.5 w-2.5 fill-white" />
                          {deal.heatScore}°
                        </span>
                      ) : null}
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-neutral-900/80 dark:bg-black/80 backdrop-blur-xs text-white text-[10px] font-mono">
                      {deal.store}
                    </span>
                  </div>

                  {/* Product Image */}
                  <div
                    onClick={() => handleInspectDeal(deal)}
                    className="w-full h-48 p-5 bg-neutral-50 dark:bg-[#16161B] flex items-center justify-center cursor-pointer border-b border-neutral-100 dark:border-neutral-800/80 overflow-hidden"
                  >
                    <img
                      src={deal.image}
                      alt={deal.title}
                      loading="lazy"
                      className="max-h-full max-w-full object-contain group-hover:scale-105 transition-transform duration-200"
                    />
                  </div>

                  {/* Card Content */}
                  <div className="p-4 flex-1 flex flex-col justify-between">
                    <div>
                      {/* Category & Source */}
                      <div className="flex items-center justify-between text-[11px] text-neutral-400 font-mono mb-1.5">
                        <span className="truncate max-w-[140px]">
                          {deal.category || "General Goods"}
                        </span>
                        {deal.timeAgo && (
                          <span className="text-[10px]">{deal.timeAgo}</span>
                        )}
                      </div>

                      {/* Title */}
                      <h3
                        onClick={() => handleInspectDeal(deal)}
                        className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 line-clamp-2 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors cursor-pointer"
                        title={deal.title}
                      >
                        {deal.title}
                      </h3>
                    </div>

                    {/* Pricing */}
                    <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800/60 mt-3">
                      <div className="flex items-baseline gap-2 font-mono">
                        <span className="text-base font-extrabold text-neutral-900 dark:text-neutral-100">
                          ₹{deal.dealPrice.toLocaleString("en-IN")}
                        </span>
                        {deal.regularPrice > deal.dealPrice && (
                          <span className="text-xs line-through text-neutral-400">
                            ₹{deal.regularPrice.toLocaleString("en-IN")}
                          </span>
                        )}
                      </div>

                      {savingsAmount > 0 && deal.discount > 0 && (
                        <div className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">
                          Save ₹{savingsAmount.toLocaleString("en-IN")} (
                          {deal.discount}% off)
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="grid grid-cols-2 gap-2 mt-3 pt-2">
                        <button
                          onClick={() => handleInspectDeal(deal)}
                          className="w-full py-2 px-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-neutral-950 font-semibold text-[11px] flex items-center justify-center gap-1 transition-colors cursor-pointer shadow-xs"
                        >
                          <Sparkles className="h-3 w-3" />
                          <span>Stack & Buy</span>
                        </button>

                        <a
                          href={deal.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full py-2 px-2.5 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-200 font-medium text-[11px] flex items-center justify-center gap-1 transition-colors cursor-pointer text-center"
                        >
                          <span>Deal Post</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* 5. Footer */}
      <footer className="border-t border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-[#0E0E12] py-6 px-4 text-center text-xs text-neutral-500 dark:text-neutral-400 font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>
              OmniCart Deal Aggregator • Community Price Tracking
            </span>
          </div>
          <div>
            <span>
              Cached for 10 minutes from public Indian deal aggregators.
              Confirm on the store.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
