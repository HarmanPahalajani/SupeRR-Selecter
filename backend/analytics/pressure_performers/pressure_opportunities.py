"""
Pressure Opportunities Identification Module
Part of SupeRR Intelligence — Pressure Performer Intelligence

Identifies qualifying high-pressure batting opportunities based strictly on
pre-delivery match state, isolating scopes and innings contexts.
"""

from typing import Dict, Tuple
import pandas as pd
import numpy as np

# Validated Empirical Thresholds (75th percentile on training data)
PRIMARY_THRESHOLDS_75TH = {
    1: 5.83,  # First-innings acceleration pressure threshold
    2: 8.60,  # Second-innings chase pressure threshold
}

EMERGING_THRESHOLDS_75TH = {
    1: 6.59,  # Emerging first-innings threshold
    2: 7.99,  # Emerging chase threshold
}

# Sensitivity Scenarios
SENSITIVITY_THRESHOLDS = {
    "p70": {1: 5.60, 2: 8.30},
    "p75": {1: 5.83, 2: 8.60},
    "p80": {1: 6.10, 2: 8.96},
    "p85": {1: 6.47, 2: 9.34},
}


def tag_high_pressure_deliveries(
    df: pd.DataFrame,
    threshold_variant: str = "p75",
    is_primary: bool = True
) -> pd.DataFrame:
    """
    Tags each delivery as high-pressure based on pre-delivery pressure index.
    
    Guarantees:
    - Never uses delivery outcome to determine pressure.
    - Separates Innings 1 (acceleration) from Innings 2 (chase).
    - Excludes Super Overs.
    """
    df = df.copy()
    
    # Filter out super overs strictly
    if "is_super_over" in df.columns:
        df = df[~df["is_super_over"]].copy()
        
    if is_primary:
        thresholds = SENSITIVITY_THRESHOLDS.get(threshold_variant, PRIMARY_THRESHOLDS_75TH)
    else:
        thresholds = EMERGING_THRESHOLDS_75TH
        
    t_inn1 = thresholds[1]
    t_inn2 = thresholds[2]
    
    # Pre-delivery pressure condition
    cond_inn1 = (df["innings"] == 1) & (df["pressure_index"] >= t_inn1)
    cond_inn2 = (df["innings"] == 2) & (df["pressure_index"] >= t_inn2)
    
    df["is_high_pressure"] = cond_inn1 | cond_inn2
    df["pressure_context"] = np.where(
        df["innings"] == 2, "CHASE",
        np.where(df["innings"] == 1, "FIRST_INNINGS", "OTHER")
    )
    
    return df
