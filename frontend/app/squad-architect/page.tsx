"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { formatPlayerRole } from "@/lib/formatRole";
import {
  formatCurrency,
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import {
  Layers,
  Sparkles,
  Shield,
  Zap,
  TrendingDown,
  RefreshCw,
  AlertTriangle,
  UserX,
  Lock,
  ArrowRight,
  CheckCircle2,
  DollarSign,
  Users,
  ChevronRight,
  Info,
} from "lucide-react";

export default function SquadArchitectPage() {
  const [budgetRemaining, setBudgetRemaining] = useState(450000000); // 45 Cr INR
  const [playersToAcquire, setPlayersToAcquire] = useState(5);
  const [strategyTab, setStrategyTab] = useState<"balanced" | "upside" | "risk_controlled">("balanced");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [whatIfDelta, setWhatIfDelta] = useState<any>(null);

  async function handleOptimize() {
    setLoading(true);
    setWhatIfDelta(null);
    try {
      const res = await api.optimizeSquad({
        budget_remaining: budgetRemaining,
        players_to_acquire: playersToAcquire,
        strategy: strategyTab,
      });
      setResult(res);
    } catch (err) {
      console.error("Optimization failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleExcludeWhatIf(pid: number) {
    if (!result) return;
    setLoading(true);
    try {
      const baseScenario = {
        budget_remaining: budgetRemaining,
        players_to_acquire: playersToAcquire,
        strategy: strategyTab,
      };
      const res = await api.whatIfSquad({
        base_scenario: baseScenario,
        exclude_player_id: pid,
      });
      setWhatIfDelta(res.delta);
      if (res.updated_solution) {
        setResult({
          status: res.status,
          strategies: {
            ...result.strategies,
            [strategyTab]: res.updated_solution,
          },
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const currentSquad = result?.strategies?.[strategyTab]?.players || [];
  const totalSpend = result?.strategies?.[strategyTab]?.total_spend || 0;
  const remPurse = budgetRemaining - totalSpend;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-rr-navy flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-rr-pink" />
            Squad Architect & Recruitment Optimization
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Build a mathematically optimized tournament squad balancing budget ceilings, positional coverage, and verified match ratings.
          </p>
        </div>
      </div>

      {/* Recruitment Parameters & Strategy Selector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Budget Setting */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-rr-navy uppercase tracking-wider">
              Available Auction Budget: {formatCurrency(budgetRemaining)}
            </label>
            <input
              type="range"
              min={150000000}
              max={900000000}
              step={25000000}
              value={budgetRemaining}
              onChange={(e) => setBudgetRemaining(Number(e.target.value))}
              className="w-full accent-rr-pink cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400 font-medium">
              <span>₹15 Cr</span>
              <span>₹50 Cr</span>
              <span>₹90 Cr</span>
            </div>
          </div>

          {/* Slots to Acquire */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-rr-navy uppercase tracking-wider">
              Remaining Squad Slots to Fill: {playersToAcquire} Players
            </label>
            <input
              type="range"
              min={2}
              max={8}
              value={playersToAcquire}
              onChange={(e) => setPlayersToAcquire(Number(e.target.value))}
              className="w-full accent-rr-pink cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400 font-medium">
              <span>2 Slots</span>
              <span>5 Slots</span>
              <span>8 Slots</span>
            </div>
          </div>

          {/* Optimization Trigger */}
          <div className="flex items-end">
            <button
              onClick={handleOptimize}
              disabled={loading}
              className="w-full btn-rr-primary py-3"
            >
              {loading ? (
                <span>Finding Best Combination...</span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Recommended Squad</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Strategy Selection Pills */}
        <div className="pt-4 border-t border-slate-100 flex items-center gap-3">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Scouting Philosophy:
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setStrategyTab("balanced")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                strategyTab === "balanced"
                  ? "bg-rr-pink text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Balanced Roster
            </button>
            <button
              onClick={() => setStrategyTab("upside")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                strategyTab === "upside"
                  ? "bg-rr-pink text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              High-Impact Upside
            </button>
            <button
              onClick={() => setStrategyTab("risk_controlled")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                strategyTab === "risk_controlled"
                  ? "bg-rr-pink text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Risk-Controlled Consistency
            </button>
          </div>
        </div>
      </div>

      {/* Optimization Result Status Banner */}
      {result && (
        <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-emerald-900 font-extrabold text-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>Best Available Squad Found</span>
            </div>
            <p className="text-xs text-emerald-800">
              The selected combination meets your budget and squad requirements while maximising the team&apos;s overall strength.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs shrink-0">
            <div>
              <span className="text-slate-500">Projected Spend: </span>
              <strong className="text-rr-navy font-bold">{formatCurrency(totalSpend)}</strong>
            </div>
            <div>
              <span className="text-slate-500">Remaining Budget: </span>
              <strong className="text-emerald-700 font-bold">{formatCurrency(remPurse)}</strong>
            </div>
          </div>
        </div>
      )}

      {/* What-If Replacement Notification */}
      {whatIfDelta && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 shadow-xs flex items-center justify-between text-xs text-blue-900">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-600 shrink-0" />
            <span>
              <strong>Replacement Analysis:</strong> Evaluated replacement candidate. Net budget change:{" "}
              <strong>{formatCurrency(whatIfDelta.spend_diff || 0)}</strong>.
            </span>
          </div>
          <button
            onClick={() => setWhatIfDelta(null)}
            className="text-xs text-blue-700 hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Recommended Squad Table */}
      {currentSquad.length > 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-xs font-bold text-rr-navy uppercase tracking-wider">
              Recommended Player Signings ({currentSquad.length} Players)
            </h2>
            <span className="text-xs font-semibold text-slate-500">
              Budget Utilization: {((totalSpend / budgetRemaining) * 100).toFixed(1)}%
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-white text-rr-navy font-bold border-b-2 border-pink-100">
                <tr>
                  <th className="py-3 px-4">Player</th>
                  <th className="py-3 px-4">Tactical Position</th>
                  <th className="py-3 px-4 text-right">Estimated Auction Price</th>
                  <th className="py-3 px-4 text-center">Batting Rating</th>
                  <th className="py-3 px-4 text-center">Bowling Rating</th>
                  <th className="py-3 px-4 text-center">Evidence Level</th>
                  <th className="py-3 px-4 text-right">What-If Alternative</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {currentSquad.map((p: any) => {
                  const ev = formatEvidenceLevel(p.confidence_tier);
                  const batRating = p.batting_rating ?? p.overall_batting_rating;
                  const bowlRating = p.bowling_rating ?? p.overall_bowling_rating;

                  return (
                    <tr key={p.player_id} className="hover:bg-pink-50/20 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-bold text-rr-navy text-xs">{p.player_name}</span>
                        <div className="text-[10px] text-slate-500">
                          {p.is_overseas ? "Overseas Signing" : "Domestic Player"}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-600">
                        {formatRoleTitle(p.primary_role)}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-rr-navy">
                        {formatCurrency(p.estimated_price || p.estimated_price_mid)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {batRating !== null && batRating !== undefined ? (
                          <span className="font-bold text-rr-pink">{formatRating(batRating)}</span>
                        ) : (
                          <span className="text-slate-400 text-[10px]">N/A</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {bowlRating !== null && bowlRating !== undefined ? (
                          <span className="font-bold text-rr-navy">{formatRating(bowlRating)}</span>
                        ) : (
                          <span className="text-slate-400 text-[10px]">N/A</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${ev.badgeClass}`}
                        >
                          {ev.label}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleExcludeWhatIf(p.player_id)}
                          className="px-2.5 py-1 rounded bg-slate-100 text-slate-600 hover:bg-pink-50 hover:text-rr-pink text-[11px] font-semibold transition-colors"
                        >
                          Exclude & Re-solve
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400 text-xs space-y-2">
          <Users className="w-8 h-8 text-slate-300 mx-auto" />
          <div className="font-semibold text-slate-600">No Squad Configured Yet</div>
          <p>Click &quot;Generate Recommended Squad&quot; above to calculate the optimal player combination.</p>
        </div>
      )}
    </div>
  );
}
