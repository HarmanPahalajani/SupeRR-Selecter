"""
Evidence Status & Narrative Module
Part of SupeRR Intelligence — Pressure Performer Intelligence

Replaces artificial player category tiers (Elite, Reliable, Hidden, etc.)
with transparent, evidence-aware status tracking and objective cricket narrative generation.
All qualifying positive batters compete on ONE unified leaderboard.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

# Unified Evidence Status Labels
STATUS_RANKED = "Ranked Pressure Performer"
STATUS_LIMITED_EVIDENCE = "Limited Evidence (<25 HP balls)"
STATUS_BELOW_BASELINE = "Below Baseline Contribution"
STATUS_INSUFFICIENT = "Insufficient Pressure Evidence"
STATUS_EMERGING_RANKED = "Emerging Pressure Performer"
STATUS_EMERGING_LIMITED = "Emerging Scope — Limited Evidence"

# Legacy backward-compatibility constants (mapped cleanly to unified concepts)
CLASS_ELITE = "Ranked Pressure Performer"
CLASS_RELIABLE = "Ranked Pressure Performer"
CLASS_HIDDEN = "Ranked Pressure Performer"
CLASS_HIGH_IMPACT_LIMITED = "Limited Evidence (<25 HP balls)"
CLASS_STRUGGLES = "Below Baseline Contribution"
CLASS_INSUFFICIENT = "Insufficient Pressure Evidence"
CLASS_EMERGING_TALENT = "Emerging Pressure Performer"


def classify_player_record(row: pd.Series, is_emerging: bool = False) -> str:
    """
    Evaluates evidence sufficiency and situational direction without artificial category buckets.
    """
    balls = row.get("hp_balls", 0.0)
    matches = row.get("hp_matches", 0)
    post_mean = row.get("hp_posterior_mean", 0.0)
    raw_rae_100 = row.get("hp_raw_rae_per_100", 0.0)
    
    if balls == 0 or pd.isna(balls):
        return STATUS_INSUFFICIENT
        
    if is_emerging:
        if balls >= 15 and matches >= 2 and post_mean > 0.0:
            return STATUS_EMERGING_RANKED
        elif post_mean > 0.0:
            return STATUS_EMERGING_LIMITED
        else:
            return STATUS_BELOW_BASELINE
            
    # Primary Scope evaluation
    if balls >= 25 and matches >= 3 and post_mean > 0.0:
        return STATUS_RANKED
    elif post_mean > 0.0 or raw_rae_100 > 0.0:
        return STATUS_LIMITED_EVIDENCE
    else:
        return STATUS_BELOW_BASELINE


def classify_dataframe(df: pd.DataFrame, is_emerging: bool = False) -> pd.DataFrame:
    """
    Assigns evidence-based status to all player records in the dataframe.
    """
    df = df.copy()
    df["classification"] = df.apply(lambda row: classify_player_record(row, is_emerging=is_emerging), axis=1)
    
    # Assign standard evidence level text
    def get_ev_level(row):
        b = row.get("hp_balls", 0)
        m = row.get("hp_matches", 0)
        if b >= 100:
            return "High Evidence"
        elif b >= 50:
            return "Moderate Evidence"
        elif b >= 25 and m >= 3:
            return "Baseline Evidence"
        elif b > 0:
            return "Limited Evidence"
        else:
            return "Insufficient Evidence"
            
    df["evidence_level"] = df.apply(get_ev_level, axis=1)
    df["explanation"] = df.apply(generate_player_explanations, axis=1)
    return df


def generate_player_explanations(row: pd.Series) -> str:
    """
    Generates objective, statistical scouting descriptions based on actual numbers.
    Does not use promotional or arbitrary tier names (Elite, Reliable, Hidden, Struggles).
    """
    balls = int(row.get("hp_balls", 0)) if not pd.isna(row.get("hp_balls", 0)) else 0
    matches = int(row.get("hp_matches", 0)) if not pd.isna(row.get("hp_matches", 0)) else 0
    rae100 = row.get("hp_raw_rae_per_100", 0.0)
    post_mean = row.get("hp_posterior_mean", 0.0)
    pos_pct = row.get("hp_positive_match_pct", 0.0)
    sr = row.get("hp_strike_rate", 0.0)
    rank = row.get("pressure_rank")
    
    if balls == 0:
        return "No qualifying high-pressure batting opportunities recorded in this competition scope."
        
    if not pd.isna(rank) and rank is not None:
        rank_str = f"Ranked #{int(rank)} on the Unified Pressure Performer Leaderboard. "
    else:
        rank_str = ""
        
    if post_mean > 0.0 and balls >= 25 and matches >= 3:
        return (
            f"{rank_str}Demonstrated positive batting contribution under match pressure, scoring "
            f"{rae100:+.1f} runs above expected per 100 high-pressure balls (posterior impact: {post_mean:+.1f}). "
            f"Delivered positive contributions in {pos_pct:.0f}% of pressure matches ({matches} matches, {balls} balls) "
            f"with a high-pressure strike rate of {sr:.1f}."
        )
    elif post_mean > 0.0 or rae100 > 0.0:
        return (
            f"Recorded {rae100:+.1f} runs above expected per 100 balls across {balls} pressure balls in {matches} matches "
            f"(strike rate: {sr:.1f}). Promising situational impact, but requires more high-pressure match evidence "
            f"to establish an official leaderboard rank."
        )
    else:
        return (
            f"Recorded {rae100:+.1f} runs above expected per 100 balls across {matches} matches ({balls} balls), "
            f"performing below situational baseline expectations under pressure."
        )
