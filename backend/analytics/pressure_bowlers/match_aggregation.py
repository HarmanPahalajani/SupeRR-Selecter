"""
Match-Level Aggregation Module for Bowlers
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Aggregates delivery-level pressure bowling performances into bowler-match records.
Treats the match as the primary unit of performance analysis to prevent
single-over distortions from inflating or deflating career ratings.
"""

from typing import Optional
import pandas as pd
import numpy as np


def aggregate_bowler_matches(
    hp_deliveries: pd.DataFrame,
    context_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    Aggregates high-pressure deliveries by bowler and match.
    
    Parameters:
    - hp_deliveries: deliveries tagged as high pressure bowling.
    - context_filter: None (all), 'CHASE_DEFENCE' (innings 2), or 'FIRST_INNINGS_RESTRICTION' (innings 1).
    """
    df = hp_deliveries.copy()
    if context_filter == "CHASE_DEFENCE":
        df = df[df["innings"] == 2].copy()
    elif context_filter == "FIRST_INNINGS_RESTRICTION":
        df = df[df["innings"] == 1].copy()
        
    if df.empty:
        return pd.DataFrame()
        
    # Aggregate by bowler and match
    match_grouped = df.groupby(["bowler_id", "bowler_name", "match_id"]).agg(
        comp_id=("comp_id", "first"),
        comp_name=("comp_name", "first"),
        season=("season", "first"),
        match_date=("match_date", "first"),
        format_scope=("format_scope", "first"),
        innings=("innings", "first"),
        pace_or_spin=("pace_or_spin", "first"),
        hp_balls=("is_legal_ball", "sum"),
        hp_total_balls=("bowler_id", "count"),
        hp_runs_conceded=("bowler_conceded_runs", "sum"),
        hp_exp_runs_conceded=("expected_bowler_conceded_runs", "sum"),
        hp_runs_saved=("runs_saved", "sum"),
        hp_wickets=("is_bowler_wicket", "sum"),
        hp_exp_wickets=("expected_wicket_prob", "sum"),
        hp_wae=("wae", "sum"),
        hp_dots=("is_dot_ball", "sum"),
        hp_boundaries_conceded=("is_boundary_conceded", "sum"),
        hp_sixes_conceded=("is_six_conceded", "sum"),
        hp_avg_pressure=("bowling_pressure_index", "mean"),
        hp_max_pressure=("bowling_pressure_index", "max"),
        entry_score=("pre_ball_score", "min"),
        entry_wickets=("pre_ball_wickets", "min"),
        entry_rrr=("required_run_rate", "first"),
        entry_balls_rem=("legal_balls_remaining", "first")
    ).reset_index()
    
    match_grouped.rename(
        columns={"bowler_id": "player_id", "bowler_name": "player_name"},
        inplace=True
    )
    
    # Pressure overs
    match_grouped["hp_overs"] = match_grouped["hp_balls"] / 6.0
    
    # Normalized match impact metrics
    safe_balls = np.maximum(match_grouped["hp_balls"], 1)
    match_grouped["hp_runs_saved_per_6"] = 6.0 * match_grouped["hp_runs_saved"] / safe_balls
    match_grouped["hp_runs_saved_per_100"] = 100.0 * match_grouped["hp_runs_saved"] / safe_balls
    match_grouped["hp_economy_rate"] = 6.0 * match_grouped["hp_runs_conceded"] / safe_balls
    match_grouped["hp_dot_pct"] = 100.0 * match_grouped["hp_dots"] / safe_balls
    
    # Impact direction flags
    match_grouped["is_positive_impact"] = match_grouped["hp_runs_saved"] > 0
    match_grouped["is_negative_impact"] = match_grouped["hp_runs_saved"] < 0
    match_grouped["is_neutral_impact"] = match_grouped["hp_runs_saved"] == 0
    
    return match_grouped
