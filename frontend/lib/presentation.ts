/**
 * Centralised Presentation and Terminology Layer for SupeRR Intelligence
 * 
 * Strict Language & Human-Readable Guidelines:
 * - Translates all backend metrics, codes, and enums into clear, cricket-scouting language.
 * - Formats currency in Indian Crores / Lakhs (₹ Cr / ₹ L).
 * - Enforces zero raw programming conditions or model jargon in the UI.
 */

export interface FormattedMetric {
  label: string;
  value: string;
  explanation: string;
  tooltip: string;
}

/**
 * Format currency into Indian Rupees (Crores / Lakhs)
 */
export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return "₹0";
  }
  const val = Math.abs(amount);
  const sign = amount < 0 ? "-" : "";
  if (val >= 10000000) {
    // Crores
    const cr = val / 10000000;
    return `${sign}₹${cr.toFixed(2)} Cr`;
  } else if (val >= 100000) {
    // Lakhs
    const lk = val / 100000;
    return `${sign}₹${lk.toFixed(1)} L`;
  }
  return `${sign}₹${val.toLocaleString("en-IN")}`;
}

/**
 * Format rating with confidence context
 */
export function formatRating(rating: number | null | undefined): string {
  if (rating === null || rating === undefined || isNaN(rating)) {
    return "N/A";
  }
  return rating.toFixed(1);
}

/**
 * Format bowling economy rate strictly respecting evidence
 */
export function formatEconomy(econ: number | null | undefined, legalBalls?: number | null | undefined): string {
  if (legalBalls !== undefined && legalBalls !== null && legalBalls <= 0) {
    return "Not available";
  }
  if (econ === null || econ === undefined || isNaN(econ)) {
    return "Not available";
  }
  return Number(econ).toFixed(2);
}

export function formatEconomyShort(econ: number | null | undefined, legalBalls?: number | null | undefined): string {
  if (legalBalls !== undefined && legalBalls !== null && legalBalls <= 0) {
    return "N/A";
  }
  if (econ === null || econ === undefined || isNaN(econ)) {
    return "N/A";
  }
  return Number(econ).toFixed(2);
}

/**
 * Format batting strike rate strictly respecting evidence
 */
export function formatStrikeRate(sr: number | null | undefined, ballsFaced?: number | null | undefined): string {
  if (ballsFaced !== undefined && ballsFaced !== null && ballsFaced <= 0) {
    return "Not available";
  }
  if (sr === null || sr === undefined || isNaN(sr)) {
    return "Not available";
  }
  return Number(sr).toFixed(1);
}

export function formatStrikeRateShort(sr: number | null | undefined, ballsFaced?: number | null | undefined): string {
  if (ballsFaced !== undefined && ballsFaced !== null && ballsFaced <= 0) {
    return "N/A";
  }
  if (sr === null || sr === undefined || isNaN(sr)) {
    return "N/A";
  }
  return Number(sr).toFixed(1);
}

/**
 * Translate evidence level / confidence tier into natural cricket terminology
 */
export function formatEvidenceLevel(tier: string | null | undefined): {
  label: string;
  description: string;
  badgeClass: string;
} {
  const t = (tier || "").toUpperCase();
  if (t === "HIGH" || t === "HIGH EVIDENCE" || t === "STRONG EVIDENCE") {
    return {
      label: "Strong Evidence",
      description: "Based on consistent performances across extensive match data.",
      badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-200",
    };
  }
  if (t === "MEDIUM" || t === "MODERATE" || t === "MEDIUM EVIDENCE" || t === "MODERATE EVIDENCE") {
    return {
      label: "Moderate Evidence",
      description: "Sufficient match data to form a reliable performance assessment.",
      badgeClass: "bg-blue-50 text-blue-800 border-blue-200",
    };
  }
  if (t === "LIMITED" || t === "LIMITED EVIDENCE" || t === "LIMITED MATCH DATA") {
    return {
      label: "Limited Match Data",
      description: "Promising performances, but more matches needed for a reliable assessment.",
      badgeClass: "bg-amber-50 text-amber-800 border-amber-200",
    };
  }
  return {
    label: "Not Enough Match Data",
    description: "Insufficient match sample to provide an official rating.",
    badgeClass: "bg-slate-100 text-slate-600 border-slate-200",
  };
}

/**
 * Format player role into natural cricket titles
 */
export function formatRoleTitle(role: string | null | undefined): string {
  if (!role) return "Player";
  const r = role.trim().toUpperCase();
  switch (r) {
    case "BATTER":
      return "Batter";
    case "BOWLER":
      return "Bowler";
    case "ALL_ROUNDER":
      return "All-Rounder";
    case "WICKETKEEPER":
    case "WICKETKEEPER_BATTER":
      return "Wicketkeeper-Batter";
    case "UNKNOWN":
      return "Not Enough Match Data";
    default:
      return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

/**
 * Translate match pressure into plain-English severity
 */
export function formatMatchPressure(pressure: number | null | undefined): {
  label: string;
  color: string;
  description: string;
} {
  if (pressure === null || pressure === undefined || isNaN(pressure)) {
    return {
      label: "Standard Match Situation",
      color: "text-slate-600",
      description: "Routine match phase with balanced scoring demands.",
    };
  }
  if (pressure >= 7.0) {
    return {
      label: "High Match Pressure",
      color: "text-rr-pink font-semibold",
      description: "Extremely demanding situation requiring elevated scoring or critical wickets.",
    };
  }
  if (pressure >= 4.0) {
    return {
      label: "Moderate Match Pressure",
      color: "text-blue-700 font-medium",
      description: "Competitive game phase where momentum is finely balanced.",
    };
  }
  return {
    label: "Low Match Pressure",
    color: "text-slate-600",
    description: "Favourable game situation with manageable required scoring rates.",
  };
}

/**
 * Provide plain-English summary of player assessment
 */
export function getPlayerPerformanceSummary(player: {
  batting_rating?: number | null;
  bowling_rating?: number | null;
  primary_role?: string;
  confidence_tier?: string;
  balls_faced?: number;
  balls_bowled?: number;
}): { headline: string; supporting: string } {
  const role = (player.primary_role || "").toUpperCase();
  const evidence = (player.confidence_tier || "").toUpperCase();
  const batRating = player.batting_rating;
  const bowlRating = player.bowling_rating;

  if (evidence === "INSUFFICIENT" || evidence === "NOT ENOUGH MATCH DATA" || role === "UNKNOWN") {
    return {
      headline: "Sample Building Phase",
      supporting: "Not enough top-tier match data to provide a reliable official assessment.",
    };
  }

  if (role === "BATTER") {
    if (batRating && batRating >= 80) {
      return {
        headline: "Elite Performer Under Pressure",
        supporting: "Consistently outperforms scoring expectations in demanding game situations.",
      };
    } else if (batRating && batRating >= 65) {
      return {
        headline: "Dependable Top-Order Contributor",
        supporting: "Demonstrates consistent run-scoring with reliable boundary production.",
      };
    }
    return {
      headline: "Solid Squad Batter",
      supporting: "Provides depth and steady scoring in primary match competitions.",
    };
  }

  if (role === "BOWLER") {
    if (bowlRating && bowlRating >= 80) {
      return {
        headline: "Frontline Strike & Economy Asset",
        supporting: "Exerts exceptional run containment and takes critical wickets under pressure.",
      };
    } else if (bowlRating && bowlRating >= 65) {
      return {
        headline: "Reliable Specialist Bowler",
        supporting: "Controls scoring effectively during key overs with disciplined execution.",
      };
    }
    return {
      headline: "Support Bowling Option",
      supporting: "Contributes valuable containment overs across league fixtures.",
    };
  }

  if (role === "ALL_ROUNDER") {
    const batValid = batRating !== null && batRating !== undefined;
    const bowlValid = bowlRating !== null && bowlRating !== undefined;
    if (batValid && bowlValid) {
      return {
        headline: "Dual-Threat Match Winner",
        supporting: "Contributes substantial proven impact with both bat and ball under pressure.",
      };
    }
    return {
      headline: "Specialist with Secondary Utility",
      supporting: "Primary skill backed by strong match evidence with developing secondary skill.",
    };
  }

  return {
    headline: "Evaluated Player",
    supporting: "Performance tracked across official regulation competitions.",
  };
}

/**
 * Plain English dictionary for tooltips and definitions
 */
export const CRICKET_TOOLTIPS = {
  matchPressure: "Shows how demanding the batting or bowling situation was at that point in the match based on score, wickets, and required rate.",
  evidenceLevel: "Indicates the depth of verified match data supporting this player's assessment. Stronger evidence means higher reliability.",
  runsAboveExpected: "Shows how many more or fewer runs a player scored compared with what was expected in similar match conditions.",
  wicketsAboveExpected: "Shows how many additional dismissals a bowler secured compared with expected baseline bowling rates.",
  battingResources: "The proportion of batting resources remaining for the innings based on available overs and wickets in hand.",
  estimatedPrice: "Estimated acquisition valuation derived from simulated franchise auction dynamics and historical bidding patterns.",
  winProbability: "Estimated chance of securing this player at the specified bid amount across 1,000 simulated auction scenarios.",
  officialRank: "Official ranking position among qualified players in main competitions (IPL & T20I). Unranked indicates insufficient match sample.",
  primaryScope: "Main Competitions: Indian Premier League (IPL) and International T20 (T20I) matches.",
  emergingScope: "Emerging Competitions: High-potential scouting matches evaluated separately from main rankings.",
};
