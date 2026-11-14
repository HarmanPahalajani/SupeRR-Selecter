"""
Batting Contribution Module
Part of SupeRR Intelligence — Pressure Performer Intelligence

Calculates delivery-level and player-level batting contributions under
high pressure, preserving cricket scoring integrity and neutral baseline expectations.
"""

import pandas as pd
import numpy as np


def compute_delivery_contributions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes delivery-level runs above expected and dismissal attribution.
    """
    df = df.copy()
    
    # Verify striker legal balls (wides excluded from balls faced)
    if "is_legal_ball" not in df.columns:
        if "extras_wide_runs" in df.columns:
            df["is_legal_ball"] = df["extras_wide_runs"] == 0
        else:
            df["is_legal_ball"] = True
        
    # Verify batter runs (clean of extras)
    if "batter_runs" not in df.columns:
        df["batter_runs"] = df["runs"]
        
    # Identify wide deliveries strictly:
    # Wides are bowling events, not batting balls faced. A batter does not face the delivery
    # and cannot score off the bat, so expected_batter_runs is 0.0 and rae is 0.0.
    if "extras_wide_runs" in df.columns:
        is_wide = df["extras_wide_runs"] > 0
    elif "is_legal_ball" in df.columns:
        is_wide = ~df["is_legal_ball"].astype(bool)
    else:
        is_wide = pd.Series(False, index=df.index)

    # Compute baseline expected runs if not present
    if "expected_batter_runs" not in df.columns:
        df["expected_batter_runs"] = 0.0
        
    # Zero out expected runs for wide deliveries so batters receive no expectation or penalty
    df.loc[is_wide, "expected_batter_runs"] = 0.0
    
    # Compute RAE: batter_runs - expected_batter_runs for legal/faced balls, exactly 0.0 for wides
    df["rae"] = df["batter_runs"] - df["expected_batter_runs"]
    df.loc[is_wide, "rae"] = 0.0
        
    # Striker dismissal attribution: only when striker is the dismissed player
    if "is_striker_dismissed" not in df.columns:
        if "is_wicket" in df.columns and "striker_id" in df.columns and "dismissed_player_id" in df.columns:
            df["is_striker_dismissed"] = (
                df["is_wicket"] & (df["striker_id"] == df["dismissed_player_id"])
            ).astype(int)
        elif "is_dismissal" in df.columns:
            df["is_striker_dismissed"] = df["is_dismissal"].astype(int)
        else:
            df["is_striker_dismissed"] = 0
        
    # Wickets Above Expected for striker
    if "expected_wicket_prob" in df.columns:
        df["striker_wae"] = df["is_striker_dismissed"] - df["expected_wicket_prob"]
    else:
        df["striker_wae"] = 0.0
        
    # Boundary tracking
    df["is_dot"] = ((df["batter_runs"] == 0) & (df["is_legal_ball"])).astype(int)
    is_four = df["is_four"] if "is_four" in df.columns else pd.Series(False, index=df.index)
    is_six = df["is_six"] if "is_six" in df.columns else pd.Series(False, index=df.index)
    df["is_boundary"] = (is_four | is_six).astype(int)
    
    return df
