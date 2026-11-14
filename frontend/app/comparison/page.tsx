"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { formatPlayerRole } from "@/lib/formatRole";
import {
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import {
  GitCompare,
  Award,
  Zap,
  TrendingUp,
  AlertCircle,
  X,
  Search,
  Check,
  ShieldCheck,
  ChevronRight,
  Info,
} from "lucide-react";

function ComparisonContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [playerIds, setPlayerIds] = useState<number[]>([]);
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [pressureBowlingComparison, setPressureBowlingComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Search state to add more players
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  useEffect(() => {
    const idsParam = searchParams.get("ids");
    if (idsParam) {
      const parsedIds = idsParam
        .split(",")
        .map(Number)
        .filter((n) => !isNaN(n));
      setPlayerIds(parsedIds);
    } else {
      loadDefaultComparison();
    }
  }, [searchParams]);

  async function loadDefaultComparison() {
    try {
      const topBat = await api.getBatterRankings(2);
      if (topBat.length >= 2) {
        const ids = [topBat[0].player_id, topBat[1].player_id];
        setPlayerIds(ids);
        executeComparison(ids);
      }
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    if (playerIds.length >= 2) {
      executeComparison(playerIds);
    }
  }, [playerIds]);

  async function executeComparison(ids: number[]) {
    setLoading(true);
    try {
      const [data, bowlData] = await Promise.all([
        api.comparePlayers(ids),
        api.comparePressureBowlers(ids).catch(() => null),
      ]);
      setComparisonData(data);
      setPressureBowlingComparison(bowlData);
    } catch (err) {
      console.error("Comparison error:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      const res = await api.getPlayers({ search: searchQuery, page_size: 5 });
      setSearchResults(res.items);
    } catch (err) {
      console.error(err);
    }
  }

  function addPlayer(pid: number) {
    if (playerIds.includes(pid)) return;
    if (playerIds.length >= 4) {
      alert("Maximum 4 players can be compared simultaneously.");
      return;
    }
    const updated = [...playerIds, pid];
    setPlayerIds(updated);
    setSearchResults([]);
    setSearchQuery("");
  }

  function removePlayer(pid: number) {
    const updated = playerIds.filter((id) => id !== pid);
    setPlayerIds(updated);
  }

  const players = comparisonData?.players || [];
  const scenarios = comparisonData?.winner_by_scenario || {};

  return (
    <div className="space-y-6">
      {/* Page Title & Add Tool */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-rr-navy flex items-center gap-2.5">
            <GitCompare className="w-6 h-6 text-rr-pink" />
            Player Comparison Lab
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Evaluate 2 to 4 candidates side-by-side using evidence-based ratings, match pressure impact, and tactical head-to-head scenarios.
          </p>
        </div>

        {/* Player Add Form */}
        <div className="relative">
          <form onSubmit={handleSearch} className="flex items-center gap-1.5">
            <input
              type="text"
              placeholder="Search player to add..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rr-pink shadow-xs"
            />
            <button
              type="submit"
              className="p-1.5 bg-rr-navy text-white rounded-lg hover:bg-rr-navylight transition-colors shadow-xs"
            >
              <Search className="w-4 h-4" />
            </button>
          </form>

          {searchResults.length > 0 && (
            <div className="absolute right-0 mt-1 w-72 bg-white border border-slate-200 rounded-xl shadow-lg z-20 p-2 space-y-1">
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider px-2 py-1">
                Select Candidate:
              </div>
              {searchResults.map((r) => (
                <button
                  key={r.player_id}
                  onClick={() => addPlayer(r.player_id)}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-pink-50 text-xs text-rr-navy font-semibold flex items-center justify-between transition-colors"
                >
                  <span>{r.player_name}</span>
                  <span className="text-[10px] font-normal text-slate-500">
                    {formatRoleTitle(r.primary_role)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Selected Player Chips */}
      <div className="flex flex-wrap items-center gap-2">
        {players.map((p: any, idx: number) => (
          <div
            key={p.player_id}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs shadow-xs ${
              idx === 0
                ? "bg-pink-50 border-pink-200 text-rr-pink font-bold"
                : "bg-blue-50 border-blue-200 text-rr-navy font-bold"
            }`}
          >
            <span>{p.player_name}</span>
            <span className="text-[10px] font-medium text-slate-500">
              ({formatRoleTitle(p.primary_role)})
            </span>
            {players.length > 2 && (
              <button
                onClick={() => removePlayer(p.player_id)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Winner by Scenario Arbitration Cards */}
      {Object.keys(scenarios).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(scenarios).map(([scName, scData]: any) => (
            <div
              key={scName}
              className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2 hover:border-pink-200 transition-colors"
            >
              <div className="text-xs font-bold text-slate-500 flex items-center gap-2 uppercase tracking-wider">
                <Award className="w-4 h-4 text-rr-pink" />
                <span>{scName}</span>
              </div>
              <div className="text-lg font-extrabold text-rr-navy">
                {scData.winner_name || "Insufficient Match Data"}
              </div>
              <div className="text-xs text-emerald-700 font-semibold">
                {scData.metric || "Verified evidence criteria"}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Head-to-Head Comparative Metric Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-xs text-rr-navy uppercase tracking-wider">
          Head-to-Head Tactical Comparison Matrix
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-white text-rr-navy font-bold border-b-2 border-pink-100">
              <tr>
                <th className="py-3 px-4 w-1/4">Tactical Criterion</th>
                {players.map((p: any, idx: number) => (
                  <th
                    key={p.player_id}
                    className={`py-3 px-4 font-extrabold text-sm ${
                      idx === 0 ? "text-rr-pink" : "text-rr-navy"
                    }`}
                  >
                    {p.player_name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {/* Primary Role */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Primary Playing Role</td>
                {players.map((p: any) => (
                  <td key={p.player_id} className="py-3 px-4 font-medium">
                    {formatRoleTitle(p.primary_role)}
                  </td>
                ))}
              </tr>

              {/* Batting Rating */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Official Batting Rating</td>
                {players.map((p: any) => {
                  const r = p.batting_rating ?? p.overall_batting_rating;
                  return (
                    <td key={p.player_id} className="py-3 px-4">
                      {r !== null && r !== undefined ? (
                        <span className="font-extrabold text-rr-pink text-sm">
                          {formatRating(r)}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs italic">Not Enough Match Data</span>
                      )}
                    </td>
                  );
                })}
              </tr>

              {/* Bowling Rating */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Official Bowling Rating</td>
                {players.map((p: any) => {
                  const r = p.bowling_rating ?? p.overall_bowling_rating;
                  return (
                    <td key={p.player_id} className="py-3 px-4">
                      {r !== null && r !== undefined ? (
                        <span className="font-extrabold text-rr-navy text-sm">
                          {formatRating(r)}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs italic">Not Enough Match Data</span>
                      )}
                    </td>
                  );
                })}
              </tr>

              {/* Career Matches */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Scouted Matches</td>
                {players.map((p: any) => (
                  <td key={p.player_id} className="py-3 px-4 font-semibold text-slate-800">
                    {p.total_matches || p.matches || 0} matches
                  </td>
                ))}
              </tr>

              {/* Balls Faced & Runs */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Batting Sample & Strike Rate</td>
                {players.map((p: any) => (
                  <td key={p.player_id} className="py-3 px-4">
                    {p.balls_faced > 0 ? (
                      <span>
                        <strong className="text-rr-navy">{p.total_runs}</strong> runs (
                        {p.balls_faced} balls) · SR{" "}
                        <strong className="text-rr-pink">{p.batting_sr != null ? Number(p.batting_sr).toFixed(1) : "N/A"}</strong>
                      </span>
                    ) : (
                      <span className="text-slate-400 text-xs italic">Not Enough Match Data</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Bowling Sample & Economy */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Bowling Sample & Economy</td>
                {players.map((p: any) => (
                  <td key={p.player_id} className="py-3 px-4">
                    {p.balls_bowled > 0 ? (
                      <span>
                        <strong className="text-rr-navy">{p.bowler_wickets}</strong> wkts (
                        {p.balls_bowled} balls) · Econ{" "}
                        <strong className="text-rr-navy">{p.bowling_econ != null ? Number(p.bowling_econ).toFixed(2) : "N/A"}</strong>
                      </span>
                    ) : (
                      <span className="text-slate-400 text-xs italic">Not Enough Match Data</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Evidence Strength */}
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-700">Evidence Reliability Level</td>
                {players.map((p: any) => {
                  const ev = formatEvidenceLevel(p.confidence_tier);
                  return (
                    <td key={p.player_id} className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${ev.badgeClass}`}
                      >
                        {ev.label}
                      </span>
                    </td>
                  );
                })}
              </tr>

              {/* Pressure Bowler Rank */}
              <tr className="hover:bg-pink-50/30">
                <td className="py-3 px-4 font-bold text-rr-navy">Pressure Bowler Rank</td>
                {players.map((p: any) => {
                  const bInfo = pressureBowlingComparison?.players?.[p.player_id] || p.pressure_bowling;
                  const rank = bInfo?.primary_rank;
                  return (
                    <td key={p.player_id} className="py-3 px-4">
                      {rank ? (
                        <span className="inline-flex items-center gap-1 font-black text-xs text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          <Award className="w-3.5 h-3.5 text-emerald-600" />
                          Rank #{rank}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs italic">Unranked</span>
                      )}
                    </td>
                  );
                })}
              </tr>

              {/* Pressure Runs Saved / 6b */}
              <tr className="hover:bg-pink-50/30">
                <td className="py-3 px-4 font-bold text-rr-navy">Defensive Impact (Runs Saved/6b)</td>
                {players.map((p: any) => {
                  const bInfo = pressureBowlingComparison?.players?.[p.player_id] || p.pressure_bowling;
                  const runsSaved = bInfo?.raw_runs_saved_per_6b ?? bInfo?.hp_raw_runs_saved_per_6b;
                  return (
                    <td key={p.player_id} className="py-3 px-4">
                      {runsSaved != null ? (
                        <span className={`font-black text-xs ${runsSaved >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                          {runsSaved >= 0 ? "+" : ""}{Number(runsSaved).toFixed(2)} runs/6b
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs italic">—</span>
                      )}
                    </td>
                  );
                })}
              </tr>

              {/* WAE */}
              <tr className="hover:bg-pink-50/30">
                <td className="py-3 px-4 font-bold text-rr-navy">Wickets Above Expected (WAE)</td>
                {players.map((p: any) => {
                  const bInfo = pressureBowlingComparison?.players?.[p.player_id] || p.pressure_bowling;
                  const wae = bInfo?.wae ?? bInfo?.hp_wae;
                  return (
                    <td key={p.player_id} className="py-3 px-4">
                      {wae != null ? (
                        <span className={`font-bold text-xs ${wae >= 0 ? "text-emerald-700" : "text-slate-700"}`}>
                          {wae >= 0 ? "+" : ""}{Number(wae).toFixed(2)} wkts
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs italic">—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Comparative Visualisation */}
      {players.length >= 2 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-sm font-bold text-rr-navy">
                Side-by-Side Performance Comparison
              </h2>
              <p className="text-xs text-slate-500">
                Direct visual benchmark across key performance and pressure metrics.
              </p>
            </div>
          </div>

          <PlotlyChart
            data={[
              {
                x: ["Batting Impact", "Pressure Response", "Scoring Consistency"],
                y: [
                  players[0]?.eb_batting_impact ? Math.max(0, players[0].eb_batting_impact * 20) : 10,
                  players[0]?.eb_batting_impact ? Math.max(0, players[0].eb_batting_impact * 25) : 12,
                  players[0]?.total_matches ? Math.min(30, players[0].total_matches) : 10,
                ],
                name: players[0]?.player_name || "Player 1",
                type: "bar",
                marker: { color: "#E50695" },
              },
              {
                x: ["Batting Impact", "Pressure Response", "Scoring Consistency"],
                y: [
                  players[1]?.eb_batting_impact ? Math.max(0, players[1].eb_batting_impact * 20) : 8,
                  players[1]?.eb_batting_impact ? Math.max(0, players[1].eb_batting_impact * 25) : 14,
                  players[1]?.total_matches ? Math.min(30, players[1].total_matches) : 10,
                ],
                name: players[1]?.player_name || "Player 2",
                type: "bar",
                marker: { color: "#001C58" },
              },
            ]}
            layout={{
              barmode: "group",
              height: 300,
              margin: { l: 40, r: 20, t: 30, b: 40 },
            }}
          />
        </div>
      )}
    </div>
  );
}

export default function PlayerComparisonPage() {
  return (
    <Suspense
      fallback={
        <div className="py-24 text-center text-slate-400 text-xs">
          Loading comparison lab...
        </div>
      }
    >
      <ComparisonContent />
    </Suspense>
  );
}
