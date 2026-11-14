"""
Defensive Bowling Pressure Engine
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Evaluates match difficulty and defensive threat strictly from the bowling team's perspective
using pre-delivery match state features.
"""

from typing import Tuple, Optional
import os
import joblib
import numpy as np
import pandas as pd


class DefensiveBowlingPressureEngine:
    def __init__(self, ridge_model_path: str = "backend/analytics/pressure/expected_score_ridge.joblib"):
        self.ridge_model_path = ridge_model_path
        self.ridge_model = None
        self.global_par = 174.25
        self.par_std = 32.0
        
        self.num_cols = [
            'pre_ball_legal_balls', 'legal_balls_remaining', 'pre_ball_score',
            'pre_ball_wickets', 'wickets_in_hand', 'current_run_rate',
            'resource_consumed_pct', 'venue_par_score'
        ]

    def _load_ridge_model(self):
        if self.ridge_model is None and os.path.exists(self.ridge_model_path):
            self.ridge_model = joblib.load(self.ridge_model_path)

    def compute_first_innings_defensive_pressure(self, df_inn1: pd.DataFrame) -> pd.Series:
        """
        Evaluates defensive pressure in the first innings.
        The bowling side's challenge is to restrict opposition acceleration and prevent a surge above par.
        """
        self._load_ridge_model()
        df = df_inn1.copy()
        
        if "venue_par_score" not in df.columns:
            df["venue_par_score"] = self.global_par
        else:
            df["venue_par_score"] = df["venue_par_score"].fillna(self.global_par).astype(float)
            
        if "resource_consumed_pct" not in df.columns:
            pb_balls = df["pre_ball_legal_balls"] if "pre_ball_legal_balls" in df.columns else 0.0
            pb_wkts = df["pre_ball_wickets"] if "pre_ball_wickets" in df.columns else 0.0
            df["resource_consumed_pct"] = 0.5 * (pb_balls / 120.0) + 0.5 * (pb_wkts / 10.0)

        # Predict expected final score using pre-delivery ridge model
        if self.ridge_model is not None:
            pred_final = self.ridge_model.predict(df[self.num_cols])
        else:
            # Fallback projection if model artifact not available
            crr = df["current_run_rate"].values
            balls_rem = df["legal_balls_remaining"].values
            score_curr = df["pre_ball_score"].values
            pred_final = score_curr + crr * (balls_rem / 6.0)

        # Standardized opposition surge above venue par
        venue_par = df["venue_par_score"].values
        surge = (pred_final - venue_par) / self.par_std

        # Death phase tension (last 5 overs when opposition has wickets in hand)
        balls_rem = np.clip(df["legal_balls_remaining"].values, 0.0, 120.0)
        wkts_in_hand = np.clip(df["wickets_in_hand"].values, 0.0, 10.0)
        death_challenge = np.clip((30.0 - balls_rem) / 30.0, 0.0, 1.0) * (wkts_in_hand / 10.0)

        # Calibrated logistic score [0.5, 9.8]
        z1 = 1.15 * surge + 0.90 * death_challenge
        p_inn1 = 10.0 / (1.0 + np.exp(-1.10 * z1))
        p_inn1 = np.clip(p_inn1, 0.5, 9.8)
        
        return pd.Series(p_inn1, index=df_inn1.index, name="bowling_pressure_index")

    def compute_second_innings_defensive_pressure(self, df_inn2: pd.DataFrame) -> pd.Series:
        """
        Evaluates defensive pressure in the second innings (defending a target).
        Bowler faces high pressure when the batting team is positioned to threaten or overrun the target.
        """
        df = df_inn2.copy()
        
        r_rem = np.maximum(df["runs_needed"].fillna(0.0).values, 0.0)
        b_rem = np.maximum(df["legal_balls_remaining"].fillna(120.0).values, 1.0)
        w_hand = np.clip(df["wickets_in_hand"].fillna(10.0).values, 0.0, 10.0)
        
        # Determine effective scheduled balls
        has_rev_o = "second_inn_revised_overs" in df.columns
        b_max = np.where(
            has_rev_o and (df["second_inn_revised_overs"].notna() & (df["second_inn_revised_overs"] > 0)),
            df["second_inn_revised_overs"] if has_rev_o else 120.0,
            120.0
        ).astype(float)
        b_max = np.maximum(b_max, 6.0)
        
        rrr = np.maximum(df["required_run_rate"].fillna(8.0).values, 0.0)

        # Batting scoring potential with w_hand wickets
        w_cap = 6.0 + 0.55 * w_hand
        
        # Threat ratio: capability vs required rate
        threat_ratio = w_cap / np.maximum(rrr, 1.0)
        progress = np.clip((b_max - b_rem) / b_max, 0.0, 1.0)
        
        # Margin closeness stress (narrow runs remaining near finish)
        margin_stress = np.exp(-r_rem / 16.0) * (b_rem <= 18.0) * (w_hand / 10.0)

        # Combined defensive stress formulation
        z2 = 1.85 * (threat_ratio - 1.0) + 1.50 * margin_stress + 0.75 * progress * (threat_ratio > 0.80)
        p_inn2 = 10.0 / (1.0 + np.exp(-1.20 * z2))
        p_inn2 = np.clip(p_inn2, 0.5, 9.8)
        
        # Explicit terminal handling: if match is already won (runs_needed <= 0), pressure drops to 0.0
        p_inn2 = np.where(r_rem <= 0.0, 0.0, p_inn2)
        
        return pd.Series(p_inn2, index=df_inn2.index, name="bowling_pressure_index")

    def compute_defensive_pressure(self, df: pd.DataFrame) -> pd.Series:
        """
        Computes bowling-side defensive pressure across both innings.
        """
        out_series = pd.Series(5.0, index=df.index, dtype=float, name="bowling_pressure_index")
        
        inn1_mask = df["innings"] == 1
        if inn1_mask.sum() > 0:
            out_series.loc[inn1_mask] = self.compute_first_innings_defensive_pressure(df[inn1_mask])
            
        inn2_mask = df["innings"] == 2
        if inn2_mask.sum() > 0:
            out_series.loc[inn2_mask] = self.compute_second_innings_defensive_pressure(df[inn2_mask])
            
        return out_series
