"""
Match-Level Aggregation Module
Part of SupeRR Intelligence — Pressure Performer Intelligence

Aggregates delivery-level pressure performances into player-match records.
Treats the match as the primary unit of performance analysis to prevent
single-innings distortions from inflating or deflating career ratings.
"""

from typing import Optional
import pandas as pd
import numpy as np


def aggregate_player_matches(
    hp_deliveries: pd.DataFrame,
    context_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    Aggregates high-pressure deliveries by player and match.
    
    Parameters:
    - hp_deliveries: deliveries tagged as high pressure.
    - context_filter: None (all), 'CHASE' (innings 2), or 'FIRST_INNINGS' (innings 1).
    """
    df = hp_deliveries.copy()
    if context_filter == "CHASE":
        df = df[df["innings"] == 2].copy()
    elif context_filter == "FIRST_INNINGS":
        df = df[df["innings"] == 1].copy()
        
    if df.empty:
        return pd.DataFrame()
        
    # Ensure wide deliveries never contribute to batting RAE or expected runs
    if "extras_wide_runs" in df.columns:
        is_wide = df["extras_wide_runs"] > 0
        df.loc[is_wide, "expected_batter_runs"] = 0.0
        df.loc[is_wide, "rae"] = 0.0
    elif "is_legal_ball" in df.columns:
        is_wide = ~df["is_legal_ball"].astype(bool)
        df.loc[is_wide, "expected_batter_runs"] = 0.0
        df.loc[is_wide, "rae"] = 0.0

    # Ensure required columns for aggregation exist
    if "expected_wicket_prob" not in df.columns:
        df["expected_wicket_prob"] = 0.0
    if "is_six" not in df.columns:
        df["is_six"] = 0
    if "is_striker_dismissed" not in df.columns:
        df["is_striker_dismissed"] = 0
        
    # Aggregate by player and match
    match_grouped = df.groupby(["striker_id", "striker_name", "match_id"]).agg(
        comp_id=("comp_id", "first"),
        comp_name=("comp_name", "first"),
        season=("season", "first"),
        match_date=("match_date", "first"),
        format_scope=("format_scope", "first"),
        innings=("innings", "first"),
        hp_balls=("is_legal_ball", "sum"),
        hp_runs=("batter_runs", "sum"),
        hp_exp_runs=("expected_batter_runs", "sum"),
        hp_rae=("rae", "sum"),
        hp_striker_dismissals=("is_striker_dismissed", "sum"),
        hp_exp_wickets=("expected_wicket_prob", "sum"),
        hp_boundaries=("is_boundary", "sum"),
        hp_sixes=("is_six", "sum"),
        hp_dots=("is_dot", "sum"),
        hp_min_pressure=("pressure_index", "min"),
        hp_max_pressure=("pressure_index", "max"),
        hp_avg_pressure=("pressure_index", "mean"),
        # Qualitative match context at entry
        entry_score=("pre_ball_score", "min"),
        entry_wickets=("pre_ball_wickets", "min"),
        entry_rrr=("required_run_rate", "first"),
        entry_balls_rem=("legal_balls_remaining", "first")
    ).reset_index()
    
    match_grouped.rename(
        columns={"striker_id": "player_id", "striker_name": "player_name"},
        inplace=True
    )
    
    # Match impact metrics
    match_grouped["hp_raw_rae_per_100"] = (
        100.0 * match_grouped["hp_rae"] / np.maximum(match_grouped["hp_balls"], 1)
    )
    match_grouped["hp_strike_rate"] = (
        100.0 * match_grouped["hp_runs"] / np.maximum(match_grouped["hp_balls"], 1)
    )
    match_grouped["is_positive_impact"] = match_grouped["hp_rae"] > 0
    match_grouped["is_negative_impact"] = match_grouped["hp_rae"] < 0
    match_grouped["is_neutral_impact"] = match_grouped["hp_rae"] == 0
    
    # Sort chronologically
    match_grouped.sort_values(by=["match_date", "match_id"], inplace=True)
    
    return match_grouped
