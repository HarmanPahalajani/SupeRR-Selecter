"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Flame, Award, Zap, ArrowRight, Info, ShieldCheck } from "lucide-react";

interface PressureBatterItem {
  player_id: number;
  player_name: string;
  pressure_rank: number;
  hp_risk_adjusted_impact: number;
  hp_balls: number;
  hp_matches: number;
  hp_raw_rae_per_100?: number;
}

interface PressureBowlerItem {
  player_id: number;
  player_name: string;
  pressure_rank: number;
  hp_risk_adjusted_impact: number;
  hp_overs: number;
  hp_matches: number;
  hp_raw_runs_saved_per_6?: number;
}

export function PressureOverviewCards() {
  const [topBatters, setTopBatters] = useState<PressureBatterItem[]>([]);
  const [topBowlers, setTopBowlers] = useState<PressureBowlerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchLeaders() {
      try {
        const [batRes, bowlRes] = await Promise.all([
          api.getPressureLeaderboard({ scope: "IPL_T20I", context: "ALL", limit: 5 }),
          api.getPressureBowlersLeaderboard({ scope: "IPL_T20I", context: "ALL", limit: 5 }),
        ]);
        if (isMounted) {
          if (batRes && Array.isArray(batRes.players)) {
            setTopBatters(batRes.players.slice(0, 5));
          }
          if (bowlRes && Array.isArray(bowlRes.records)) {
            setTopBowlers(bowlRes.records.slice(0, 5));
          }
        }
      } catch (err: any) {
        if (isMounted) {
          console.error("Failed to load pressure overview leaders:", err);
          setError("Unable to load pressure overview");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchLeaders();
    return () => {
      isMounted = false;
    };
  }, []);

  // Compute maximum values for proportional bar scaling
  const maxBatCrai = Math.max(...topBatters.map((b) => b.hp_risk_adjusted_impact || 0), 30);
  const maxBowlCrai = Math.max(...topBowlers.map((b) => b.hp_risk_adjusted_impact || 0), 1.3);

  return (
    <section className="space-y-4" aria-label="Pressure Performance Overview">
      {/* Section Header */}
      <div className="pb-2 border-b border-slate-200">
        <h2 className="text-xl font-extrabold tracking-tight text-rr-navy">
          Pressure Performance Overview
        </h2>
        <p className="text-xs text-slate-500">
          Top 5 qualified performers delivering verified execution under extreme defensive and chase demands (IPL &amp; T20I).
        </p>
      </div>

      {/* Two Independent Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CARD A: Batting Under Pressure */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4 hover:border-pink-200 transition-colors">
          <div className="space-y-3">
            {/* Card Header */}
            <div className="flex items-center justify-between pb-3 border-b border-pink-100/70">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-pink-50 text-rr-pink border border-pink-100">
                  <Flame className="w-4 h-4 text-rr-pink" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-rr-navy flex items-center gap-1.5">
                    <span>Batting Under Pressure</span>
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-pink-100 text-rr-pink">
                      Top 5
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Ranked by Conservative Risk-Adjusted Impact (CRAI)
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  RAE / 100b
                </span>
              </div>
            </div>

            {/* Explanation / Units Note */}
            <div className="text-[11px] text-slate-600 bg-pink-50/50 border border-pink-100 rounded-lg p-2.5 flex items-start gap-2">
              <Info className="w-3.5 h-3.5 text-rr-pink shrink-0 mt-0.5" />
              <span>
                <strong>Metric:</strong> Runs Above Expected per 100 pressure balls faced ($RAE/100b$), penalized for sample uncertainty via Empirical Bayes ($k=0.50$).
              </span>
            </div>

            {/* Horizontal Bar Chart Rows */}
            {loading ? (
              <div className="py-12 text-center text-xs text-slate-400">
                Loading batting pressure leaders...
              </div>
            ) : topBatters.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                No qualified batting pressure records found.
              </div>
            ) : (
              <div className="space-y-3 pt-1">
                {topBatters.map((batter, idx) => {
                  const crai = Number(batter.hp_risk_adjusted_impact || 0);
                  const barWidthPct = Math.min(100, Math.max(12, (crai / maxBatCrai) * 100));
                  const balls = Math.round(batter.hp_balls || 0);
                  const matches = batter.hp_matches || 0;

                  return (
                    <div key={batter.player_id} className="group">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="w-5 h-5 rounded-full bg-pink-100 text-rr-pink font-extrabold text-[10px] flex items-center justify-center shrink-0">
                            #{batter.pressure_rank || idx + 1}
                          </span>
                          <Link
                            href={`/players/${batter.player_id}`}
                            className="font-bold text-rr-navy hover:text-rr-pink transition-colors truncate"
                          >
                            {batter.player_name}
                          </Link>
                          <span className="text-[11px] text-slate-400 shrink-0">
                            · {balls}b ({matches}m)
                          </span>
                        </div>
                        <div className="flex items-baseline gap-1 shrink-0 pl-2">
                          <span className="font-extrabold text-rr-pink text-xs">
                            +{crai.toFixed(1)}
                          </span>
                          <span className="text-[10px] text-slate-400 font-medium">
                            RAE/100b
                          </span>
                        </div>
                      </div>

                      {/* Visual Bar Container */}
                      <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden p-0.5 border border-slate-200/60">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-pink-500 to-rr-pink transition-all duration-500 group-hover:brightness-110"
                          style={{ width: `${barWidthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Card Footer Link */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              Min. threshold: 20 pressure balls in scope
            </span>
            <Link
              href="/discovery?tab=pressure"
              className="inline-flex items-center gap-1 text-xs font-bold text-rr-pink hover:text-rr-darkpink transition-colors"
            >
              <span>View Full Batting Board</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* CARD B: Bowling Under Pressure */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4 hover:border-blue-200 transition-colors">
          <div className="space-y-3">
            {/* Card Header */}
            <div className="flex items-center justify-between pb-3 border-b border-blue-100/70">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-blue-50 text-rr-navy border border-blue-100">
                  <Zap className="w-4 h-4 text-rr-navy" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-rr-navy flex items-center gap-1.5">
                    <span>Bowling Under Pressure</span>
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-100 text-rr-navy">
                      Top 5
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Ranked by Run Prevention CRAI ($k=0.50$)
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  Saved / 6b
                </span>
              </div>
            </div>

            {/* Explanation / Units Note */}
            <div className="text-[11px] text-slate-600 bg-blue-50/50 border border-blue-100 rounded-lg p-2.5 flex items-start gap-2">
              <Info className="w-3.5 h-3.5 text-rr-navy shrink-0 mt-0.5" />
              <span>
                <strong>Metric:</strong> Runs Saved per 6 pressure balls ($Saved/6b$) against match context expectation, penalized for sample uncertainty via Empirical Bayes ($k=0.50$).
              </span>
            </div>

            {/* Horizontal Bar Chart Rows */}
            {loading ? (
              <div className="py-12 text-center text-xs text-slate-400">
                Loading bowling pressure leaders...
              </div>
            ) : topBowlers.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                No qualified bowling pressure records found.
              </div>
            ) : (
              <div className="space-y-3 pt-1">
                {topBowlers.map((bowler, idx) => {
                  const crai = Number(bowler.hp_risk_adjusted_impact || 0);
                  const barWidthPct = Math.min(100, Math.max(12, (crai / maxBowlCrai) * 100));
                  const overs = Number(bowler.hp_overs || 0).toFixed(1);
                  const matches = bowler.hp_matches || 0;

                  return (
                    <div key={bowler.player_id} className="group">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="w-5 h-5 rounded-full bg-blue-100 text-rr-navy font-extrabold text-[10px] flex items-center justify-center shrink-0">
                            #{bowler.pressure_rank || idx + 1}
                          </span>
                          <Link
                            href={`/players/${bowler.player_id}`}
                            className="font-bold text-rr-navy hover:text-blue-800 transition-colors truncate"
                          >
                            {bowler.player_name}
                          </Link>
                          <span className="text-[11px] text-slate-400 shrink-0">
                            · {overs} ov ({matches}m)
                          </span>
                        </div>
                        <div className="flex items-baseline gap-1 shrink-0 pl-2">
                          <span className="font-extrabold text-blue-700 text-xs">
                            +{crai.toFixed(2)}
                          </span>
                          <span className="text-[10px] text-slate-400 font-medium">
                            Saved/6b
                          </span>
                        </div>
                      </div>

                      {/* Visual Bar Container */}
                      <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden p-0.5 border border-slate-200/60">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-blue-700 to-rr-navy transition-all duration-500 group-hover:brightness-110"
                          style={{ width: `${barWidthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Card Footer Link */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              Min. threshold: 6 pressure overs in scope
            </span>
            <Link
              href="/discovery?discipline=bowling"
              className="inline-flex items-center gap-1 text-xs font-bold text-rr-navy hover:text-blue-800 transition-colors"
            >
              <span>View Full Bowling Board</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
