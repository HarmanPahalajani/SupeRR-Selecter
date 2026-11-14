"use client";

import React, { useState } from "react";
import { Flame, Target, Info, ShieldCheck, AlertCircle } from "lucide-react";

interface DonutData {
  title: string;
  discipline: "batting" | "bowling";
  matches: number;
  positiveMatches: number;
  negativeMatches: number;
  neutralMatches: number;
  positivePct: number | null;
  sampleUnits: string; // e.g. "499 balls faced" or "78.7 overs bowled"
  explanation: string;
  metricDefinition: string;
}

interface PressureBreakdownSectionProps {
  battingProfile: any;
  bowlingProfile: any;
}

export function PressureBreakdownSection({
  battingProfile,
  bowlingProfile,
}: PressureBreakdownSectionProps) {
  // Extract Batting Pressure Context (IPL_T20I_ALL)
  const batCtx = battingProfile?.contexts?.IPL_T20I_ALL || battingProfile || {};
  const batMatches = Number(batCtx.hp_matches || 0);
  const batBalls = Number(batCtx.hp_balls || 0);
  const batPosMatches = Number(batCtx.hp_positive_matches || 0);
  const batNegMatches = Number(batCtx.hp_negative_matches || 0);
  const batNeuMatches = Number(batCtx.hp_neutral_matches || 0);
  const batPosPct =
    batCtx.hp_positive_match_pct != null
      ? Number(batCtx.hp_positive_match_pct)
      : batMatches > 0
      ? (batPosMatches / batMatches) * 100
      : null;

  const hasBattingEvidence = batMatches > 0 && batBalls > 0;

  // Extract Bowling Pressure Profile
  const bowlProfile = bowlingProfile?.profile || bowlingProfile || {};
  const bowlMatches = Number(bowlProfile.hp_matches || bowlProfile.matches || 0);
  const bowlOvers = Number(bowlProfile.hp_overs || bowlProfile.pressure_overs || 0);
  const bowlPosMatches = Number(
    bowlProfile.hp_positive_matches || bowlProfile.positive_matches || 0
  );
  const bowlNegMatches = Number(
    bowlProfile.hp_negative_matches || bowlProfile.negative_matches || 0
  );
  const bowlNeuMatches = Number(
    bowlProfile.hp_neutral_matches || bowlProfile.neutral_matches || 0
  );
  const bowlPosPct =
    bowlProfile.hp_positive_match_pct != null
      ? Number(bowlProfile.hp_positive_match_pct)
      : bowlMatches > 0
      ? (bowlPosMatches / bowlMatches) * 100
      : null;

  const hasBowlingEvidence =
    Boolean(bowlProfile.has_pressure_data) && bowlMatches > 0 && bowlOvers > 0;

  return (
    <section className="space-y-4" aria-label="Pressure Performance Breakdown">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[11px] font-bold text-slate-700 mb-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Match-by-Match Reliability</span>
          </div>
          <h2 className="text-xl font-extrabold tracking-tight text-rr-navy">
            Pressure Performance Breakdown
          </h2>
          <p className="text-xs text-slate-500">
            Proportion of high-pressure appearances where the player generated net positive match value against situational expectations.
          </p>
        </div>
      </div>

      {/* Grid of Donut Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* BATTING DONUT CARD */}
        {hasBattingEvidence && batPosPct !== null ? (
          <DonutCard
            title="Batting Under Pressure"
            discipline="batting"
            matches={batMatches}
            positiveMatches={batPosMatches}
            negativeMatches={batNegMatches}
            neutralMatches={batNeuMatches}
            positivePct={batPosPct}
            sampleUnits={`${Math.round(batBalls)} balls faced`}
            explanation="A positive pressure match occurs when the batter scores more runs than situational baseline expectations (Runs Above Expected > 0)."
            metricDefinition="Positive Match: High-Pressure RAE > 0.0 runs. Non-positive matches combine neutral (RAE = 0) and below-par (RAE < 0) outcomes."
          />
        ) : (
          <EmptyDonutCard
            title="Batting Under Pressure"
            discipline="batting"
            reason="Not enough pressure-match evidence to generate this visualization."
            details="This player has not faced the qualifying threshold of high-pressure deliveries in the primary competition scope (IPL & T20I)."
          />
        )}

        {/* BOWLING DONUT CARD */}
        {hasBowlingEvidence && bowlPosPct !== null ? (
          <DonutCard
            title="Bowling Under Pressure"
            discipline="bowling"
            matches={bowlMatches}
            positiveMatches={bowlPosMatches}
            negativeMatches={bowlNegMatches}
            neutralMatches={bowlNeuMatches}
            positivePct={bowlPosPct}
            sampleUnits={`${bowlOvers.toFixed(1)} overs bowled`}
            explanation="A positive pressure match occurs when the bowler concedes fewer runs than the situational baseline expectation (Runs Saved > 0)."
            metricDefinition="Positive Match: High-Pressure Runs Saved > 0.0 runs. Non-positive matches combine neutral (Runs Saved = 0) and above-par concession (Runs Saved < 0) outcomes."
          />
        ) : (
          <EmptyDonutCard
            title="Bowling Under Pressure"
            discipline="bowling"
            reason="Not enough pressure-match evidence to generate this visualization."
            details="This player has not bowled the qualifying threshold of high-pressure overs in the primary competition scope (IPL & T20I)."
          />
        )}
      </div>
    </section>
  );
}

/**
 * Modern SVG Donut Chart Card
 */
function DonutCard({
  title,
  discipline,
  matches,
  positiveMatches,
  negativeMatches,
  neutralMatches,
  positivePct,
  sampleUnits,
  explanation,
  metricDefinition,
}: DonutData) {
  const [showTooltip, setShowTooltip] = useState(false);

  // SVG Donut Math
  const radius = 54;
  const circumference = 2 * Math.PI * radius; // ~339.29
  const clampedPct = Math.max(0, Math.min(100, positivePct ?? 0));
  const strokeDashoffset = circumference - (clampedPct / 100) * circumference;

  const nonPositiveMatches = matches - positiveMatches;
  const nonPositivePct = Math.max(0, 100 - clampedPct);

  const isBatting = discipline === "batting";
  const accentBadge = isBatting
    ? "bg-pink-50 text-rr-pink border-pink-200"
    : "bg-blue-50 text-rr-navy border-blue-200";

  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4 hover:border-slate-300 transition-colors">
      <div className="space-y-4">
        {/* Card Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div
              className={`p-2 rounded-xl border ${
                isBatting
                  ? "bg-pink-50 text-rr-pink border-pink-100"
                  : "bg-blue-50 text-rr-navy border-blue-100"
              }`}
            >
              {isBatting ? (
                <Flame className="w-4 h-4 text-rr-pink" />
              ) : (
                <Target className="w-4 h-4 text-rr-navy" />
              )}
            </div>
            <div>
              <h3 className="text-sm font-bold text-rr-navy">{title}</h3>
              <p className="text-[11px] text-slate-500">
                Match Outcome Consistency ({matches} appearances)
              </p>
            </div>
          </div>

          {/* Tooltip trigger */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowTooltip(!showTooltip)}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Metric definition"
            >
              <Info className="w-4 h-4" />
            </button>
            {showTooltip && (
              <div className="absolute right-0 top-6 z-30 w-64 p-2.5 bg-slate-900 text-white text-[11px] rounded-lg shadow-lg leading-relaxed border border-slate-700">
                {metricDefinition}
              </div>
            )}
          </div>
        </div>

        {/* Visual Content: Donut + Legend */}
        <div className="flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-6 pt-1">
          {/* SVG Donut Chart */}
          <div className="relative w-36 h-36 shrink-0 flex items-center justify-center">
            <svg
              className="w-full h-full transform -rotate-90"
              viewBox="0 0 140 140"
              aria-hidden="true"
            >
              {/* Background ring representing Non-positive */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                className="stroke-slate-200"
                strokeWidth="14"
                fill="transparent"
              />
              {/* Foreground arc representing Positive Impact */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                className="stroke-emerald-500 transition-all duration-700 ease-out"
                strokeWidth="14"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>

            {/* Donut Center Display */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-black text-rr-navy tracking-tight leading-none">
                {clampedPct.toFixed(1)}%
              </span>
              <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mt-1">
                Positive
              </span>
            </div>
          </div>

          {/* Legend & Exact Counts */}
          <div className="space-y-2.5 text-xs w-full">
            {/* Positive matches row */}
            <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50/60 border border-emerald-100">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500 shrink-0" />
                <span className="font-bold text-emerald-900">Positive Impact</span>
              </div>
              <div className="text-right">
                <span className="font-extrabold text-emerald-700">
                  {positiveMatches}
                </span>{" "}
                <span className="text-[11px] text-emerald-800/80">
                  ({clampedPct.toFixed(1)}%)
                </span>
              </div>
            </div>

            {/* Non-positive matches row */}
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200/80">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-slate-400 shrink-0" />
                <span className="font-semibold text-slate-700">Non-positive</span>
              </div>
              <div className="text-right">
                <span className="font-bold text-slate-600">
                  {nonPositiveMatches}
                </span>{" "}
                <span className="text-[11px] text-slate-400">
                  ({nonPositivePct.toFixed(1)}%)
                </span>
              </div>
            </div>

            {/* Sample Size Indicator */}
            <div className="text-[11px] text-slate-500 flex items-center justify-between px-1">
              <span>Sample Evidence:</span>
              <span className="font-medium text-slate-700">
                {matches} matches · {sampleUnits}
              </span>
            </div>
          </div>
        </div>

        {/* Short Plain-English Explanation */}
        <div className="text-[11px] text-slate-600 bg-slate-50 border border-slate-200/70 rounded-lg p-2.5 leading-relaxed">
          {explanation}
        </div>
      </div>
    </div>
  );
}

/**
 * Tasteful Empty State Card when no qualifying evidence exists
 */
function EmptyDonutCard({
  title,
  discipline,
  reason,
  details,
}: {
  title: string;
  discipline: "batting" | "bowling";
  reason: string;
  details: string;
}) {
  const isBatting = discipline === "batting";

  return (
    <div className="bg-slate-50/60 p-5 rounded-2xl border border-dashed border-slate-300 shadow-2xs flex flex-col justify-between space-y-4">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-slate-100 text-slate-400 border border-slate-200">
              {isBatting ? (
                <Flame className="w-4 h-4 text-slate-400" />
              ) : (
                <Target className="w-4 h-4 text-slate-400" />
              )}
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-600">{title}</h3>
              <p className="text-[11px] text-slate-400">No qualifying pressure data</p>
            </div>
          </div>
        </div>

        {/* Tasteful Empty State Message */}
        <div className="py-8 px-4 text-center space-y-2">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 text-slate-400 mb-1">
            <AlertCircle className="w-5 h-5 text-slate-400" />
          </div>
          <p className="text-xs font-semibold text-slate-700">{reason}</p>
          <p className="text-[11px] text-slate-500 max-w-sm mx-auto leading-relaxed">
            {details}
          </p>
        </div>
      </div>

      <div className="text-[10px] text-slate-400 border-t border-slate-200 pt-2 text-center">
        Threshold: Min. 20 pressure balls faced / 6 pressure overs bowled
      </div>
    </div>
  );
}
