/**
 * Format player roles consistently across the UI.
 * Ensures the UNKNOWN category is always displayed as "Insufficient Performance Data".
 */
export function formatPlayerRole(role: string | null | undefined): string {
  if (!role) return "Unclassified";
  const r = role.trim().toUpperCase();
  if (r === "UNKNOWN") {
    return "Insufficient Performance Data";
  }
  if (r === "ALL_ROUNDER") {
    return "All-Rounder";
  }
  if (r === "WICKETKEEPER" || r === "WICKETKEEPER_BATTER") {
    return "Wicketkeeper";
  }
  if (r === "BATTER") {
    return "Batter";
  }
  if (r === "BOWLER") {
    return "Bowler";
  }
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
