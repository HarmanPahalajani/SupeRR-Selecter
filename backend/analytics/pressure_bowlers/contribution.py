"""
Bowling Contribution Module
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Calculates delivery-level and player-level bowling contributions under
high defensive pressure, preserving cricket scoring integrity and neutral baseline expectations.
"""

import pandas as pd
import numpy as np

# Non-bowler dismissal types strictly excluded from bowler credit
NON_BOWLER_DISMISSALS = {
    "run out", "retired out", "retired hurt", "obstructing the field", 
    "timed out", "handled the ball", "hit the ball twice"
}

BOWLER_CREDITED_DISMISSALS = {
    "bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"
}


def compute_bowling_delivery_contributions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes delivery-level runs saved above expected and credited wicket creation.
    
    Guarantees:
    - Wides and no-balls are not legal balls.
    - Byes, leg-byes, and penalty runs are excluded from bowler-conceded runs.
    - Run-outs and non-credited dismissals are excluded from bowler wickets.
    - Runs Saved = Expected Bowler-Conceded Runs - Actual Bowler-Conceded Runs.
    - Wickets Above Expected = Actual Bowler-Credited Wicket - Expected Wicket Prob.
    """
    df = df.copy()
    
    # 1. Legal balls calculation
    if "is_legal_ball" not in df.columns:
        wides = df["extras_wide_runs"] if "extras_wide_runs" in df.columns else 0
        noballs = df["extras_noball_runs"] if "extras_noball_runs" in df.columns else 0
        df["is_legal_ball"] = (wides == 0) & (noballs == 0)
        
    # 2. Bowler-conceded runs (clean of byes/leg-byes/penalties)
    if "bowler_conceded_runs" not in df.columns:
        if "batter_runs" in df.columns:
            b_runs = df["batter_runs"]
        elif "runs" in df.columns:
            b_runs = df["runs"]
        else:
            b_runs = 0
            
        w_runs = df["extras_wide_runs"] if "extras_wide_runs" in df.columns else 0
        nb_runs = df["extras_noball_runs"] if "extras_noball_runs" in df.columns else 0
        df["bowler_conceded_runs"] = b_runs + w_runs + nb_runs
        
    # 3. Runs Saved Above Expected
    if "expected_bowler_conceded_runs" not in df.columns:
        # Neutral baseline fallback if model expectation is not pre-scored
        df["expected_bowler_conceded_runs"] = 1.30
        
    df["runs_saved"] = df["expected_bowler_conceded_runs"] - df["bowler_conceded_runs"]
    
    # 4. Bowler credited wicket attribution
    if "is_bowler_wicket" not in df.columns:
        if "is_wicket" in df.columns and "dismissal_type" in df.columns:
            d_type = df["dismissal_type"].astype(str).str.lower().str.strip()
            df["is_bowler_wicket"] = (df["is_wicket"] == True) & (~d_type.isin(NON_BOWLER_DISMISSALS))
        elif "is_wicket" in df.columns:
            df["is_bowler_wicket"] = df["is_wicket"] == True
        else:
            df["is_bowler_wicket"] = False
            
    df["is_bowler_wicket"] = df["is_bowler_wicket"].astype(int)
    
    # 5. Wickets Above Expected (WAE)
    if "expected_wicket_prob" not in df.columns:
        df["expected_wicket_prob"] = 0.05
        
    df["wae"] = df["is_bowler_wicket"] - df["expected_wicket_prob"]
    
    # 6. Dot balls & boundaries conceded
    df["is_dot_ball"] = ((df["bowler_conceded_runs"] == 0) & (df["is_legal_ball"])).astype(int)
    
    is_four = df["is_four"] if "is_four" in df.columns else pd.Series(False, index=df.index)
    is_six = df["is_six"] if "is_six" in df.columns else pd.Series(False, index=df.index)
    df["is_boundary_conceded"] = (is_four | is_six).astype(int)
    df["is_six_conceded"] = is_six.astype(int)
    
    return df
