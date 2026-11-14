"use client";

import React, { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Search,
  Filter,
  Layers,
  ChevronDown,
  Sparkles,
  Database,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";

const PAGE_TITLES: Record<string, { title: string; category: string }> = {
  "/": { title: "Intelligence Overview", category: "Intelligence" },
  "/discovery": { title: "Player Discovery", category: "Intelligence" },
  "/comparison": { title: "Player Comparison Lab", category: "Intelligence" },
  "/squad-architect": { title: "Squad Architect", category: "Recruitment" },
  "/auction-simulator": { title: "Auction Decision Simulator", category: "Recruitment" },
  "/watchlist": { title: "Scouting Watchlist", category: "Recruitment" },
  "/methodology": { title: "Methodology & Validation Centre", category: "System" },
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [scope, setScope] = useState("IPL_T20I");

  let currentPage = PAGE_TITLES[pathname];
  if (!currentPage && pathname.startsWith("/players/")) {
    currentPage = { title: "Player Intelligence Profile", category: "Intelligence" };
  }
  if (!currentPage) {
    currentPage = { title: "Cricket Scouting Intelligence", category: "SupeRR" };
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/discovery?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 px-8 py-2.5 h-14 flex items-center justify-between">
      {/* Breadcrumb & Current Page Title */}
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xs font-semibold uppercase tracking-wider text-rr-pink bg-pink-50 px-2.5 py-1 rounded-full border border-pink-100 shrink-0">
          {currentPage.category}
        </span>
        <span className="text-slate-300 shrink-0">/</span>
        <h1 className="text-base font-bold text-rr-navy tracking-tight truncate">
          {currentPage.title}
        </h1>
      </div>

      {/* Center / Right Controls */}
      <div className="flex items-center gap-3 lg:gap-4 shrink-0">
        {/* Global Player Search */}
        <form onSubmit={handleSearchSubmit} className="relative shrink">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search player or squad..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-4 py-1.5 w-44 sm:w-52 lg:w-60 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rr-pink focus:bg-white transition-all"
          />
        </form>

        {/* Competition Scope Selector */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-rr-navy shadow-xs shrink-0 whitespace-nowrap">
          <Database className="w-3.5 h-3.5 text-rr-pink shrink-0" />
          <span className="text-slate-500 font-medium shrink-0">Scope:</span>
          <div className="relative inline-flex items-center">
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="appearance-none [appearance:none] [-webkit-appearance:none] [-moz-appearance:none] bg-transparent pl-1 pr-5 py-0.5 text-xs font-bold text-rr-navy focus:outline-none cursor-pointer leading-normal whitespace-nowrap"
            >
              <option value="IPL_T20I">Main Competitions (IPL & T20I)</option>
              <option value="ALL">All Competitions (Inc. Emerging)</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none shrink-0" />
          </div>
        </div>

        {/* Verified Data Snapshot Date Indicator */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200 shrink-0">
          <div
            title="Precomputed analytics snapshot covering 853 elite T20 matches (IPL 2022–2026 & Official T20Is). Deployed via Cloudflare edge delivery without live server dependencies."
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-[11px] font-semibold text-slate-700 whitespace-nowrap cursor-help hover:bg-pink-50 hover:border-pink-200 hover:text-rr-pink transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-rr-pink" />
            <span>Data Snapshot: 15 Nov 2026</span>
          </div>
        </div>
      </div>
    </header>
  );
}
