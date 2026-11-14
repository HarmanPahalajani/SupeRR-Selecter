"""
Pressure Bowler Ranking Module
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Generates deterministic, evidence-aware unified pressure bowling leaderboards.
Sorts qualified positive performers by Conservative Risk-Adjusted Impact (CRAI / LCB)
to reward repeatability and penalize high statistical uncertainty.
All qualifying bowlers are ranked on ONE unified leaderboard without artificial category boundaries.
"""

from typing import Optional
import pandas as pd
import numpy as np


def compute_bowler_pressure_rankings(
    df: pd.DataFrame,
    min_overs: float = 4.0,
    min_matches: int = 3,
    is_emerging: bool = False
) -> pd.DataFrame:
    """
    Assigns official unified pressure rank to all bowlers with demonstrated positive
    contributions and sufficient opportunity evidence.
    
    Ranking Criteria:
    - Primary scopes: hp_overs >= min_overs (default 4.0 ov / 24 balls), hp_matches >= min_matches (default 3),
      and hp_posterior_mean > 0.0.
    - Emerging scope: hp_overs >= 2.0 (12 balls), hp_matches >= 2, and hp_posterior_mean > 0.0.
    
    Tie-breaking:
    1. hp_risk_adjusted_impact / hp_lcb (descending)
    2. hp_posterior_mean (descending)
    3. hp_balls (descending)
    4. player_id (ascending)
    """
    df = df.copy()
    
    m_overs = 2.0 if is_emerging else min_overs
    m_matches = 2 if is_emerging else min_matches
    
    # Qualification condition: sufficient evidence and positive posterior runs saved per 6
    qualified_mask = (
        (df["hp_overs"] >= m_overs) &
        (df["hp_matches"] >= m_matches) &
        (df["hp_posterior_mean"] > 0.0)
    )
    
    df["is_pressure_ranked"] = qualified_mask
    df["pressure_rank"] = np.nan
    
    if qualified_mask.sum() > 0:
        ranked_subset = df[qualified_mask].sort_values(
            by=["hp_risk_adjusted_impact", "hp_posterior_mean", "hp_balls", "player_id"],
            ascending=[False, False, False, True]
        ).copy()
        
        ranked_subset["pressure_rank"] = np.arange(1, len(ranked_subset) + 1)
        df.loc[ranked_subset.index, "pressure_rank"] = ranked_subset["pressure_rank"]
        
    # Also compute independent Wicket Creation rank for bowlers with positive WAE
    wae_qual_mask = (
        (df["hp_overs"] >= m_overs) &
        (df["hp_matches"] >= m_matches) &
        (df["hp_wae"] > 0.0)
    )
    df["is_wicket_ranked"] = wae_qual_mask
    df["pressure_wicket_rank"] = np.nan
    if wae_qual_mask.sum() > 0:
        w_ranked = df[wae_qual_mask].sort_values(
            by=["hp_wae", "hp_wickets", "hp_balls", "player_id"],
            ascending=[False, False, False, True]
        ).copy()
        w_ranked["pressure_wicket_rank"] = np.arange(1, len(w_ranked) + 1)
        df.loc[w_ranked.index, "pressure_wicket_rank"] = w_ranked["pressure_wicket_rank"]
        
    # Sort entire dataframe:
    # 1. Ranked players first (by pressure_rank ascending)
    # 2. Unranked with hp_balls > 0 next (by CRAI desc, post_mean desc, hp_balls desc)
    # 3. Zero balls at the end
    df["sort_group"] = 2
    df.loc[df["is_pressure_ranked"], "sort_group"] = 1
    df.loc[df["hp_balls"] == 0, "sort_group"] = 3
    
    df.sort_values(
        by=["sort_group", "pressure_rank", "hp_risk_adjusted_impact", "hp_posterior_mean", "hp_balls"],
        ascending=[True, True, False, False, False],
        inplace=True
    )
    df.drop(columns=["sort_group"], inplace=True)
    
    return df
