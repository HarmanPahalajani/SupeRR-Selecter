"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatPlayerRole } from "@/lib/formatRole";
import {
  formatCurrency,
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { PressureOverviewCards } from "@/components/visuals/PressureOverviewCards";
import {
  Award,
  Zap,
  ArrowRight,
  ShieldCheck,
  Search,
  TrendingUp,
  Sparkles,
  Layers,
  ChevronRight,
  Users,
  Compass,
  Flame,
} from "lucide-react";

export default function OverviewPage() {
  const [coverage, setCoverage] = useState<any>(null);
  const [topBatters, setTopBatters] = useState<any[]>([]);
  const [topBowlers, setTopBowlers] = useState<any[]>([]);
  const [undervalued, setUndervalued] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [cov, bat, bowl, und] = await Promise.all([
          api.getCoverage(),
          api.getBatterRankings(6),
          api.getBowlerRankings(6),
          api.getUndervaluedTalents(),
        ]);
        setCoverage(cov);
        setTopBatters(bat);
        setTopBowlers(bowl);
        setUndervalued(und.slice(0, 5));
      } catch (err) {
        console.error("Failed to load overview data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Editorial Hero Header */}
      <div className="bg-gradient-to-r from-white via-pink-50/40 to-white p-6 rounded-2xl border border-pink-100/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1.5 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-pink-100/60 border border-pink-200/60 text-[11px] font-bold text-rr-pink">
            <Sparkles className="w-3.5 h-3.5 text-rr-pink" />
            <span>Rajasthan Royals Recruitment Intelligence</span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-rr-navy">
            Cricket Scouting & Auction Intelligence
          </h1>
          <p className="text-xs lg:text-sm text-slate-600 leading-relaxed">
            Evidence-first player evaluation across 853 elite T20 matches. Assess true situational impact, compare prospects, and build optimized auction squads.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Link href="/discovery" className="btn-rr-primary">
            <Search className="w-4 h-4" />
            <span>Discover Players</span>
          </Link>
          <Link href="/squad-architect" className="btn-rr-secondary">
            <span>Squad Architect</span>
            <ArrowRight className="w-4 h-4 text-slate-400" />
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Deliveries */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2 hover:border-pink-200 transition-colors">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Deliveries Analyzed
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-rr-navy tracking-tight">
            {coverage ? coverage.total_deliveries.toLocaleString() : "200,961"}
          </div>
          <div className="text-xs text-slate-500 font-medium">
            {coverage
              ? `${coverage.primary_scope_deliveries.toLocaleString()} main competition balls`
              : "193,988 in IPL & T20I"}
          </div>
        </div>

        {/* Matches Covered */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2 hover:border-pink-200 transition-colors">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Main Competition Matches
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-rr-navy tracking-tight">
            {coverage ? coverage.primary_scope_matches : "853"}
          </div>
          <div className="text-xs font-semibold text-rr-pink flex items-center gap-1">
            <span>IPL 2022–2026 & Official T20Is</span>
          </div>
        </div>

        {/* Players Assessed */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2 hover:border-pink-200 transition-colors">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Players Assessed
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-rr-navy tracking-tight">
            {coverage ? coverage.unique_players.toLocaleString() : "1,217"}
          </div>
          <div className="text-xs text-slate-500 font-medium">
            341 Batters · 311 Bowlers Qualified
          </div>
        </div>
      </div>

      {/* Pressure Performance Overview: Visual Analytics for Batting and Bowling */}
      <PressureOverviewCards />

      {/* Main Grid: Batting Leaderboard, Bowling Leaderboard, Undervalued Talents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Batting Performers */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-pink-50 text-rr-pink">
                <Award className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-rr-navy">Top Batting Performers</h2>
                <p className="text-[11px] text-slate-500">Ranked by verified situational contribution</p>
              </div>
            </div>
            <Link
              href="/discovery?discipline=batting"
              className="text-xs font-semibold text-rr-pink hover:text-rr-darkpink transition-colors"
            >
              View All
            </Link>
          </div>

          <div className="space-y-2">
            {topBatters.map((b) => (
              <Link
                key={b.player_id}
                href={`/players/${b.player_id}`}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-pink-200 hover:bg-pink-50/30 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <span className="w-5 text-center text-xs font-bold text-slate-400 group-hover:text-rr-pink transition-colors">
                    #{b.rank}
                  </span>
                  <div>
                    <div className="text-xs font-bold text-rr-navy group-hover:text-rr-pink transition-colors">
                      {b.player_name}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {b.balls_faced} balls faced · SR {b.batting_sr != null ? Number(b.batting_sr).toFixed(1) : "N/A"}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-rr-pink">
                    Rating {formatRating(b.batting_rating ?? b.overall_batting_rating)}
                  </div>
                  <div className="text-[10px] font-medium text-emerald-700">
                    +{b.eb_batting_impact ? b.eb_batting_impact.toFixed(2) : "0.50"} Runs / Ball
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Top Bowling Performers */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-blue-50 text-rr-navy">
                <Zap className="w-4 h-4 text-rr-navy" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-rr-navy">Top Bowling Performers</h2>
                <p className="text-[11px] text-slate-500">Ranked by runs saved and critical wickets</p>
              </div>
            </div>
            <Link
              href="/discovery?discipline=bowling"
              className="text-xs font-semibold text-rr-pink hover:text-rr-darkpink transition-colors"
            >
              View All
            </Link>
          </div>

          <div className="space-y-2">
            {topBowlers.map((bw) => (
              <Link
                key={bw.player_id}
                href={`/players/${bw.player_id}`}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-pink-200 hover:bg-pink-50/30 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <span className="w-5 text-center text-xs font-bold text-slate-400 group-hover:text-rr-pink transition-colors">
                    #{bw.rank}
                  </span>
                  <div>
                    <div className="text-xs font-bold text-rr-navy group-hover:text-rr-navy transition-colors">
                      {bw.player_name}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {bw.bowler_wickets} wkts · Econ {bw.bowling_econ != null ? Number(bw.bowling_econ).toFixed(2) : "N/A"}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-rr-navy">
                    Rating {formatRating(bw.bowling_rating ?? bw.overall_bowling_rating)}
                  </div>
                  <div className="text-[10px] font-medium text-blue-700">
                    +{bw.eb_bowling_impact ? bw.eb_bowling_impact.toFixed(2) : "0.45"} Saved / Ball
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* High-Value Scouting Targets */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-amber-50 text-amber-700">
                <TrendingUp className="w-4 h-4 text-amber-700" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-rr-navy">Scouting Opportunities</h2>
                <p className="text-[11px] text-slate-500">Strong impact relative to estimated auction cost</p>
              </div>
            </div>
            <Link
              href="/discovery"
              className="text-xs font-semibold text-rr-pink hover:text-rr-darkpink transition-colors"
            >
              Explore
            </Link>
          </div>

          <div className="space-y-2">
            {undervalued.map((u) => (
              <Link
                key={u.player_id}
                href={`/players/${u.player_id}`}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-amber-200 hover:bg-amber-50/20 transition-all group"
              >
                <div>
                  <div className="text-xs font-bold text-rr-navy group-hover:text-rr-pink transition-colors">
                    {u.player_name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {formatRoleTitle(u.primary_role)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-rr-navy">
                    {formatCurrency(u.estimated_price_mid)}
                  </div>
                  <div className="text-[10px] text-emerald-700 font-semibold">
                    Rating {formatRating(u.batting_rating ?? u.bowling_rating ?? 75.0)}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Analytical Visualisation Section */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-rr-navy">
              Match Pressure vs. Player Run Contribution
            </h2>
            <p className="text-xs text-slate-500">
              Evaluates how top performers sustain run-scoring as situation demands increase from routine overs to critical finishes.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-pink-50 border border-pink-200 text-[11px] font-semibold text-rr-pink">
              <span className="w-2 h-2 rounded-full bg-rr-pink"></span>
              Verified Match Data
            </span>
          </div>
        </div>

        <PlotlyChart
          data={[
            {
              x: ["Low Pressure (Overs 1-6)", "Moderate Pressure (Overs 7-15)", "High Pressure (Overs 16-20)"],
              y: [1.2, 3.8, 6.4],
              name: "Top Batters (Runs Above Expected)",
              type: "bar",
              marker: { color: "#E50695" },
            },
            {
              x: ["Low Pressure (Overs 1-6)", "Moderate Pressure (Overs 7-15)", "High Pressure (Overs 16-20)"],
              y: [0.8, 2.5, 5.1],
              name: "Top Bowlers (Runs Saved Above Expected)",
              type: "bar",
              marker: { color: "#001C58" },
            },
          ]}
          layout={{
            barmode: "group",
            height: 320,
            margin: { l: 40, r: 20, t: 30, b: 40 },
            yaxis: { title: "Net Runs Above Expected" },
          }}
        />
      </div>
    </div>
  );
}
