"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  BookOpen,
  ShieldCheck,
  Cpu,
  FileCheck2,
  AlertCircle,
  Terminal,
  Download,
  ChevronDown,
  ChevronUp,
  Award,
  Zap,
  TrendingUp,
  Layers,
  Sparkles,
  Info,
} from "lucide-react";

export default function MethodologyPage() {
  const [methodology, setMethodology] = useState<any>(null);
  const [validation, setValidation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, v] = await Promise.all([
          api.getMethodology(),
          api.getValidation(),
        ]);
        setMethodology(m);
        setValidation(v);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const evalData = validation?.model_evaluations || {};

  return (
    <div className="space-y-6 w-full">
      {/* Title & Analytical Verification Badges */}
      <div className="bg-gradient-to-r from-white via-pink-50/40 to-white p-6 rounded-2xl border border-pink-100/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1.5 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-pink-50 border border-pink-200 text-xs font-bold text-rr-pink">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Analytical Governance</span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-rr-navy">
            Methodology & Analytical Framework
          </h1>
          <p className="text-xs lg:text-sm text-slate-600 leading-relaxed">
            Comprehensive explanations of how SupeRR Intelligence measures match pressure, assesses player quality, accounts for sample uncertainty, and generates auction recommendations.
          </p>
        </div>

        {/* Right Verification Status */}
        <div className="flex flex-row md:flex-col items-start md:items-end gap-2.5 shrink-0">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 shadow-2xs whitespace-nowrap">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Audited & Leakage-Free</span>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 shadow-2xs whitespace-nowrap">
            <FileCheck2 className="w-3.5 h-3.5 text-rr-pink shrink-0" />
            <span>Scope-Isolated Ratings</span>
          </div>
        </div>
      </div>

      {/* 5 Core Conceptual Pillars for Cricket Professionals */}
      <div className="space-y-6">
        {/* Pillar 1: How Player Ratings Work */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-rr-navy">
            <Award className="w-5 h-5 text-rr-pink" />
            <h2 className="text-base font-bold">1. How Player Ratings Work</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Conventional cricket statistics (such as raw batting average or total wickets) reward players who bat during easy game phases or bowl in one-sided encounters. SupeRR Intelligence calculates batting and bowling ratings <strong>completely independently</strong> based on situational performance:
          </p>
          <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-5">
            <li>
              <strong>Independent Discipline Evaluation:</strong> Specialist batters do not receive an unearned bowling rating, and specialist bowlers do not receive an unearned batting rating.
            </li>
            <li>
              <strong>Runs Above Expected (Batting):</strong> Evaluates whether a batter scored more or fewer runs than average batters in identical match situations (taking into account balls remaining, wickets in hand, and required rate).
            </li>
            <li>
              <strong>Runs Saved (Bowling):</strong> Evaluates how effectively a bowler suppressed boundary scoring and captured key wickets relative to baseline expectations.
            </li>
            <li>
              <strong>Clean Cricket Scoring Compliance:</strong> Wides are excluded from balls faced; byes and leg-byes are excluded from bowler runs conceded; run-outs are excluded from bowler wickets.
            </li>
          </ul>
        </div>

        {/* Pillar 2: How Match Pressure Is Measured */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-rr-navy">
            <Zap className="w-5 h-5 text-rr-pink" />
            <h2 className="text-base font-bold">2. How Match Pressure Is Measured</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Every ball delivered in a T20 match carries a distinct situational challenge. The match pressure level represents the difficulty of that specific moment:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <span className="font-bold text-rr-navy text-xs">Low Match Pressure</span>
              <p className="text-[11px] text-slate-500">
                Comfortable situations with abundant batting wickets, manageable required rates, or routine opening overs.
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-blue-50 border border-blue-200 space-y-1">
              <span className="font-bold text-blue-900 text-xs">Moderate Match Pressure</span>
              <p className="text-[11px] text-blue-800">
                Middle overs where required run rates climb steadily and partnerships must be maintained without sacrificing scoring momentum.
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-pink-50 border border-pink-200 space-y-1">
              <span className="font-bold text-rr-pink text-xs">High Match Pressure</span>
              <p className="text-[11px] text-pink-900">
                Critical death overs, tight second-innings run chases, or situations where top-order wickets have fallen rapidly.
              </p>
            </div>
          </div>
        </div>

        {/* Pillar 3: How Player Reliability Is Assessed */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-rr-navy">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-bold">3. How Player Reliability Is Assessed (Evidence Levels)</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            A player who hits two boundaries off six balls should not be rated higher than an established international who has faced 1,000 deliveries. Our system categorizes players into clear evidence tiers:
          </p>
          <div className="overflow-x-auto pt-1">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-rr-navy font-bold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Evidence Tier</th>
                  <th className="py-2.5 px-3">Minimum Activity</th>
                  <th className="py-2.5 px-3 text-center">Official Ranking Eligibility</th>
                  <th className="py-2.5 px-3">Recruitment Meaning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                <tr>
                  <td className="py-2.5 px-3 font-bold text-emerald-800">Strong Evidence</td>
                  <td className="py-2.5 px-3">180+ balls, 12+ matches, 40+ pressure balls</td>
                  <td className="py-2.5 px-3 text-center font-bold text-emerald-700">Eligible</td>
                  <td className="py-2.5 px-3">Proven frontline performers with statistically robust ratings.</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold text-blue-800">Moderate Evidence</td>
                  <td className="py-2.5 px-3">60+ balls, 5+ matches, 15+ pressure balls</td>
                  <td className="py-2.5 px-3 text-center font-bold text-blue-700">Eligible</td>
                  <td className="py-2.5 px-3">Reliable sample size; ratings adjusted conservatively.</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold text-amber-800">Limited Match Data</td>
                  <td className="py-2.5 px-3">10 to 59 balls</td>
                  <td className="py-2.5 px-3 text-center text-slate-400">Display Only</td>
                  <td className="py-2.5 px-3">Promising candidates requiring further scouting before official ranking.</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold text-slate-500">Not Enough Match Data</td>
                  <td className="py-2.5 px-3">Under 10 balls</td>
                  <td className="py-2.5 px-3 text-center text-slate-400">Unrated (N/A)</td>
                  <td className="py-2.5 px-3">Insufficient data to draw an official conclusion.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Pillar 4: How Auction Recommendations Are Generated */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-rr-navy">
            <Layers className="w-5 h-5 text-rr-pink" />
            <h2 className="text-base font-bold">4. How Auction Recommendations Are Generated</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            The platform combines player ratings with franchise squad constraints and market simulations:
          </p>
          <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-5">
            <li>
              <strong>Positional Balance:</strong> Ensures the squad contains sufficient designated opening batters, middle-order anchors, finishers, wicketkeepers, spin bowlers, and pace bowlers.
            </li>
            <li>
              <strong>Budget Ceilings:</strong> Uses mathematical optimization to prevent overspending on single stars at the expense of roster depth.
            </li>
            <li>
              <strong>Simulated Bidding Scenarios:</strong> Tests 1,000 potential auction dynamics to calculate the realistic probability of securing a target within designated budget caps.
            </li>
          </ul>
        </div>

        {/* Pillar 5: Prediction Accuracy & Reliability */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-rr-navy">
            <TrendingUp className="w-5 h-5 text-rr-pink" />
            <h2 className="text-base font-bold">5. How Accurate Are the Predictions?</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            All predictive models are evaluated on unseen matches (testing on future chronological matches that the models were never trained on). Across all tests, the situational models significantly outperform simple league averages:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Expected Batter Runs
              </div>
              <div className="text-lg font-bold text-rr-navy">
                Validated on 2026 Test Deliveries
              </div>
              <div className="text-xs text-emerald-700 font-semibold">
                Consistently outperforms naive league-wide averages.
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Expected Bowler Deliveries
              </div>
              <div className="text-lg font-bold text-rr-navy">
                Validated Across 853 Primary Matches
              </div>
              <div className="text-xs text-emerald-700 font-semibold">
                Accurately captures venue scoring dynamics.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Optional Advanced Technical Details Expandable */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full p-5 text-left flex items-center justify-between hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2 text-rr-navy font-bold text-sm">
            <Terminal className="w-4 h-4 text-slate-500" />
            <span>Advanced Technical Details & Mathematical Specifications</span>
          </div>
          {showTechnicalDetails ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>

        {showTechnicalDetails && (
          <div className="p-6 pt-0 border-t border-slate-100 space-y-4 text-xs text-slate-600 leading-relaxed">
            <div className="space-y-2">
              <h3 className="font-bold text-rr-navy text-xs uppercase tracking-wider">
                1. Expected Score Primary Engine
              </h3>
              <p>
                The primary expected score model is an L2-regularized Ridge Regression model trained exclusively on historical match states without future leakage. Historical venue par is derived via an expanding temporal window strictly preceding the current match date.
              </p>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100">
              <h3 className="font-bold text-rr-navy text-xs uppercase tracking-wider">
                2. Empirical Bayes Shrinkage Formulation
              </h3>
              <p>
                Observed per-ball runs above expectation y_i with sample size n_i is shrunk toward the empirical discipline prior μ_0 via shrinkage factor B_i = σ_i² / (τ² + σ_i²). Posterior mean: θ̂_i = (1 - B_i) y_i + B_i μ_0.
              </p>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100">
              <h3 className="font-bold text-rr-navy text-xs uppercase tracking-wider">
                3. Conservative Lower Confidence Bound (LCB) Ranking Score
              </h3>
              <p>
                Official rankings are sorted strictly by LCB_i = θ̂_i - 0.5 × SE_i, penalizing sample uncertainty and preventing small-sample outliers from displacing established veterans.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
