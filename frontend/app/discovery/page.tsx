"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import {
  formatCurrency,
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import {
  Search,
  Filter,
  ArrowUpDown,
  GitCompare,
  TrendingUp,
  BookmarkPlus,
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  Info,
  Flame,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Target,
  AlertTriangle,
  HelpCircle,
  Award,
} from "lucide-react";

function formatEvidenceStatus(status: string) {
  if (status === "Ranked Pressure Performer" || status === "Emerging Pressure Performer") {
    return {
      label: status,
      badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-200",
      icon: Award,
    };
  }
  if (status?.includes("Limited Evidence")) {
    return {
      label: status,
      badgeClass: "bg-amber-50 text-amber-800 border-amber-200",
      icon: Target,
    };
  }
  if (status?.includes("Below Baseline")) {
    return {
      label: status,
      badgeClass: "bg-rose-50 text-rose-800 border-rose-200",
      icon: ShieldAlert,
    };
  }
  return {
    label: status || "Insufficient Evidence",
    badgeClass: "bg-slate-50 text-slate-600 border-slate-200",
    icon: HelpCircle,
  };
}

function DiscoveryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get("search") || "";
  const initialDiscipline = searchParams.get("discipline") || "";
  const tabParam = searchParams.get("tab");
  const initialTab =
    tabParam === "pressure-bowlers" || tabParam === "bowling"
      ? "PRESSURE_BOWLING"
      : tabParam === "pressure" || tabParam === "batting"
      ? "PRESSURE"
      : "DISCIPLINE";

  // Navigation tab
  const [activeTab, setActiveTab] = useState<"DISCIPLINE" | "PRESSURE" | "PRESSURE_BOWLING">(initialTab);

  // Discipline Ratings state
  const [players, setPlayers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [loading, setLoading] = useState(true);
  const [role, setRole] = useState("");
  const [search, setSearch] = useState(initialSearch);
  const [sortBy, setSortBy] = useState(
    initialDiscipline === "bowling" ? "overall_bowling_rating" : "overall_batting_rating"
  );
  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);
  const [addedNote, setAddedNote] = useState<number | null>(null);

  // Pressure Performers (Batting) state
  const [pressureScope, setPressureScope] = useState<"IPL_T20I" | "IPL" | "T20I" | "EMERGING">("IPL_T20I");
  const [pressureContext, setPressureContext] = useState<"ALL" | "CHASE" | "FIRST_INNINGS">("ALL");
  const [pressureSearch, setPressureSearch] = useState("");
  const [pressureSortBy, setPressureSortBy] = useState<string>("pressure_rank");
  const [pressureSortDir, setPressureSortDir] = useState<"asc" | "desc">("asc");
  const [pressurePerformers, setPressurePerformers] = useState<any[]>([]);
  const [pressureSummary, setPressureSummary] = useState<any>(null);
  const [pressureLoading, setPressureLoading] = useState(false);

  // Bowling Under Pressure state
  const [bowlerScope, setBowlerScope] = useState<"IPL_T20I" | "IPL" | "T20I" | "EMERGING">("IPL_T20I");
  const [bowlerPaceSpin, setBowlerPaceSpin] = useState<"ALL" | "PACE" | "SPIN">("ALL");
  const [bowlerSearch, setBowlerSearch] = useState("");
  const [bowlerSortBy, setBowlerSortBy] = useState<string>("pressure_rank");
  const [bowlerSortDir, setBowlerSortDir] = useState<"asc" | "desc">("asc");
  const [pressureBowlers, setPressureBowlers] = useState<any[]>([]);
  const [bowlerSummary, setBowlerSummary] = useState<any>(null);
  const [bowlerLoading, setBowlerLoading] = useState(false);

  useEffect(() => {
    if (activeTab === "DISCIPLINE") {
      loadPlayers();
    } else if (activeTab === "PRESSURE") {
      loadPressureData();
    } else if (activeTab === "PRESSURE_BOWLING") {
      loadPressureBowlerData();
    }
  }, [
    activeTab,
    page,
    role,
    sortBy,
    pressureScope,
    pressureContext,
    pressureSortBy,
    pressureSortDir,
    bowlerScope,
    bowlerPaceSpin,
    bowlerSortBy,
    bowlerSortDir,
  ]);

  async function loadPlayers() {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
      };
      if (role) params.role = role;
      if (search) params.search = search;

      const res = await api.getPlayers(params);
      setPlayers(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to load players:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadPressureData() {
    setPressureLoading(true);
    try {
      const [lbRes, discRes] = await Promise.all([
        api.getPressureLeaderboard({
          scope: pressureScope,
          context: pressureContext,
          search: pressureSearch.trim() || undefined,
          sort_by: pressureSortBy,
          sort_dir: pressureSortDir,
          limit: 150,
        }),
        api.getPressureDiscovery(pressureScope),
      ]);
      setPressurePerformers(lbRes.players || []);
      setPressureSummary(discRes);
    } catch (err) {
      console.error("Failed to load pressure intelligence:", err);
    } finally {
      setPressureLoading(false);
    }
  }

  async function loadPressureBowlerData() {
    setBowlerLoading(true);
    try {
      const [lbRes, sumRes] = await Promise.all([
        api.getPressureBowlersLeaderboard({
          scope: bowlerScope,
          pace_spin: bowlerPaceSpin !== "ALL" ? bowlerPaceSpin : undefined,
          search: bowlerSearch.trim() || undefined,
          sort_by: bowlerSortBy,
          sort_dir: bowlerSortDir,
          limit: 150,
        }),
        api.getPressureBowlersSummary(bowlerScope),
      ]);
      setPressureBowlers(lbRes.records || lbRes.bowlers || []);
      setBowlerSummary(sumRes);
    } catch (err) {
      console.error("Failed to load pressure bowling intelligence:", err);
    } finally {
      setBowlerLoading(false);
    }
  }

  function handleBowlerSort(col: string) {
    if (bowlerSortBy === col) {
      setBowlerSortDir(bowlerSortDir === "asc" ? "desc" : "asc");
    } else {
      setBowlerSortBy(col);
      setBowlerSortDir(
        col === "pressure_rank" || col === "player_name" || col === "hp_wae_rank" ? "asc" : "desc"
      );
    }
  }

  function handleBowlerSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadPressureBowlerData();
  }

  function handlePressureSort(col: string) {
    if (pressureSortBy === col) {
      setPressureSortDir(pressureSortDir === "asc" ? "desc" : "asc");
    } else {
      setPressureSortBy(col);
      setPressureSortDir(col === "pressure_rank" || col === "player_name" ? "asc" : "desc");
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    loadPlayers();
  }

  function handlePressureSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadPressureData();
  }

  function toggleCompare(pid: number) {
    if (selectedForCompare.includes(pid)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== pid));
    } else {
      if (selectedForCompare.length >= 4) {
        alert("Maximum 4 players can be compared simultaneously.");
        return;
      }
      setSelectedForCompare([...selectedForCompare, pid]);
    }
  }

  function goToCompare() {
    if (selectedForCompare.length < 2) {
      alert("Please select at least 2 players to compare.");
      return;
    }
    router.push(`/comparison?ids=${selectedForCompare.join(",")}`);
  }

  async function handleQuickWatchlist(pid: number) {
    try {
      const wls = await api.getWatchlists();
      if (wls.length > 0) {
        await api.addWatchlistPlayer(wls[0].watchlist_id, pid, "High", "Scouted Candidate");
        setAddedNote(pid);
        setTimeout(() => setAddedNote(null), 2500);
      }
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-rr-navy">
            Player Talent Discovery
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Identify proven contributors through independent discipline ratings and situational pressure intelligence.
          </p>
        </div>

        {selectedForCompare.length > 0 && activeTab === "DISCIPLINE" && (
          <div className="flex items-center gap-3 p-2 bg-pink-50 rounded-lg border border-pink-200 animate-fadeIn">
            <span className="text-xs text-rr-navy font-bold">
              {selectedForCompare.length} Selected
            </span>
            <button
              onClick={goToCompare}
              className="px-3 py-1.5 rounded-md bg-rr-pink text-white text-xs font-semibold hover:bg-rr-darkpink transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>Compare Players</span>
            </button>
            <button
              onClick={() => setSelectedForCompare([])}
              className="text-xs text-slate-500 hover:text-rr-navy"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("DISCIPLINE")}
          className={`pb-3 px-1 text-xs font-bold transition-all relative flex items-center gap-2 ${
            activeTab === "DISCIPLINE"
              ? "text-rr-pink border-b-2 border-rr-pink"
              : "text-slate-500 hover:text-rr-navy"
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Discipline Ratings & Baselines</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
            1,217 Players
          </span>
        </button>

        <button
          onClick={() => setActiveTab("PRESSURE")}
          className={`pb-3 px-1 text-xs font-bold transition-all relative flex items-center gap-2 ${
            activeTab === "PRESSURE"
              ? "text-rr-pink border-b-2 border-rr-pink"
              : "text-slate-500 hover:text-rr-navy"
          }`}
        >
          <Flame className="w-4 h-4 text-rr-pink" />
          <span>Batting Under Pressure</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-pink-100 text-rr-pink font-bold">
            81 Qualified Batters
          </span>
        </button>

        <button
          onClick={() => setActiveTab("PRESSURE_BOWLING")}
          className={`pb-3 px-1 text-xs font-bold transition-all relative flex items-center gap-2 ${
            activeTab === "PRESSURE_BOWLING"
              ? "text-rr-pink border-b-2 border-rr-pink"
              : "text-slate-500 hover:text-rr-navy"
          }`}
        >
          <Target className="w-4 h-4 text-rr-pink" />
          <span>Bowling Under Pressure</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-pink-100 text-rr-pink font-bold">
            36 Qualified Bowlers
          </span>
        </button>
      </div>

      {/* VIEW 1: DISCIPLINE RATINGS */}
      {activeTab === "DISCIPLINE" && (
        <div className="space-y-4">
          {/* Filter and Search Bar */}
          <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
            {/* Search */}
            <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-sm">
              <div className="relative w-full">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by player name..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:border-rr-pink focus:bg-white focus:outline-none transition-all"
                />
              </div>
              <button
                type="submit"
                className="px-3.5 py-1.5 bg-rr-navy text-xs font-semibold text-white rounded-lg hover:bg-rr-navylight transition-colors"
              >
                Search
              </button>
            </form>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Role Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-slate-600">Playing Role:</span>
                <select
                  value={role}
                  onChange={(e) => {
                    setRole(e.target.value);
                    setPage(1);
                  }}
                  className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-medium text-rr-navy focus:outline-none focus:border-rr-pink"
                >
                  <option value="">All Roles</option>
                  <option value="BATTER">Batters</option>
                  <option value="BOWLER">Bowlers</option>
                  <option value="ALL_ROUNDER">All-Rounders</option>
                  <option value="WICKETKEEPER">Wicketkeepers</option>
                  <option value="UNKNOWN">Not Enough Match Data</option>
                </select>
              </div>

              {/* Sort Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-slate-600">Rank By:</span>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value);
                    setPage(1);
                  }}
                  className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-medium text-rr-navy focus:outline-none focus:border-rr-pink"
                >
                  <option value="overall_batting_rating">Batting Rating (Highest First)</option>
                  <option value="overall_bowling_rating">Bowling Rating (Highest First)</option>
                  <option value="eb_batting_impact">Runs Above Expected (Batting)</option>
                  <option value="eb_bowling_impact">Runs Saved (Bowling)</option>
                  <option value="total_runs">Total Runs Scored</option>
                  <option value="bowler_wickets">Total Wickets Taken</option>
                  <option value="batting_sr">Batting Strike Rate</option>
                  <option value="bowling_econ">Bowling Economy Rate</option>
                </select>
              </div>
            </div>
          </div>

          {/* Insufficient Performance Data Disclaimer Banner */}
          {role === "UNKNOWN" && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-3">
              <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <span>
                <strong>Not Enough Match Data:</strong> These players are included in competition rosters but do not have sufficient recorded match balls in top-tier T20 matches (2022–2026) to provide an official rating.
              </span>
            </div>
          )}

          {/* Players Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-rr-navy font-bold border-b-2 border-pink-100 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4 w-10 text-center">Compare</th>
                    <th className="py-3 px-4">Player</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4 text-center">Matches</th>
                    <th className="py-3 px-4 text-center">Batting Rating</th>
                    <th className="py-3 px-4 text-center">Bowling Rating</th>
                    <th className="py-3 px-4 text-right">Performance Impact</th>
                    <th className="py-3 px-4 text-center">Evidence Level</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {loading ? (
                    <tr>
                      <td colSpan={9} className="py-12 text-center text-slate-400">
                        Loading verified player intelligence records...
                      </td>
                    </tr>
                  ) : players.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="py-12 text-center text-slate-400">
                        No players found matching your filter criteria.
                      </td>
                    </tr>
                  ) : (
                    players.map((p) => {
                      const isChecked = selectedForCompare.includes(p.player_id);
                      const evidence = formatEvidenceLevel(p.confidence_tier);
                      const batRating = p.batting_rating ?? p.overall_batting_rating;
                      const bowlRating = p.bowling_rating ?? p.overall_bowling_rating;

                      return (
                        <tr
                          key={p.player_id}
                          className="hover:bg-pink-50/30 transition-colors group"
                        >
                          <td className="py-3 px-4 text-center">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => toggleCompare(p.player_id)}
                              className="w-4 h-4 rounded border-slate-300 text-rr-pink focus:ring-rr-pink cursor-pointer"
                            />
                          </td>
                          <td className="py-3 px-4">
                            <Link
                              href={`/players/${p.player_id}`}
                              className="font-bold text-rr-navy hover:text-rr-pink transition-colors text-xs flex items-center gap-1.5"
                            >
                              <span>{p.player_name}</span>
                            </Link>
                            <div className="text-[10px] text-slate-500">
                              {p.balls_faced || 0} balls faced · {p.balls_bowled || 0} balls bowled
                            </div>
                          </td>
                          <td className="py-3 px-4 font-medium text-slate-600">
                            {formatRoleTitle(p.primary_role)}
                          </td>
                          <td className="py-3 px-4 text-center font-semibold text-rr-navy">
                            {p.total_matches || p.matches || 0}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {batRating !== null && batRating !== undefined ? (
                              <span className="font-bold text-rr-pink text-xs">
                                {formatRating(batRating)}
                              </span>
                            ) : (
                              <span className="text-[10px] text-slate-400">N/A</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {bowlRating !== null && bowlRating !== undefined ? (
                              <span className="font-bold text-rr-navy text-xs">
                                {formatRating(bowlRating)}
                              </span>
                            ) : (
                              <span className="text-[10px] text-slate-400">N/A</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            {p.eb_batting_impact && p.eb_batting_impact > 0 ? (
                              <span className="text-emerald-700 font-semibold text-xs">
                                +{p.eb_batting_impact.toFixed(2)} Runs/Ball
                              </span>
                            ) : p.eb_bowling_impact && p.eb_bowling_impact > 0 ? (
                              <span className="text-blue-700 font-semibold text-xs">
                                +{p.eb_bowling_impact.toFixed(2)} Saved/Ball
                              </span>
                            ) : (
                              <span className="text-slate-500 text-xs">Standard Baseline</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${evidence.badgeClass}`}
                              title={evidence.description}
                            >
                              {evidence.label}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <Link
                                href={`/players/${p.player_id}`}
                                className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:text-rr-pink hover:bg-pink-50 transition-colors"
                                title="View Player Profile"
                              >
                                <Eye className="w-3.5 h-3.5" />
                              </Link>
                              <button
                                onClick={() => handleQuickWatchlist(p.player_id)}
                                className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 transition-colors"
                                title="Add to Scouting Watchlist"
                              >
                                {addedNote === p.player_id ? (
                                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                                ) : (
                                  <BookmarkPlus className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Bar */}
            <div className="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
              <div>
                Showing <span className="font-bold text-rr-navy">{players.length}</span> of{" "}
                <span className="font-bold text-rr-navy">{total}</span> scouted players
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 font-medium text-slate-700 disabled:opacity-40 hover:bg-slate-100 transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>
                <span className="font-semibold text-rr-navy px-2">Page {page}</span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page * pageSize >= total}
                  className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 font-medium text-slate-700 disabled:opacity-40 hover:bg-slate-100 transition-colors flex items-center gap-1"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: UNIFIED PRESSURE PERFORMER LEADERBOARD */}
      {activeTab === "PRESSURE" && (
        <div className="space-y-4">
          {/* 4 Objective Analytical Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {/* Total Batters Assessed */}
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-rr-navy" />
                  Total Batters Assessed
                </span>
                <span className="text-xl font-black text-rr-navy">
                  {pressureSummary?.total_batters_assessed ?? 0}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                Batters with recorded high-pressure opportunities in qualifying matches.
              </p>
            </div>

            {/* Positively Contributing Batters */}
            <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  Positive Contributors
                </span>
                <span className="text-xl font-black text-emerald-800">
                  {pressureSummary?.positive_batters ?? 0}
                </span>
              </div>
              <p className="text-[11px] text-emerald-800 leading-snug">
                Batters outperforming situational expected run baselines under pressure.
              </p>
            </div>

            {/* Sufficient Ranking Evidence */}
            <div className="p-4 rounded-xl bg-pink-50/60 border border-pink-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-pink-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-rr-pink" />
                  Officially Ranked Batters
                </span>
                <span className="text-xl font-black text-rr-pink">
                  {pressureSummary?.sufficient_evidence_batters ?? 0}
                </span>
              </div>
              <p className="text-[11px] text-pink-800 leading-snug">
                Batters satisfying sample and repeatability thresholds for official rank.
              </p>
            </div>

            {/* Total High-Pressure Matches Evaluated */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-amber-500" />
                  Pressure Matches Evaluated
                </span>
                <span className="text-xl font-black text-rr-navy">
                  {pressureSummary?.total_pressure_matches ?? 0}
                </span>
              </div>
              <p className="text-[11px] text-slate-600 leading-snug">
                Distinct competitive matches with verified high-pressure crisis moments.
              </p>
            </div>
          </div>

          {/* Controls: Competition Scope, Pressure Context & Search */}
          <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              {/* Competition Scope Filter */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                <button
                  onClick={() => setPressureScope("IPL_T20I")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    pressureScope === "IPL_T20I"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Main (IPL & T20I)
                </button>
                <button
                  onClick={() => setPressureScope("IPL")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    pressureScope === "IPL"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  IPL Only
                </button>
                <button
                  onClick={() => setPressureScope("T20I")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    pressureScope === "T20I"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  T20I Only
                </button>
                <button
                  onClick={() => setPressureScope("EMERGING")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    pressureScope === "EMERGING"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Emerging Scope
                </button>
              </div>

              {/* Match Context Filter */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                <button
                  onClick={() => setPressureContext("ALL")}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    pressureContext === "ALL"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  All High-Pressure
                </button>
                <button
                  onClick={() => setPressureContext("CHASE")}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    pressureContext === "CHASE"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Chase Crisis
                </button>
                <button
                  onClick={() => setPressureContext("FIRST_INNINGS")}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    pressureContext === "FIRST_INNINGS"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  1st Innings Pressure
                </button>
              </div>
            </div>

            {/* Player Search Form */}
            <form onSubmit={handlePressureSearchSubmit} className="relative flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter batter name..."
                  value={pressureSearch}
                  onChange={(e) => setPressureSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 w-48 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:border-rr-pink focus:outline-none"
                />
              </div>
              <button
                type="submit"
                className="px-3 py-1.5 bg-rr-navy text-xs font-semibold text-white rounded-lg hover:bg-rr-navylight transition-colors"
              >
                Filter
              </button>
              {pressureSearch && (
                <button
                  type="button"
                  onClick={() => {
                    setPressureSearch("");
                    loadPressureData();
                  }}
                  className="px-2.5 py-1.5 bg-slate-100 text-xs font-medium text-slate-600 rounded-lg hover:bg-slate-200"
                >
                  Clear
                </button>
              )}
            </form>
          </div>

          {/* Unified Pressure Performer Leaderboard Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-rr-navy font-bold border-b-2 border-pink-100 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th
                      onClick={() => handlePressureSort("pressure_rank")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Rank</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("player_name")}
                      className="py-3 px-4 cursor-pointer hover:bg-slate-100 transition-colors"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Player & Role</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_raw_rae_per_100")}
                      className="py-3 px-3 text-right cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1 justify-end">
                        <span>Pressure Impact</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_rae")}
                      className="py-3 px-3 text-right cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1 justify-end">
                        <span>Total Contribution</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_positive_match_pct")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Positive Matches</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_negative_match_pct")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Negative Matches</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_balls")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Pressure Balls (Matches)</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_strike_rate")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>HP Strike Rate</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handlePressureSort("hp_risk_adjusted_impact")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Statistical Uncertainty (CRAI)</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th className="py-3 px-3 text-center whitespace-nowrap">Evidence Status</th>
                    <th className="py-3 px-3 text-right">Profile</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {pressureLoading ? (
                    <tr>
                      <td colSpan={11} className="py-12 text-center text-slate-400">
                        Loading unified pressure performer evaluations...
                      </td>
                    </tr>
                  ) : pressurePerformers.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="py-12 text-center text-slate-400">
                        No batters match the selected pressure criteria and filters.
                      </td>
                    </tr>
                  ) : (
                    pressurePerformers.map((p) => {
                      const isRanked = p.pressure_rank !== null && p.pressure_rank !== undefined;
                      const rawImpact = p.hp_raw_rae_per_100;
                      const isPositive = (rawImpact ?? 0) >= 0;
                      const totalRae = p.hp_rae;
                      const isTotalPos = (totalRae ?? 0) >= 0;
                      const evStatus = formatEvidenceStatus(p.classification);
                      const EvIcon = evStatus.icon;

                      return (
                        <tr
                          key={p.player_id}
                          className="hover:bg-pink-50/30 transition-colors group"
                        >
                          {/* Pressure Rank */}
                          <td className="py-3 px-3 text-center">
                            {isRanked ? (
                              <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-pink-50 border border-pink-200 text-rr-pink font-black text-xs shadow-2xs">
                                #{p.pressure_rank}
                              </span>
                            ) : (
                              <span
                                className="text-slate-400 font-bold text-xs"
                                title={p.hp_balls < 25 ? "Limited Evidence (<25 HP balls)" : "Below Situational Baseline"}
                              >
                                —
                              </span>
                            )}
                          </td>

                          {/* Player & Role */}
                          <td className="py-3 px-4">
                            <Link
                              href={`/players/${p.player_id}`}
                              className="font-bold text-rr-navy hover:text-rr-pink transition-colors text-xs flex items-center gap-1.5"
                            >
                              <span>{p.player_name}</span>
                            </Link>
                            <div className="text-[10px] text-slate-500">
                              {p.bat_style || "Right Handed"} · {p.bowl_style || "Specialist"} · {p.is_wk ? "WK · " : ""}{p.hp_balls ?? 0}b pressure
                            </div>
                          </td>

                          {/* Pressure Impact (RAE/100b) */}
                          <td className="py-3 px-3 text-right">
                            <span
                              className={`font-black text-xs ${
                                rawImpact != null && rawImpact >= 0
                                  ? "text-emerald-700"
                                  : "text-rose-700"
                              }`}
                            >
                              {rawImpact != null
                                ? `${rawImpact >= 0 ? "+" : ""}${Number(rawImpact).toFixed(1)}`
                                : "—"}
                            </span>
                            <div className="text-[10px] text-slate-400">
                              Post: {p.hp_posterior_mean != null ? `${p.hp_posterior_mean >= 0 ? "+" : ""}${Number(p.hp_posterior_mean).toFixed(1)}` : "—"}
                            </div>
                          </td>

                          {/* Total Pressure Contribution */}
                          <td className="py-3 px-3 text-right">
                            <span
                              className={`font-bold text-xs ${
                                totalRae != null && totalRae >= 0
                                  ? "text-emerald-700"
                                  : "text-rose-700"
                              }`}
                            >
                              {totalRae != null
                                ? `${totalRae >= 0 ? "+" : ""}${Number(totalRae).toFixed(1)}`
                                : "—"}{" "}
                              <span className="text-[10px] text-slate-400 font-normal">runs</span>
                            </span>
                          </td>

                          {/* Positive Matches */}
                          <td className="py-3 px-3 text-center">
                            <span className="font-semibold text-emerald-800">
                              {p.hp_positive_matches ?? 0}
                            </span>
                            <span className="text-slate-400 text-[10px]">
                              {" "}
                              ({p.hp_positive_match_pct != null ? `${Number(p.hp_positive_match_pct).toFixed(0)}%` : "—"})
                            </span>
                          </td>

                          {/* Negative Matches */}
                          <td className="py-3 px-3 text-center">
                            <span className="font-semibold text-rose-800">
                              {p.hp_negative_matches ?? 0}
                            </span>
                            <span className="text-slate-400 text-[10px]">
                              {" "}
                              ({p.hp_negative_match_pct != null ? `${Number(p.hp_negative_match_pct).toFixed(0)}%` : "—"})
                            </span>
                          </td>

                          {/* Pressure Opportunities (Balls & Matches) */}
                          <td className="py-3 px-3 text-center font-medium text-slate-700">
                            <strong>{p.hp_balls ?? 0}b</strong>
                            <span className="text-slate-400 text-[10px]">
                              {" "}
                              ({p.hp_matches ?? 0}m)
                            </span>
                          </td>

                          {/* HP Strike Rate */}
                          <td className="py-3 px-3 text-center font-semibold text-rr-navy">
                            {p.hp_strike_rate != null ? Number(p.hp_strike_rate).toFixed(1) : "—"}
                          </td>

                          {/* Statistical Uncertainty (CRAI & CI) */}
                          <td className="py-3 px-3 text-center">
                            <div className="font-bold text-slate-800 text-[11px]">
                              CRAI: {p.hp_risk_adjusted_impact != null ? `${p.hp_risk_adjusted_impact >= 0 ? "+" : ""}${Number(p.hp_risk_adjusted_impact).toFixed(1)}` : "—"}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              95% CI: [{p.hp_lcb_95 != null ? Number(p.hp_lcb_95).toFixed(1) : "—"}, {p.hp_ucb_95 != null ? Number(p.hp_ucb_95).toFixed(1) : "—"}]
                            </div>
                          </td>

                          {/* Evidence Status */}
                          <td className="py-3 px-3 text-center">
                            <span
                              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${evStatus.badgeClass}`}
                            >
                              <EvIcon className="w-3 h-3 shrink-0" />
                              <span>{evStatus.label}</span>
                            </span>
                          </td>

                          {/* Profile Link */}
                          <td className="py-3 px-3 text-right">
                            <Link
                              href={`/players/${p.player_id}`}
                              className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:text-rr-pink hover:bg-pink-50 transition-colors inline-flex items-center justify-center"
                              title="View Full Player Profile"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </Link>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Table Footer */}
            <div className="p-3.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex flex-col sm:flex-row items-center justify-between gap-2">
              <div>
                Displaying <span className="font-bold text-rr-navy">{pressurePerformers.length}</span> batters on the Unified Pressure Performer Leaderboard.
              </div>
              <div className="text-[11px] text-slate-500">
                Official ranks assigned based on Conservative Risk-Adjusted Impact (CRAI) and posterior repeatability. Zero artificial category segregation.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: BOWLING UNDER PRESSURE */}
      {activeTab === "PRESSURE_BOWLING" && (
        <div className="space-y-4">
          {/* 4 Objective Analytical Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {/* Total Bowlers Assessed */}
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-rr-navy" />
                  Pressure Bowlers Assessed
                </span>
                <span className="text-xl font-black text-rr-navy">
                  {bowlerSummary?.total_bowlers_assessed ?? 511}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                511 bowlers with high-pressure exposure (out of 596 primary-scope bowlers).
              </p>
            </div>

            {/* Positively Contributing Bowlers */}
            <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  Positive Contributors
                </span>
                <span className="text-xl font-black text-emerald-800">
                  {bowlerSummary?.positive_bowlers ?? 148}
                </span>
              </div>
              <p className="text-[11px] text-emerald-800 leading-snug">
                Bowlers restricting runs or taking wickets above situational baselines.
              </p>
            </div>

            {/* Sufficient Ranking Evidence */}
            <div className="p-4 rounded-xl bg-pink-50/60 border border-pink-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-pink-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-rr-pink" />
                  Officially Ranked Bowlers
                </span>
                <span className="text-xl font-black text-rr-pink">
                  {bowlerSummary?.sufficient_evidence_bowlers ?? 36}
                </span>
              </div>
              <p className="text-[11px] text-pink-800 leading-snug">
                Bowlers satisfying sample (≥4 ov, ≥3m) and posterior repeatability thresholds.
              </p>
            </div>

            {/* Total Defensive Pressure Matches Evaluated */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-rr-navy" />
                  Pressure Matches Evaluated
                </span>
                <span className="text-xl font-black text-rr-navy">
                  {bowlerSummary?.total_pressure_matches ?? 783}
                </span>
              </div>
              <p className="text-[11px] text-slate-600 leading-snug">
                Distinct competitive matches with verified defensive pressure overs.
              </p>
            </div>
          </div>

          {/* Controls: Competition Scope, Bowling Style & Search */}
          <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              {/* Competition Scope Filter */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                <button
                  onClick={() => setBowlerScope("IPL_T20I")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    bowlerScope === "IPL_T20I"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Main (IPL & T20I)
                </button>
                <button
                  onClick={() => setBowlerScope("IPL")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    bowlerScope === "IPL"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  IPL Only
                </button>
                <button
                  onClick={() => setBowlerScope("T20I")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    bowlerScope === "T20I"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  T20I Only
                </button>
                <button
                  onClick={() => setBowlerScope("EMERGING")}
                  className={`px-3 py-1 rounded-md transition-all ${
                    bowlerScope === "EMERGING"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Emerging Scope
                </button>
              </div>

              {/* Pace vs Spin Filter */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                <button
                  onClick={() => setBowlerPaceSpin("ALL")}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    bowlerPaceSpin === "ALL"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  All Styles
                </button>
                <button
                  onClick={() => setBowlerPaceSpin("PACE")}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    bowlerPaceSpin === "PACE"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Pace
                </button>
                <button
                  onClick={() => setBowlerPaceSpin("SPIN")}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    bowlerPaceSpin === "SPIN"
                      ? "bg-white text-rr-navy shadow-xs font-bold"
                      : "text-slate-600 hover:text-rr-navy"
                  }`}
                >
                  Spin
                </button>
              </div>
            </div>

            {/* Bowler Search Form */}
            <form onSubmit={handleBowlerSearchSubmit} className="relative flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter bowler name..."
                  value={bowlerSearch}
                  onChange={(e) => setBowlerSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 w-48 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:border-rr-pink focus:outline-none"
                />
              </div>
              <button
                type="submit"
                className="px-3 py-1.5 bg-rr-navy text-xs font-semibold text-white rounded-lg hover:bg-rr-navylight transition-colors"
              >
                Filter
              </button>
              {bowlerSearch && (
                <button
                  type="button"
                  onClick={() => {
                    setBowlerSearch("");
                    loadPressureBowlerData();
                  }}
                  className="px-2.5 py-1.5 bg-slate-100 text-xs font-medium text-slate-600 rounded-lg hover:bg-slate-200"
                >
                  Clear
                </button>
              )}
            </form>
          </div>

          {/* Unified Pressure Bowler Leaderboard Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-rr-navy font-bold border-b-2 border-pink-100 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th
                      onClick={() => handleBowlerSort("pressure_rank")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Rank</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("player_name")}
                      className="py-3 px-4 cursor-pointer hover:bg-slate-100 transition-colors"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Bowler & Style</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_raw_runs_saved_per_6b")}
                      className="py-3 px-3 text-right cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1 justify-end">
                        <span>Runs Saved / 6b</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_runs_saved")}
                      className="py-3 px-3 text-right cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1 justify-end">
                        <span>Total Runs Saved</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_wae")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>WAE (Rank)</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_wickets")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Pressure Wickets</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_overs")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Pressure Overs</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_economy_rate")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Economy</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_positive_match_pct")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Positive Matches</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleBowlerSort("hp_risk_adjusted_impact")}
                      className="py-3 px-3 text-center cursor-pointer hover:bg-slate-100 transition-colors whitespace-nowrap"
                    >
                      <div className="inline-flex items-center gap-1">
                        <span>Uncertainty (CRAI & CI)</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th className="py-3 px-3 text-center whitespace-nowrap">Evidence Status</th>
                    <th className="py-3 px-3 text-right">Profile</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {bowlerLoading ? (
                    <tr>
                      <td colSpan={12} className="py-16 text-center text-slate-400 text-xs">
                        Loading Unified Pressure Bowler Leaderboard...
                      </td>
                    </tr>
                  ) : pressureBowlers.length === 0 ? (
                    <tr>
                      <td colSpan={12} className="py-16 text-center text-slate-400 text-xs">
                        No bowlers found matching the selected pressure criteria.
                      </td>
                    </tr>
                  ) : (
                    pressureBowlers.map((b: any) => {
                      const rank = b.pressure_rank;
                      const runsSavedPer6b = b.hp_raw_runs_saved_per_6 ?? b.hp_raw_runs_saved_per_6b;
                      const postRunsSaved = b.hp_posterior_mean ?? b.hp_posterior_runs_saved_per_6b;
                      const totalRunsSaved = b.hp_runs_saved;
                      const wae = b.hp_wae;
                      const waeRank = b.pressure_wicket_rank ?? b.hp_wae_rank;
                      const evStatus = formatEvidenceStatus(b.data_status || b.evidence_status);
                      const EvIcon = evStatus.icon;

                      return (
                        <tr
                          key={b.player_id}
                          className="hover:bg-pink-50/25 transition-colors border-b border-slate-100 last:border-b-0"
                        >
                          {/* Rank */}
                          <td className="py-3 px-3 text-center">
                            {rank ? (
                              <span
                                className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-black ${
                                  rank === 1
                                    ? "bg-amber-100 text-amber-900 border border-amber-300 shadow-2xs"
                                    : rank === 2
                                    ? "bg-slate-200 text-slate-800 border border-slate-300"
                                    : rank === 3
                                    ? "bg-amber-50 text-amber-800 border border-amber-200"
                                    : "bg-slate-100 text-slate-700 font-bold"
                                }`}
                              >
                                {rank}
                              </span>
                            ) : (
                              <span className="text-[11px] font-bold text-slate-400">
                                —
                              </span>
                            )}
                          </td>

                          {/* Bowler & Style */}
                          <td className="py-3 px-4">
                            <Link
                              href={`/players/${b.player_id}`}
                              className="font-bold text-rr-navy hover:text-rr-pink transition-colors text-xs flex items-center gap-1.5"
                            >
                              <span>{b.player_name}</span>
                            </Link>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-[10px] text-slate-500 font-medium">
                                {b.bowling_style || "Bowler"}
                              </span>
                              <span className="text-slate-300">•</span>
                              <span
                                className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                  b.pace_or_spin === "Pace"
                                    ? "bg-blue-50 text-blue-700 border border-blue-100"
                                    : "bg-purple-50 text-purple-700 border border-purple-100"
                                }`}
                              >
                                {b.pace_or_spin || "Specialist"}
                              </span>
                            </div>
                          </td>

                          {/* Runs Saved / 6b */}
                          <td className="py-3 px-3 text-right">
                            <span
                              className={`font-black text-xs ${
                                runsSavedPer6b != null && runsSavedPer6b >= 0
                                  ? "text-emerald-700"
                                  : "text-rose-700"
                              }`}
                            >
                              {runsSavedPer6b != null
                                ? `${runsSavedPer6b >= 0 ? "+" : ""}${Number(runsSavedPer6b).toFixed(2)}`
                                : "—"}
                            </span>
                            <div className="text-[10px] text-slate-400">
                              Post: {postRunsSaved != null ? `${postRunsSaved >= 0 ? "+" : ""}${Number(postRunsSaved).toFixed(2)}` : "—"}
                            </div>
                          </td>

                          {/* Total Runs Saved */}
                          <td className="py-3 px-3 text-right">
                            <span
                              className={`font-bold text-xs ${
                                totalRunsSaved != null && totalRunsSaved >= 0
                                  ? "text-emerald-700"
                                  : "text-rose-700"
                              }`}
                            >
                              {totalRunsSaved != null
                                ? `${totalRunsSaved >= 0 ? "+" : ""}${Number(totalRunsSaved).toFixed(1)}`
                                : "—"}{" "}
                              <span className="text-[10px] text-slate-400 font-normal">runs</span>
                            </span>
                          </td>

                          {/* WAE (Rank) */}
                          <td className="py-3 px-3 text-center">
                            <span
                              className={`font-bold text-xs ${
                                wae != null && wae >= 0 ? "text-emerald-700" : "text-slate-600"
                              }`}
                            >
                              {wae != null ? `${wae >= 0 ? "+" : ""}${Number(wae).toFixed(2)}` : "—"}
                            </span>
                            {waeRank && (
                              <div className="text-[10px] text-slate-400 font-semibold">
                                WAE #{waeRank}
                              </div>
                            )}
                          </td>

                          {/* Pressure Wickets */}
                          <td className="py-3 px-3 text-center">
                            <span className="font-bold text-rr-navy text-xs">
                              {b.hp_wickets ?? 0}
                            </span>
                            <span className="text-slate-400 text-[10px]">
                              {" "}
                              wkts ({b.hp_balls ?? b.hp_legal_balls ?? 0}b)
                            </span>
                          </td>

                          {/* Pressure Overs */}
                          <td className="py-3 px-3 text-center font-medium text-slate-700">
                            <strong>{b.hp_overs != null ? Number(b.hp_overs).toFixed(1) : "0.0"} ov</strong>
                            <span className="text-slate-400 text-[10px]">
                              {" "}
                              ({b.hp_matches ?? 0}m)
                            </span>
                          </td>

                          {/* Economy */}
                          <td className="py-3 px-3 text-center font-semibold text-rr-navy">
                            {b.hp_economy_rate != null ? Number(b.hp_economy_rate).toFixed(2) : "—"}
                          </td>

                          {/* Positive Matches */}
                          <td className="py-3 px-3 text-center">
                            <span className="font-semibold text-emerald-800">
                              {b.hp_positive_matches ?? 0}
                            </span>
                            <span className="text-slate-400 text-[10px]">
                              {" "}
                              ({b.hp_positive_match_pct != null ? `${Number(b.hp_positive_match_pct).toFixed(0)}%` : "—"})
                            </span>
                          </td>

                          {/* Uncertainty (CRAI & CI) */}
                          <td className="py-3 px-3 text-center">
                            <div className="font-bold text-slate-800 text-[11px]">
                              CRAI: {b.hp_risk_adjusted_impact != null ? `${b.hp_risk_adjusted_impact >= 0 ? "+" : ""}${Number(b.hp_risk_adjusted_impact).toFixed(2)}` : "—"}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              95% CI: [{b.hp_lcb_95 != null ? Number(b.hp_lcb_95).toFixed(2) : "—"}, {b.hp_ucb_95 != null ? Number(b.hp_ucb_95).toFixed(2) : "—"}]
                            </div>
                          </td>

                          {/* Evidence Status */}
                          <td className="py-3 px-3 text-center">
                            <span
                              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${evStatus.badgeClass}`}
                            >
                              <EvIcon className="w-3 h-3 shrink-0" />
                              <span>{evStatus.label}</span>
                            </span>
                          </td>

                          {/* Profile Link */}
                          <td className="py-3 px-3 text-right">
                            <Link
                              href={`/players/${b.player_id}`}
                              className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:text-rr-pink hover:bg-pink-50 transition-colors inline-flex items-center justify-center"
                              title="View Full Bowler Profile"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </Link>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Table Footer */}
            <div className="p-3.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex flex-col sm:flex-row items-center justify-between gap-2">
              <div>
                Displaying <span className="font-bold text-rr-navy">{pressureBowlers.length}</span> bowlers on the Unified Pressure Bowler Leaderboard.
              </div>
              <div className="text-[11px] text-slate-500">
                Official ranks assigned based on Conservative Risk-Adjusted Impact (CRAI) on run prevention and posterior repeatability. Sortable by WAE for wicket creation. Zero artificial category silos.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PlayerDiscoveryPage() {
  return (
    <Suspense
      fallback={
        <div className="py-24 text-center text-slate-400 text-xs">
          Loading player discovery workspace...
        </div>
      }
    >
      <DiscoveryContent />
    </Suspense>
  );
}
