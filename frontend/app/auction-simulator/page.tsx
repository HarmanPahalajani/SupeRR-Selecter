"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatPlayerRole } from "@/lib/formatRole";
import {
  formatCurrency,
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import {
  Gavel,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  GitBranch,
  ShieldCheck,
  CheckCircle2,
  DollarSign,
  ArrowRight,
  Sparkles,
  Info,
} from "lucide-react";

export default function AuctionSimulatorPage() {
  const [pool, setPool] = useState<any[]>([]);
  const [selectedPlayerId, setSelectedPlayerId] = useState<number | null>(null);
  const [bidCap, setBidCap] = useState(35000000); // 3.5 Cr INR
  const [userBudget, setUserBudget] = useState(120000000); // 12 Cr INR
  const [inflation, setInflation] = useState(1.0);
  const [simResult, setSimResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadPool() {
      try {
        const res = await api.getAuctionPool();
        setPool(res.pool || []);
        if (res.pool?.length > 0) {
          setSelectedPlayerId(res.pool[0].player_id);
          setBidCap(res.pool[0].price_mid);
        }
      } catch (err) {
        console.error("Failed to load auction pool:", err);
      }
    }
    loadPool();
  }, []);

  async function handleSimulate() {
    if (!selectedPlayerId) return;
    setLoading(true);
    try {
      const res = await api.simulateAuction({
        target_player_id: selectedPlayerId,
        bid_cap: bidCap,
        user_budget: userBudget,
        n_simulations: 1000,
        inflation_factor: inflation,
      });
      setSimResult(res);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setLoading(false);
    }
  }

  const selectedPlayer = pool.find((p) => p.player_id === selectedPlayerId);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-rr-navy flex items-center gap-2.5">
            <Gavel className="w-6 h-6 text-rr-pink" />
            Auction Decision Simulator
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Simulate realistic auction scenarios to establish disciplined bid limits, calculate acquisition likelihood, and evaluate backup recruitment options.
          </p>
        </div>
      </div>

      {/* Simulator Control Card */}
      <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs space-y-5">
        <h2 className="text-xs font-bold text-rr-navy uppercase tracking-wider">
          Auction Setup & Valuation Parameters
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {/* Target Player Select */}
          <div>
            <label className="text-xs font-semibold text-slate-600 block mb-1.5">
              Target Player:
            </label>
            <select
              value={selectedPlayerId || ""}
              onChange={(e) => {
                const pid = Number(e.target.value);
                setSelectedPlayerId(pid);
                const pl = pool.find((p) => p.player_id === pid);
                if (pl) setBidCap(pl.price_mid);
              }}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-rr-navy focus:outline-none focus:border-rr-pink"
            >
              {pool.map((p) => (
                <option key={p.player_id} value={p.player_id}>
                  {p.player_name} ({formatRoleTitle(p.primary_role)})
                </option>
              ))}
            </select>
          </div>

          {/* Our Bid Cap */}
          <div>
            <label className="text-xs font-semibold text-slate-600 block mb-1.5">
              Suggested Maximum Bid:
            </label>
            <input
              type="number"
              step="5000000"
              value={bidCap}
              onChange={(e) => setBidCap(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-rr-navy focus:outline-none focus:border-rr-pink"
            />
            <div className="text-[11px] font-semibold text-rr-pink mt-1">
              Cap: {formatCurrency(bidCap)}
            </div>
          </div>

          {/* Market Inflation Multiplier */}
          <div>
            <label className="text-xs font-semibold text-slate-600 block mb-1.5">
              Auction Room Demand:
            </label>
            <select
              value={inflation}
              onChange={(e) => setInflation(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-rr-navy focus:outline-none focus:border-rr-pink"
            >
              <option value={0.85}>Favourable Buyer Market (0.85x)</option>
              <option value={1.0}>Standard Market Demand (1.0x)</option>
              <option value={1.25}>Competitive Bidding War (1.25x)</option>
              <option value={1.5}>Intense Rivalry Demand (1.5x)</option>
            </select>
          </div>

          {/* Action Button */}
          <div className="flex items-end">
            <button
              onClick={handleSimulate}
              disabled={loading}
              className="w-full btn-rr-primary py-2.5"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Simulating Scenarios...</span>
                </>
              ) : (
                <>
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Simulate Auction Scenarios</span>
                </>
              )}
            </button>
          </div>
        </div>

        {selectedPlayer && (
          <div className="p-3.5 rounded-lg bg-pink-50/50 border border-pink-100 flex items-center justify-between text-xs text-slate-700">
            <div>
              Estimated Valuation Range:{" "}
              <strong className="text-rr-navy">
                {formatCurrency(selectedPlayer.price_low)} – {formatCurrency(selectedPlayer.price_high)}
              </strong>{" "}
              (Target Anchor:{" "}
              <strong className="text-rr-pink font-bold">{formatCurrency(selectedPlayer.price_mid)}</strong>)
            </div>
            <div className="text-[11px] text-slate-500 font-medium">
              Based on historical franchise auction patterns
            </div>
          </div>
        )}
      </div>

      {/* Simulation Results */}
      {simResult && (
        <div className="space-y-6">
          {/* Key Simulation KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1 hover:border-pink-200 transition-colors">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Chance of Acquiring Player at Cap
              </div>
              <div className="text-2xl lg:text-3xl font-extrabold text-rr-pink tracking-tight">
                {(simResult.win_probability * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-500">
                Based on 1,000 simulated auction scenarios.
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1 hover:border-pink-200 transition-colors">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Expected Purchase Price if Won
              </div>
              <div className="text-2xl lg:text-3xl font-extrabold text-rr-navy tracking-tight">
                {formatCurrency(simResult.expected_expenditure_if_won)}
              </div>
              <div className="text-[11px] text-slate-500">
                Estimated average winning hammer bid
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1 hover:border-pink-200 transition-colors">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Risk of Exceeding Cap
              </div>
              <div className="text-2xl lg:text-3xl font-extrabold text-amber-700 tracking-tight">
                {(simResult.risk_of_exceeding_budget * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-500">
                Likelihood that rival bids exceed ceiling
              </div>
            </div>
          </div>

          {/* Bid Sensitivity Chart */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
            <h2 className="text-sm font-bold text-rr-navy">
              Bid Sensitivity Curve: Maximum Bid vs Acquisition Likelihood
            </h2>
            <p className="text-xs text-slate-500">
              Evaluates how the likelihood of winning this player increases as you adjust your maximum allocated bid ceiling.
            </p>

            <PlotlyChart
              data={[
                {
                  x: simResult.bid_curve.map((b: any) => b.bid_amount / 10000000),
                  y: simResult.bid_curve.map((b: any) => b.win_probability * 100),
                  mode: "lines+markers",
                  type: "scatter",
                  line: { color: "#E50695", width: 3 },
                  marker: { size: 6, color: "#E50695" },
                },
              ]}
              layout={{
                xaxis: { title: "Maximum Bid Limit (₹ Crores)" },
                yaxis: { title: "Simulated Acquisition Chance (%)", range: [0, 105] },
                height: 280,
              }}
            />
          </div>

          {/* Fallback Decision Tree */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-rr-pink" />
              <div>
                <h2 className="text-sm font-bold text-rr-navy">
                  Alternative Targets (If Designated Bid Ceiling Is Exceeded)
                </h2>
                <p className="text-xs text-slate-500">
                  Pre-screened tactical replacements sharing similar playing roles, ranked by verified match performance.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
              {simResult.replacement_tree.map((rep: any, idx: number) => {
                const ev = formatEvidenceLevel(rep.confidence_tier);
                return (
                  <div
                    key={rep.player_id}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 hover:border-pink-200 transition-colors"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-400">Option #{idx + 1}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${ev.badgeClass}`}>
                        {ev.label}
                      </span>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-rr-navy">
                        {rep.player_name}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {formatRoleTitle(rep.primary_role)}
                      </div>
                    </div>
                    <div className="text-xs font-bold text-rr-pink pt-1 border-t border-slate-200">
                      Est. Price: {formatCurrency(rep.estimated_price)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
