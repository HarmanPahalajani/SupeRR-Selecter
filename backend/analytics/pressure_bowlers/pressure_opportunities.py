"""
Pressure Opportunities Identification Module for Bowlers
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Identifies qualifying high-pressure bowling opportunities based strictly on
pre-delivery defensive match state, isolating scopes and innings contexts.
"""

from typing import Dict, Tuple
import pandas as pd
import numpy as np

# Validated Empirical 75th Percentile Thresholds (Frozen from training/validation data)
PRIMARY_BOWLING_THRESHOLDS_75TH = {
    1: 6.91,  # First-innings opposition restriction threshold
    2: 7.79,  # Second-innings target defence threshold
}

EMERGING_BOWLING_THRESHOLDS_75TH = {
    1: 5.62,  # Emerging first-innings threshold
    2: 8.41,  # Emerging target defence threshold
}

# Sensitivity Scenarios across Percentiles
SENSITIVITY_BOWLING_THRESHOLDS = {
    "p70": {
        "primary": {1: 6.52, 2: 7.43},
        "emerging": {1: 5.42, 2: 8.15}
    },
    "p75": {
        "primary": {1: 6.91, 2: 7.79},
        "emerging": {1: 5.62, 2: 8.41}
    },
    "p80": {
        "primary": {1: 7.34, 2: 8.21},
        "emerging": {1: 5.89, 2: 8.74}
    },
    "p85": {
        "primary": {1: 7.84, 2: 8.74},
        "emerging": {1: 6.21, 2: 9.30}
    },
}


def tag_high_pressure_bowling_deliveries(
    df: pd.DataFrame,
    threshold_variant: str = "p75",
    is_primary: bool = True
) -> pd.DataFrame:
    """
    Tags each delivery as high-pressure bowling based on pre-delivery defensive pressure index.
    
    Guarantees:
    - Never uses delivery outcome to determine pressure.
    - Separates Innings 1 (Restriction) from Innings 2 (Target Defence).
    - Excludes Super Overs strictly.
    """
    df = df.copy()
    
    # Filter out super overs strictly
    if "is_super_over" in df.columns:
        df = df[~df["is_super_over"]].copy()
        
    scope_key = "primary" if is_primary else "emerging"
    thresholds = SENSITIVITY_BOWLING_THRESHOLDS.get(
        threshold_variant, {}
    ).get(scope_key, PRIMARY_BOWLING_THRESHOLDS_75TH if is_primary else EMERGING_BOWLING_THRESHOLDS_75TH)
        
    t_inn1 = thresholds[1]
    t_inn2 = thresholds[2]
    
    # Ensure bowling_pressure_index column is present
    if "bowling_pressure_index" not in df.columns:
        raise ValueError("Column 'bowling_pressure_index' must be computed before tagging opportunities.")
    
    # Pre-delivery pressure condition
    cond_inn1 = (df["innings"] == 1) & (df["bowling_pressure_index"] >= t_inn1)
    cond_inn2 = (df["innings"] == 2) & (df["bowling_pressure_index"] >= t_inn2)
    
    df["is_high_pressure_bowling"] = cond_inn1 | cond_inn2
    df["bowling_pressure_context"] = np.where(
        df["innings"] == 2, "CHASE_DEFENCE",
        np.where(df["innings"] == 1, "FIRST_INNINGS_RESTRICTION", "OTHER")
    )
    
    return df
