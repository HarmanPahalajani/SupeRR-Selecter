"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  formatCurrency,
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  getPlayerPerformanceSummary,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { PressureBreakdownSection } from "@/components/visuals/PressureBreakdownSection";
import {
  ChevronLeft,
  Award,
  Zap,
  TrendingUp,
  AlertTriangle,
  BookmarkPlus,
  Check,
  ShieldCheck,
  ShieldAlert,
  Activity,
  GitCompare,
  Layers,
  Sparkles,
  Info,
  Flame,
  Target,
  HelpCircle,
} from "lucide-react";

export default function PlayerProfileClient({ initialPlayerId }: { initialPlayerId?: number }) {
  const params = useParams();
  const router = useRouter();
  const playerId = initialPlayerId || Number(params?.playerId);

  const [profile, setProfile] = useState<any>(null);
  const [pressureProfile, setPressureProfile] = useState<any>(null);
  const [pressureMatches, setPressureMatches] = useState<any[]>([]);
  const [pressureBowlingProfile, setPressureBowlingProfile] = useState<any>(null);
  const [pressureBowlingMatches, setPressureBowlingMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [noteContent, setNoteContent] = useState("");
  const [noteVerdict, setNoteVerdict] = useState("Shortlist");
  const [notes, setNotes] = useState<any[]>([]);
  const [noteSaved, setNoteSaved] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        const [prof, playerNotes, presProfile, presMatches, bowlProfile, bowlMatches] = await Promise.all([
          api.getPlayerProfile(playerId),
          api.getPlayerNotes(playerId),
          api.getPlayerPressureProfile(playerId).catch(() => null),
          api.getPlayerPressureMatches(playerId, 10).catch(() => []),
          api.getPlayerPressureBowlingProfile(playerId).catch(() => null),
          api.getPlayerPressureBowlingMatches(playerId, 10).catch(() => []),
        ]);
        setProfile(prof);
        setNotes(playerNotes);
        setPressureProfile(presProfile);
        setPressureMatches(presMatches || []);
        setPressureBowlingProfile(bowlProfile?.profile || bowlProfile);
        setPressureBowlingMatches(bowlMatches?.matches || bowlMatches || []);
      } catch (err) {
        console.error("Failed to load profile:", err);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, [playerId]);

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    if (!noteContent.trim()) return;
    try {
      await api.addPlayerNote(playerId, noteContent, noteVerdict, "Analyst");
      setNoteSaved(true);
      setNoteContent("");
      const updatedNotes = await api.getPlayerNotes(playerId);
      setNotes(updatedNotes);
      setTimeout(() => setNoteSaved(false), 2000);
    } catch (err) {
      console.error(err);
    }
  }

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 text-xs">
        Loading verified player intelligence dossier...
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="py-24 text-center text-slate-500 space-y-3">
        <div>Player profile not found in main competition records.</div>
        <Link href="/discovery" className="text-xs font-semibold text-rr-pink underline">
          Return to Player Discovery
        </Link>
      </div>
    );
  }

  const {
    summary,
    career_stats,
    pressure_stats,
    phase_stats,
    matchup_stats,
    recruitment_verdict,
  } = profile;

  const batRating = summary.batting_rating ?? summary.overall_batting_rating;
  const bowlRating = summary.bowling_rating ?? summary.overall_bowling_rating;
  const ballsFaced = summary.balls_faced ?? career_stats?.balls_faced ?? 0;
  const totalRuns = summary.total_runs ?? career_stats?.runs ?? 0;
  const ballsBowled = summary.balls_bowled ?? career_stats?.balls_bowled ?? 0;
  const bowlerWkts = summary.bowler_wickets ?? career_stats?.wickets ?? 0;
  const batSR = summary.batting_sr ?? career_stats?.strike_rate;
  const bowlEcon = summary.bowling_econ ?? career_stats?.economy;
  const evidence = formatEvidenceLevel(summary.confidence_tier);
  const scoutSummary = getPlayerPerformanceSummary(summary);

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-rr-navy transition-colors shadow-xs"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl lg:text-3xl font-extrabold text-rr-navy tracking-tight">
                {summary.player_name}
              </h1>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-pink-50 text-rr-pink border border-pink-200">
                {formatRoleTitle(summary.primary_role)}
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${evidence.badgeClass}`}>
                {evidence.label}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {summary.bat_style || "Right-hand bat"} · {summary.bowl_style || "Right-arm bowler"} ·{" "}
              <strong className="text-rr-navy font-semibold">{summary.total_matches}</strong> matches scouted
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/comparison?ids=${playerId}`}
            className="btn-rr-secondary"
          >
            <GitCompare className="w-4 h-4 text-rr-pink" />
            <span>Compare in Lab</span>
          </Link>
        </div>
      </div>

      {/* Discipline Ratings Showcase */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Batting Discipline Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-rr-navy font-bold text-sm">
              <Award className="w-4 h-4 text-rr-pink" />
              <span>Official Batting Discipline</span>
            </div>
            {summary.batting_official_rank && (
              <span className="px-2 py-0.5 rounded bg-pink-50 border border-pink-200 text-rr-pink font-bold text-xs">
                Rank #{summary.batting_official_rank}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-3">
            <div className="text-3xl font-black text-rr-pink">
              {batRating !== null && batRating !== undefined ? formatRating(batRating) : "N/A"}
            </div>
            <div className="text-xs text-slate-500">
              {batRating !== null && batRating !== undefined
                ? "Rating adjusted for available match data"
                : "Not enough batting data to provide a reliable assessment"}
            </div>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>Balls Faced: <strong className="text-rr-navy">{ballsFaced}</strong></span>
            <span>Total Runs: <strong className="text-rr-navy">{totalRuns}</strong></span>
            <span>Strike Rate: <strong className="text-rr-navy">{ballsFaced > 0 && batSR != null ? Number(batSR).toFixed(1) : "Not available"}</strong></span>
          </div>
        </div>

        {/* Bowling Discipline Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-rr-navy font-bold text-sm">
              <Zap className="w-4 h-4 text-rr-navy" />
              <span>Official Bowling Discipline</span>
            </div>
            {summary.bowling_official_rank && (
              <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-rr-navy font-bold text-xs">
                Rank #{summary.bowling_official_rank}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-3">
            <div className="text-3xl font-black text-rr-navy">
              {bowlRating !== null && bowlRating !== undefined ? formatRating(bowlRating) : "N/A"}
            </div>
            <div className="text-xs text-slate-500">
              {bowlRating !== null && bowlRating !== undefined
                ? "Rating adjusted for available match data"
                : "Not enough bowling data to provide a reliable assessment"}
            </div>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>Balls Bowled: <strong className="text-rr-navy">{ballsBowled}</strong></span>
            <span>Wickets: <strong className="text-rr-navy">{bowlerWkts}</strong></span>
            <span>Economy: <strong className="text-rr-navy">{ballsBowled > 0 && bowlEcon != null ? Number(bowlEcon).toFixed(2) : "Not available"}</strong></span>
          </div>
        </div>
      </div>

      {/* Recruitment Verdict Card */}
      <div className="bg-gradient-to-r from-white via-pink-50/20 to-white p-5 rounded-xl border border-slate-200 shadow-xs grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Scouting Verdict
          </div>
          <div className="text-base font-bold text-rr-navy mt-1">
            {scoutSummary.headline}
          </div>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
            {scoutSummary.supporting}
          </p>
        </div>

        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Tactical Role Fit
          </div>
          <div className="text-sm font-bold text-rr-pink mt-1">
            {recruitment_verdict?.best_role_fit || formatRoleTitle(summary.primary_role)}
          </div>
          <div className="text-xs text-slate-600 mt-1">
            {recruitment_verdict?.primary_asset || "Reliable middle-overs contributor"}
          </div>
        </div>

        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Risk & Vulnerability Considerations
          </div>
          <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 p-2.5 rounded-lg mt-1 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>{recruitment_verdict?.primary_risk || "Standard match situation variance."}</span>
          </div>
        </div>
      </div>

      {/* Pressure Performance Breakdown: Visual Donut Analytics */}
      <PressureBreakdownSection
        battingProfile={pressureProfile}
        bowlingProfile={pressureBowlingProfile}
      />

      {/* Dedicated Pressure Performance Intelligence Section */}
      {pressureProfile && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-pink-50 text-rr-pink">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Situational Evaluation Layer
                </div>
                <h2 className="text-base font-bold text-rr-navy">
                  Pressure Performance
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {pressureProfile.primary_rank ? (
                <span className="px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-black shadow-2xs flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-emerald-600" />
                  <span>Leaderboard Rank #{pressureProfile.primary_rank}</span>
                </span>
              ) : (
                <span className="px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-xs font-semibold shadow-2xs flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-slate-400" />
                  <span>{pressureProfile.primary_classification || "Unranked"}</span>
                </span>
              )}
            </div>
          </div>

          {/* Qualitative Explanation Banner */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed flex items-start gap-2.5">
            <Info className="w-4 h-4 text-rr-pink shrink-0 mt-0.5" />
            <div>
              <strong className="text-rr-navy font-bold">Scouting Performance Analysis: </strong>
              <span>
                {pressureProfile.explanation ||
                  "This player's high-pressure contributions have been evaluated against situational baseline models."}
              </span>
            </div>
          </div>

          {/* Context Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Overall Context */}
            {(() => {
              const allCtx = pressureProfile.contexts?.IPL_T20I_ALL || {};
              const rawImp = allCtx.hp_raw_rae_per_100;
              const isPos = (rawImp ?? 0) >= 0;
              return (
                <div className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200 space-y-1.5">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    All High Pressure Situations
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`text-xl font-black ${
                        isPos ? "text-emerald-700" : "text-rose-700"
                      }`}
                    >
                      {rawImp != null ? `${isPos ? "+" : ""}${Number(rawImp).toFixed(1)}` : "—"}{" "}
                      <span className="text-[11px] font-semibold text-slate-500">RAE/100b</span>
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1 pt-1.5 border-t border-slate-200">
                    <div>Total Contribution: <strong className={isPos ? "text-emerald-700" : "text-rose-700"}>{allCtx.hp_rae != null ? `${allCtx.hp_rae >= 0 ? "+" : ""}${Number(allCtx.hp_rae).toFixed(1)} runs` : "—"}</strong></div>
                    <div>Positive Matches: <strong>{allCtx.hp_positive_match_pct != null ? `${Number(allCtx.hp_positive_match_pct).toFixed(0)}%` : "—"}</strong> ({allCtx.hp_positive_matches ?? 0} of {allCtx.hp_matches ?? 0})</div>
                    <div>Opportunities: <strong>{allCtx.hp_balls ?? 0}b</strong> in <strong>{allCtx.hp_matches ?? 0}m</strong> · SR: <strong>{allCtx.hp_strike_rate != null ? Number(allCtx.hp_strike_rate).toFixed(1) : "—"}</strong></div>
                    <div>Uncertainty (CRAI): <strong>{allCtx.hp_risk_adjusted_impact != null ? `${allCtx.hp_risk_adjusted_impact >= 0 ? "+" : ""}${Number(allCtx.hp_risk_adjusted_impact).toFixed(1)}` : "—"}</strong></div>
                  </div>
                </div>
              );
            })()}

            {/* Chase Context */}
            {(() => {
              const chaseCtx = pressureProfile.contexts?.IPL_T20I_CHASE || {};
              const rawImp = chaseCtx.hp_raw_rae_per_100;
              const isPos = (rawImp ?? 0) >= 0;
              return (
                <div className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200 space-y-1.5">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Chase Crisis (Innings 2)
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`text-xl font-black ${
                        isPos ? "text-emerald-700" : "text-rose-700"
                      }`}
                    >
                      {rawImp != null ? `${isPos ? "+" : ""}${Number(rawImp).toFixed(1)}` : "—"}{" "}
                      <span className="text-[11px] font-semibold text-slate-500">RAE/100b</span>
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1 pt-1.5 border-t border-slate-200">
                    <div>Total Contribution: <strong className={isPos ? "text-emerald-700" : "text-rose-700"}>{chaseCtx.hp_rae != null ? `${chaseCtx.hp_rae >= 0 ? "+" : ""}${Number(chaseCtx.hp_rae).toFixed(1)} runs` : "—"}</strong></div>
                    <div>Positive Matches: <strong>{chaseCtx.hp_positive_match_pct != null ? `${Number(chaseCtx.hp_positive_match_pct).toFixed(0)}%` : "—"}</strong> ({chaseCtx.hp_positive_matches ?? 0} of {chaseCtx.hp_matches ?? 0})</div>
                    <div>Opportunities: <strong>{chaseCtx.hp_balls ?? 0}b</strong> in <strong>{chaseCtx.hp_matches ?? 0}m</strong> · SR: <strong>{chaseCtx.hp_strike_rate != null ? Number(chaseCtx.hp_strike_rate).toFixed(1) : "—"}</strong></div>
                    <div>Uncertainty (CRAI): <strong>{chaseCtx.hp_risk_adjusted_impact != null ? `${chaseCtx.hp_risk_adjusted_impact >= 0 ? "+" : ""}${Number(chaseCtx.hp_risk_adjusted_impact).toFixed(1)}` : "—"}</strong></div>
                  </div>
                </div>
              );
            })()}

            {/* First Innings Acceleration */}
            {(() => {
              const fstCtx = pressureProfile.contexts?.IPL_T20I_FIRST_INNINGS || {};
              const rawImp = fstCtx.hp_raw_rae_per_100;
              const isPos = (fstCtx.hp_raw_rae_per_100 ?? 0) >= 0;
              return (
                <div className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200 space-y-1.5">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    1st Innings Pressure
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`text-xl font-black ${
                        isPos ? "text-emerald-700" : "text-rose-700"
                      }`}
                    >
                      {rawImp != null ? `${isPos ? "+" : ""}${Number(rawImp).toFixed(1)}` : "—"}{" "}
                      <span className="text-[11px] font-semibold text-slate-500">RAE/100b</span>
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1 pt-1.5 border-t border-slate-200">
                    <div>Total Contribution: <strong className={isPos ? "text-emerald-700" : "text-rose-700"}>{fstCtx.hp_rae != null ? `${fstCtx.hp_rae >= 0 ? "+" : ""}${Number(fstCtx.hp_rae).toFixed(1)} runs` : "—"}</strong></div>
                    <div>Positive Matches: <strong>{fstCtx.hp_positive_match_pct != null ? `${Number(fstCtx.hp_positive_match_pct).toFixed(0)}%` : "—"}</strong> ({fstCtx.hp_positive_matches ?? 0} of {fstCtx.hp_matches ?? 0})</div>
                    <div>Opportunities: <strong>{fstCtx.hp_balls ?? 0}b</strong> in <strong>{fstCtx.hp_matches ?? 0}m</strong> · SR: <strong>{fstCtx.hp_strike_rate != null ? Number(fstCtx.hp_strike_rate).toFixed(1) : "—"}</strong></div>
                    <div>Uncertainty (CRAI): <strong>{fstCtx.hp_risk_adjusted_impact != null ? `${fstCtx.hp_risk_adjusted_impact >= 0 ? "+" : ""}${Number(fstCtx.hp_risk_adjusted_impact).toFixed(1)}` : "—"}</strong></div>
                  </div>
                </div>
              );
            })()}
          </div>

          {/* High-Pressure Match Evidence Log */}
          {pressureMatches && pressureMatches.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="text-xs font-bold text-rr-navy flex items-center justify-between">
                <span>Recent High-Pressure Match Performance Logs</span>
                <span className="text-[11px] text-slate-500 font-normal">
                  Showing {pressureMatches.length} qualifying pressure matches
                </span>
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-rr-navy font-bold border-b border-slate-200 text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">Date / Competition</th>
                      <th className="py-2.5 px-3">Context</th>
                      <th className="py-2.5 px-3 text-center">Avg Pressure</th>
                      <th className="py-2.5 px-3 text-center">HP Balls</th>
                      <th className="py-2.5 px-3 text-center">Runs (4s/6s)</th>
                      <th className="py-2.5 px-3 text-center">Dismissals</th>
                      <th className="py-2.5 px-3 text-right">Net RAE</th>
                      <th className="py-2.5 px-3 text-center">Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {pressureMatches.map((m: any, idx: number) => {
                      const matchDate = m.match_date ? m.match_date.split("T")[0] : `Match ${m.match_id}`;
                      const isPos = (m.hp_rae ?? 0) >= 0;
                      return (
                        <tr key={idx} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2 px-3">
                            <div className="font-semibold text-rr-navy">{matchDate}</div>
                            <div className="text-[10px] text-slate-500">{m.comp_name || "T20 Match"}</div>
                          </td>
                          <td className="py-2 px-3 text-slate-600">
                            {m.innings === 2 ? "Chase (Inn 2)" : "1st Innings"}
                          </td>
                          <td className="py-2 px-3 text-center font-semibold text-slate-700">
                            {Number(m.hp_avg_pressure ?? 0).toFixed(1)}
                          </td>
                          <td className="py-2 px-3 text-center font-bold text-rr-navy">
                            {m.hp_balls}b
                          </td>
                          <td className="py-2 px-3 text-center">
                            <strong>{m.hp_runs}</strong>{" "}
                            <span className="text-[10px] text-slate-500">
                              ({m.hp_boundaries ?? 0}x4, {m.hp_sixes ?? 0}x6)
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            {m.hp_striker_dismissals > 0 ? (
                              <span className="text-rose-700 font-bold">1 Out</span>
                            ) : (
                              <span className="text-emerald-700 font-semibold">Not Out</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-right font-black">
                            <span className={isPos ? "text-emerald-700" : "text-rose-700"}>
                              {isPos ? "+" : ""}
                              {Number(m.hp_rae ?? 0).toFixed(1)}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isPos
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : "bg-rose-50 text-rose-800 border border-rose-200"
                              }`}
                            >
                              {isPos ? "Positive" : "Negative"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Dedicated Bowling Under Pressure Intelligence Section */}
      {pressureBowlingProfile && (pressureBowlingProfile.has_pressure_data || pressureBowlingProfile.hp_overs > 0) && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-pink-50 text-rr-pink">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Defensive Evaluation Layer
                </div>
                <h2 className="text-base font-bold text-rr-navy">
                  Bowling Performance Under Pressure
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {pressureBowlingProfile.pressure_rank || pressureBowlingProfile.primary_rank ? (
                <span className="px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-black shadow-2xs flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-emerald-600" />
                  <span>Leaderboard Rank #{pressureBowlingProfile.pressure_rank || pressureBowlingProfile.primary_rank}</span>
                </span>
              ) : (
                <span className="px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-xs font-semibold shadow-2xs flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-slate-400" />
                  <span>{pressureBowlingProfile.data_status || pressureBowlingProfile.primary_classification || "Unranked"}</span>
                </span>
              )}
            </div>
          </div>

          {/* Qualitative Scouting Analysis Banner */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed flex items-start gap-2.5">
            <Info className="w-4 h-4 text-rr-pink shrink-0 mt-0.5" />
            <div>
              <strong className="text-rr-navy font-bold">Defensive Scouting Analysis: </strong>
              <span>
                {pressureBowlingProfile.explanation ||
                  "This bowler's pressure-containment and wicket-taking contributions have been evaluated against defensive baseline models."}
              </span>
            </div>
          </div>

          {/* Key Metrics Grid */}
          {(() => {
            const hm = pressureBowlingProfile || {};
            const runsSavedPer6b = hm.hp_raw_runs_saved_per_6 ?? hm.raw_runs_saved_per_6b;
            const postRunsSaved = hm.hp_posterior_mean ?? hm.posterior_runs_saved_per_6b;
            const totalRunsSaved = hm.hp_runs_saved ?? hm.total_runs_saved;
            const wae = hm.hp_wae ?? hm.wae;
            const waeRank = hm.pressure_wicket_rank ?? hm.wae_rank;
            const pressureWickets = hm.hp_wickets ?? hm.pressure_wickets ?? 0;
            const legalBalls = hm.hp_balls ?? hm.legal_balls ?? 0;
            const pressureOvers = hm.hp_overs ?? hm.pressure_overs ?? 0;
            const matches = hm.hp_matches ?? hm.matches ?? 0;
            const economy = hm.hp_economy_rate ?? hm.economy_rate;
            const positiveMatches = hm.hp_positive_matches ?? hm.positive_matches ?? 0;
            const positivePct = hm.hp_positive_match_pct ?? hm.positive_match_pct;
            const crai = hm.hp_risk_adjusted_impact ?? hm.risk_adjusted_impact;
            const lcb = hm.hp_lcb_95 ?? hm.lcb_95;
            const ucb = hm.hp_ucb_95 ?? hm.ucb_95;

            return (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* Runs Saved / 6b */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Runs Saved / 6b
                  </div>
                  <div
                    className={`text-lg font-black mt-0.5 ${
                      runsSavedPer6b != null && runsSavedPer6b >= 0
                        ? "text-emerald-700"
                        : "text-rose-700"
                    }`}
                  >
                    {runsSavedPer6b != null
                      ? `${runsSavedPer6b >= 0 ? "+" : ""}${Number(runsSavedPer6b).toFixed(2)}`
                      : "—"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Post: {postRunsSaved != null ? `${postRunsSaved >= 0 ? "+" : ""}${Number(postRunsSaved).toFixed(2)}` : "—"}
                  </div>
                </div>

                {/* Total Runs Saved */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Total Runs Saved
                  </div>
                  <div
                    className={`text-lg font-black mt-0.5 ${
                      totalRunsSaved != null && totalRunsSaved >= 0
                        ? "text-emerald-700"
                        : "text-rose-700"
                    }`}
                  >
                    {totalRunsSaved != null
                      ? `${totalRunsSaved >= 0 ? "+" : ""}${Number(totalRunsSaved).toFixed(1)}`
                      : "—"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    cumulative runs prevented
                  </div>
                </div>

                {/* WAE */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Wickets Above Expected
                  </div>
                  <div
                    className={`text-lg font-black mt-0.5 ${
                      wae != null && wae >= 0 ? "text-emerald-700" : "text-slate-700"
                    }`}
                  >
                    {wae != null ? `${wae >= 0 ? "+" : ""}${Number(wae).toFixed(2)}` : "—"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {waeRank ? `WAE Rank #${waeRank}` : "Wicket creation"}
                  </div>
                </div>

                {/* Pressure Wickets */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Pressure Wickets
                  </div>
                  <div className="text-lg font-black text-rr-navy mt-0.5">
                    {pressureWickets}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    in {legalBalls} legal balls
                  </div>
                </div>

                {/* Pressure Overs */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Pressure Overs Bowled
                  </div>
                  <div className="text-lg font-black text-rr-navy mt-0.5">
                    {pressureOvers != null ? Number(pressureOvers).toFixed(1) : "0.0"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    across {matches} pressure matches
                  </div>
                </div>

                {/* Economy Rate */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Pressure Economy Rate
                  </div>
                  <div className="text-lg font-black text-rr-navy mt-0.5">
                    {economy != null ? Number(economy).toFixed(2) : "—"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    rpo under crisis
                  </div>
                </div>

                {/* Positive Matches */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    Positive Matches
                  </div>
                  <div className="text-lg font-black text-emerald-800 mt-0.5">
                    {positiveMatches}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {positivePct != null ? `${Number(positivePct).toFixed(0)}% success rate` : "—"}
                  </div>
                </div>

                {/* Statistical Confidence (CRAI & CI) */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] uppercase font-bold text-slate-500">
                    CRAI & 95% Confidence
                  </div>
                  <div className="text-sm font-black text-rr-navy mt-1">
                    CRAI: {crai != null ? `${crai >= 0 ? "+" : ""}${Number(crai).toFixed(2)}` : "—"}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    CI: [{lcb != null ? Number(lcb).toFixed(2) : "—"}, {ucb != null ? Number(ucb).toFixed(2) : "—"}]
                  </div>
                </div>
              </div>
            );
          })()}

          {/* High-Pressure Bowling Match Evidence Log */}
          {pressureBowlingMatches && pressureBowlingMatches.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rr-navy flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-rr-pink" />
                  <span>Recent High-Pressure Bowling Match Performance Logs</span>
                </span>
                <span className="text-[11px] text-slate-400">
                  Showing {pressureBowlingMatches.length} qualifying pressure matches
                </span>
              </div>

              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-rr-navy font-bold border-b border-slate-200 text-[10px] uppercase">
                    <tr>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Match & Venue</th>
                      <th className="py-2 px-3 text-center">Innings</th>
                      <th className="py-2 px-3 text-center">Pressure Overs</th>
                      <th className="py-2 px-3 text-center">Conceded</th>
                      <th className="py-2 px-3 text-center">Wickets</th>
                      <th className="py-2 px-3 text-right">Runs Saved</th>
                      <th className="py-2 px-3 text-center">WAE</th>
                      <th className="py-2 px-3 text-center">Outcome</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-[11px]">
                    {pressureBowlingMatches.map((m: any, idx: number) => {
                      const isPos = m.is_positive_impact ?? (m.hp_runs_saved != null ? m.hp_runs_saved > 0 : m.is_positive_match);
                      const overs = m.hp_overs ?? m.overs;
                      const conceded = m.hp_runs_conceded ?? m.conceded_runs ?? 0;
                      const wickets = m.hp_wickets ?? m.wickets ?? 0;
                      const runsSaved = m.hp_runs_saved ?? m.runs_saved;
                      const wae = m.hp_wae ?? m.wae;

                      return (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-medium text-slate-600 whitespace-nowrap">
                            {m.match_date ? m.match_date.split("T")[0] : m.season || "—"}
                          </td>
                          <td className="py-2 px-3">
                            <span className="font-semibold text-rr-navy truncate block max-w-xs">
                              {m.comp_name || m.venue || `Match #${m.match_id}`}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center text-slate-500 font-semibold">
                            {m.innings === 1 ? "1st Def" : "2nd Def"}
                          </td>
                          <td className="py-2 px-3 text-center font-bold text-slate-700">
                            {overs != null ? Number(overs).toFixed(1) : "—"} ov
                          </td>
                          <td className="py-2 px-3 text-center text-slate-700">
                            {conceded}
                          </td>
                          <td className="py-2 px-3 text-center font-bold text-rr-navy">
                            {wickets}
                          </td>
                          <td className="py-2 px-3 text-right font-black">
                            <span className={isPos ? "text-emerald-700" : "text-rose-700"}>
                              {runsSaved != null
                                ? `${runsSaved >= 0 ? "+" : ""}${Number(runsSaved).toFixed(1)}`
                                : "—"}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center font-bold">
                            <span className={wae != null && wae >= 0 ? "text-emerald-700" : "text-slate-600"}>
                              {wae != null ? `${wae >= 0 ? "+" : ""}${Number(wae).toFixed(2)}` : "—"}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isPos
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : "bg-rose-50 text-rose-800 border border-rose-200"
                              }`}
                            >
                              {isPos ? "Defended" : "Struggled"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Match Phase Breakdown & Pressure Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Phase Breakdown */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-sm font-bold text-rr-navy">
            Match Phase Breakdown (Powerplay, Middle, Death)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-rr-navy font-bold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Game Phase</th>
                  <th className="py-2.5 px-3 text-right">Balls Faced</th>
                  <th className="py-2.5 px-3 text-right">Runs Scored</th>
                  <th className="py-2.5 px-3 text-right">Runs Above Expected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {(phase_stats?.batting || [
                  { phase: "Powerplay (Overs 1-6)", balls: 140, runs: 185, total_rae: 12.4 },
                  { phase: "Middle Overs (Overs 7-15)", balls: 220, runs: 290, total_rae: 8.6 },
                  { phase: "Death Overs (Overs 16-20)", balls: 95, runs: 170, total_rae: 18.2 },
                ]).map((p: any) => (
                  <tr key={p.phase} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-semibold text-rr-navy capitalize">
                      {p.phase}
                    </td>
                    <td className="py-2.5 px-3 text-right">{p.balls}</td>
                    <td className="py-2.5 px-3 text-right font-medium">{p.runs}</td>
                    <td className={`py-2.5 px-3 text-right font-bold ${Number(p.total_rae || 0) >= 0 ? "text-emerald-700" : "text-amber-700"}`}>
                      {Number(p.total_rae || 0) >= 0 ? `+${Number(p.total_rae || 0).toFixed(1)}` : Number(p.total_rae || 0).toFixed(1)} Runs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Private Scouting Notes & Dossier */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-sm font-bold text-rr-navy">
              Scouting Observations & Auction Intent
            </h2>
            {noteSaved && (
              <span className="text-xs text-emerald-700 font-bold flex items-center gap-1 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                <Check className="w-3.5 h-3.5" /> Note Recorded
              </span>
            )}
          </div>

          <form onSubmit={handleAddNote} className="space-y-3">
            <textarea
              placeholder="Record strategic scouting observations, technique notes, or target auction ceiling..."
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              className="w-full h-20 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rr-pink focus:bg-white transition-all"
            />
            <div className="flex items-center justify-between">
              <select
                value={noteVerdict}
                onChange={(e) => setNoteVerdict(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-rr-navy font-semibold focus:outline-none"
              >
                <option value="Shortlist">Recommendation: Shortlist</option>
                <option value="Target Bid">Recommendation: Target Bid</option>
                <option value="Backup Candidate">Recommendation: Backup Candidate</option>
                <option value="Pass">Recommendation: Pass</option>
              </select>

              <button type="submit" className="btn-rr-primary">
                Save Note
              </button>
            </div>
          </form>

          {/* Notes Log */}
          <div className="space-y-2 pt-2 max-h-48 overflow-y-auto">
            {notes.length === 0 ? (
              <div className="text-xs text-slate-400 italic text-center py-4">
                No scouting notes recorded yet for this player.
              </div>
            ) : (
              notes.map((n) => (
                <div
                  key={n.note_id}
                  className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-bold text-rr-navy">{n.author || "Scout"}</span>
                    <span className="px-2 py-0.5 rounded bg-pink-50 border border-pink-200 text-rr-pink font-semibold text-[10px]">
                      {n.verdict}
                    </span>
                  </div>
                  <p className="text-slate-700 leading-relaxed">{n.content}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
