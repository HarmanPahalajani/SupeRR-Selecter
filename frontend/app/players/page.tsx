"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatRating } from "@/lib/presentation";
import {
  Search,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Award,
  Zap,
  X,
} from "lucide-react";

interface SearchPlayer {
  player_id: number;
  player_name: string;
  primary_role: string;
  overall_player_rating: number | null;
  overall_batting_rating: number | null;
  overall_bowling_rating: number | null;
  total_matches: number;
  balls_faced: number;
  balls_bowled: number;
  confidence_tier?: string;
}

const FEATURED_SUGGESTIONS = [
  { player_id: 47, name: "Virat Kohli", role: "Anchor / Chase Specialist" },
  { player_id: 2933, name: "Jasprit Bumrah", role: "#1 Pressure Bowler" },
  { player_id: 4847, name: "Finn Allen", role: "#1 Situational Batter" },
  { player_id: 4260, name: "Heinrich Klaasen", role: "Middle-Overs Spin Destroyer" },
  { player_id: 2258, name: "Sanju Samson", role: "RR Captain & WK-Batter" },
  { player_id: 2367, name: "Travis Head", role: "Powerplay Impact Batter" },
  { player_id: 3125, name: "Nicholas Pooran", role: "High-RAE Finisher" },
];

export default function PlayersSearchHubPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchPlayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timeout = setTimeout(async () => {
      try {
        const res = await api.getPlayers({ search: trimmed, page_size: 7 });
        setResults(res.items || []);
        setSelectedIndex(0);
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setLoading(false);
      }
    }, 120);

    return () => clearTimeout(timeout);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (results.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const selected = results[selectedIndex];
      if (selected) {
        router.push(`/players/${selected.player_id}`);
      }
    } else if (e.key === "Escape") {
      setQuery("");
      setResults([]);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm min-h-[78vh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background Subtle Gradient Accents */}
      <div className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-pink-50/50 via-white to-transparent pointer-events-none" />
      <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-pink-100/30 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-80 h-80 rounded-full bg-blue-100/30 blur-3xl pointer-events-none" />

      <div className="w-full max-w-2xl mx-auto space-y-7 text-center relative z-10">
        {/* Title Header */}
        <div className="space-y-3">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-rr-navy">
            Search Player Intelligence
          </h1>

          <p className="text-xs sm:text-sm text-slate-500 max-w-lg mx-auto leading-relaxed">
            Search any player across 1,217 assessed profiles to open their situational pressure analytics, phase breakdowns, and recruitment verdict.
          </p>
        </div>

        {/* Center Search Bar Container */}
        <div className="relative text-left">
          <div className="relative flex items-center shadow-md rounded-2xl border-2 border-slate-200 bg-white focus-within:border-rr-pink focus-within:ring-4 focus-within:ring-pink-100/60 transition-all px-4 sm:px-5">
            <Search className="w-5 h-5 text-slate-400 shrink-0 mr-3 pointer-events-none" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search any player by name... (e.g. Virat Kohli, Jasprit Bumrah)"
              className="w-full py-4 text-sm sm:text-base font-semibold text-slate-800 placeholder-slate-400 bg-transparent focus:outline-none"
            />
            {query && (
              <button
                onClick={() => {
                  setQuery("");
                  setResults([]);
                  inputRef.current?.focus();
                }}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors shrink-0 ml-2"
                title="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Autocomplete Results Dropdown */}
          {query.trim().length > 0 && (
            <div className="absolute top-full inset-x-0 mt-2 bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden z-50 divide-y divide-slate-100">
              {loading && results.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-400">
                  Searching verified dossiers...
                </div>
              ) : results.length > 0 ? (
                <div>
                  <div className="px-4 py-2 bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400 flex justify-between items-center">
                    <span>Matched Players ({results.length})</span>
                    <span>Use ↑ ↓ to navigate, Enter to select</span>
                  </div>
                  {results.map((p, idx) => {
                    const isSelected = idx === selectedIndex;
                    const rating = p.overall_player_rating ?? p.overall_batting_rating ?? p.overall_bowling_rating;

                    return (
                      <Link
                        key={p.player_id}
                        href={`/players/${p.player_id}`}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        className={`flex items-center justify-between px-4 py-3 transition-colors ${
                          isSelected ? "bg-pink-50/70" : "hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div
                            className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
                              isSelected
                                ? "bg-rr-pink text-white"
                                : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {p.player_name.charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <div className="font-bold text-sm text-rr-navy truncate flex items-center gap-2">
                              <span>{p.player_name}</span>
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
                                {p.primary_role}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 truncate">
                              {p.total_matches} matches · {p.balls_faced} balls faced · {p.balls_bowled} balls bowled
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          {rating != null ? (
                            <div className="text-right">
                              <div className="text-xs font-bold text-rr-pink">
                                Rating {formatRating(rating)}
                              </div>
                              <div className="text-[10px] text-slate-400 font-medium">
                                {p.confidence_tier || "Assessed"}
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 font-medium">Unrated</span>
                          )}
                          <ArrowRight className={`w-4 h-4 ${isSelected ? "text-rr-pink" : "text-slate-300"}`} />
                        </div>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div className="p-6 text-center space-y-1">
                  <div className="text-xs font-semibold text-slate-700">No players found matching "{query}"</div>
                  <div className="text-[11px] text-slate-400">
                    Try checking spelling or search by last name (e.g. Bumrah, Allen, Klaasen).
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quick Suggestion Pills */}
        <div className="space-y-2.5 pt-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Quick Featured Profiles
          </div>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {FEATURED_SUGGESTIONS.map((sug) => (
              <Link
                key={sug.player_id}
                href={`/players/${sug.player_id}`}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-50 hover:bg-pink-50 border border-slate-200 hover:border-pink-200 text-xs font-semibold text-slate-700 hover:text-rr-pink transition-all shadow-2xs"
              >
                <span>{sug.name}</span>
                <span className="text-[10px] text-slate-400 group-hover:text-rr-pink/70 font-normal">
                  ({sug.role})
                </span>
              </Link>
            ))}
          </div>
        </div>

        {/* Bottom Helper Link to Discovery */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-center gap-2 text-xs text-slate-500">
          <span>Looking to compare or filter by criteria?</span>
          <Link
            href="/discovery"
            className="font-bold text-rr-pink hover:text-rr-darkpink inline-flex items-center gap-1 transition-colors"
          >
            <span>Open Player Discovery Table</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
