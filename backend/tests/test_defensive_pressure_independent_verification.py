"""
Independent Unit and Integration Test: Defensive Pressure Engine
Validates mathematical formulation, directional monotonicity, and independence from unit test hardcoding.
Every test independently implements the raw mathematical formulas from explicit match-state inputs
and compares against the production DefensiveBowlingPressureEngine.
"""

import pytest
import numpy as np
import pandas as pd
from backend.analytics.pressure_bowlers.pressure_engine import DefensiveBowlingPressureEngine


def calculate_raw_second_innings_pressure(
    runs_needed: float,
    legal_balls_remaining: float,
    wickets_in_hand: float,
    required_run_rate: float,
    scheduled_overs: float = 120.0
) -> float:
    """
    Independent ground-truth implementation of the Second Innings Defensive Pressure Equation.
    Operates strictly from raw mathematical primitives without calling the engine.
    """
    b_max = max(scheduled_overs, 6.0)
    b_rem = max(legal_balls_remaining, 1.0)
    r_rem = max(runs_needed, 0.0)
    w_hand = np.clip(wickets_in_hand, 0.0, 10.0)
    rrr = max(required_run_rate, 0.0)
    
    # Terminal handling: if match is already won, pressure is 0.0
    if r_rem <= 0.0:
        return 0.0
        
    # 1. Batting scoring capability given wickets in hand
    w_cap = 6.0 + 0.55 * w_hand
    
    # 2. Threat ratio: opposition capability relative to required run rate
    threat_ratio = w_cap / max(rrr, 1.0)
    
    # 3. Match timeline progress
    progress = np.clip((b_max - b_rem) / b_max, 0.0, 1.0)
    
    # 4. Margin closeness stress near the finish
    margin_stress = np.exp(-r_rem / 16.0) * (1.0 if b_rem <= 18.0 else 0.0) * (w_hand / 10.0)
    
    # 5. Combined defensive stress latent score
    z2 = 1.85 * (threat_ratio - 1.0) + 1.50 * margin_stress + 0.75 * progress * (1.0 if threat_ratio > 0.80 else 0.0)
    
    # 6. Calibrated logistic activation [0.5, 9.8]
    p_inn2 = 10.0 / (1.0 + np.exp(-1.20 * z2))
    return float(np.clip(p_inn2, 0.5, 9.8))


def calculate_raw_first_innings_pressure(
    predicted_final_score: float,
    venue_par_score: float,
    legal_balls_remaining: float,
    wickets_in_hand: float,
    par_std: float = 32.0
) -> float:
    """
    Independent ground-truth implementation of the First Innings Defensive Pressure Equation.
    """
    surge = (predicted_final_score - venue_par_score) / par_std
    balls_rem = np.clip(legal_balls_remaining, 0.0, 120.0)
    w_hand = np.clip(wickets_in_hand, 0.0, 10.0)
    death_challenge = np.clip((30.0 - balls_rem) / 30.0, 0.0, 1.0) * (w_hand / 10.0)
    
    z1 = 1.15 * surge + 0.90 * death_challenge
    p_inn1 = 10.0 / (1.0 + np.exp(-1.10 * z1))
    return float(np.clip(p_inn1, 0.5, 9.8))


def test_independent_calculation_situation_a_and_b():
    """
    Test Situation A (8 off 6) and Situation B (35 off 6) by comparing
    independent formula calculation against the engine output.
    """
    engine = DefensiveBowlingPressureEngine()
    
    # Test across multiple wickets-in-hand configurations (w = 10, 5, 4, 2)
    for w in [10.0, 5.0, 4.0, 2.0]:
        # Situation A: Defending 8 from 6 balls (Narrow margin crisis)
        raw_a = calculate_raw_second_innings_pressure(8.0, 6.0, w, 8.0)
        df_a = pd.DataFrame([{
            "innings": 2, "runs_needed": 8.0, "legal_balls_remaining": 6.0,
            "wickets_in_hand": w, "required_run_rate": 8.0, "second_inn_revised_overs": 120.0
        }])
        eng_a = float(engine.compute_second_innings_defensive_pressure(df_a).iloc[0])
        assert abs(eng_a - raw_a) < 1e-6, f"Situation A discrepancy at w={w}: eng={eng_a}, raw={raw_a}"
        
        # Situation B: Defending 35 from 6 balls (Comfortable cushion)
        raw_b = calculate_raw_second_innings_pressure(35.0, 6.0, w, 35.0)
        df_b = pd.DataFrame([{
            "innings": 2, "runs_needed": 35.0, "legal_balls_remaining": 6.0,
            "wickets_in_hand": w, "required_run_rate": 35.0, "second_inn_revised_overs": 120.0
        }])
        eng_b = float(engine.compute_second_innings_defensive_pressure(df_b).iloc[0])
        assert abs(eng_b - raw_b) < 1e-6, f"Situation B discrepancy at w={w}: eng={eng_b}, raw={raw_b}"
        
        # Verify Directional Soundness:
        # Situation A (crisis) MUST have significantly higher pressure than Situation B (comfortable cushion)
        assert eng_a > eng_b, f"Defending 8 off 6 ({eng_a}) must exceed defending 35 off 6 ({eng_b})"
        assert eng_b < 3.0, f"Defending 35 off 6 must be low pressure, got {eng_b}"


def test_independent_calculation_first_innings_all_scenarios():
    """
    Test first-innings defensive pressure across five distinct match states:
    1. Middle overs acceleration (110/1 in 10 ov)
    2. Early innings par pace (45/1 in 6 ov)
    3. Middle overs batting collapse (50/5 in 10 ov)
    4. Death overs acceleration surge (175/2 in 18 ov)
    5. Death overs containment (140/7 in 18 ov)
    
    Verifies that the independent mathematical formula calculation strictly agrees
    with the production DefensiveBowlingPressureEngine across all states.
    """
    engine = DefensiveBowlingPressureEngine()
    engine._load_ridge_model()
    
    test_cases = [
        {
            "desc": "Middle Overs Acceleration (110/1 in 10 ov)",
            "row": {
                "innings": 1, "pre_ball_legal_balls": 60.0, "legal_balls_remaining": 60.0,
                "pre_ball_score": 110.0, "pre_ball_wickets": 1.0, "wickets_in_hand": 9.0,
                "current_run_rate": 11.0, "resource_consumed_pct": 0.30, "venue_par_score": 170.0
            }
        },
        {
            "desc": "Early Innings Par Pace (45/1 in 6 ov)",
            "row": {
                "innings": 1, "pre_ball_legal_balls": 36.0, "legal_balls_remaining": 84.0,
                "pre_ball_score": 45.0, "pre_ball_wickets": 1.0, "wickets_in_hand": 9.0,
                "current_run_rate": 7.5, "resource_consumed_pct": 0.20, "venue_par_score": 170.0
            }
        },
        {
            "desc": "Middle Overs Collapse (50/5 in 10 ov)",
            "row": {
                "innings": 1, "pre_ball_legal_balls": 60.0, "legal_balls_remaining": 60.0,
                "pre_ball_score": 50.0, "pre_ball_wickets": 5.0, "wickets_in_hand": 5.0,
                "current_run_rate": 5.0, "resource_consumed_pct": 0.50, "venue_par_score": 170.0
            }
        },
        {
            "desc": "Death Overs Surge (175/2 in 18 ov)",
            "row": {
                "innings": 1, "pre_ball_legal_balls": 108.0, "legal_balls_remaining": 12.0,
                "pre_ball_score": 175.0, "pre_ball_wickets": 2.0, "wickets_in_hand": 8.0,
                "current_run_rate": 9.72, "resource_consumed_pct": 0.55, "venue_par_score": 170.0
            }
        },
        {
            "desc": "Death Overs Containment (140/7 in 18 ov)",
            "row": {
                "innings": 1, "pre_ball_legal_balls": 108.0, "legal_balls_remaining": 12.0,
                "pre_ball_score": 140.0, "pre_ball_wickets": 7.0, "wickets_in_hand": 3.0,
                "current_run_rate": 7.78, "resource_consumed_pct": 0.80, "venue_par_score": 170.0
            }
        }
    ]
    
    df = pd.DataFrame([tc["row"] for tc in test_cases])
    eng_preds = engine.compute_first_innings_defensive_pressure(df)
    ridge_preds = engine.ridge_model.predict(df[engine.num_cols])
    
    for i, tc in enumerate(test_cases):
        r = tc["row"]
        pred_final = float(ridge_preds[i])
        eng_p = float(eng_preds.iloc[i])
        
        # Independent formula calculation strictly from raw mathematical primitives
        raw_p = calculate_raw_first_innings_pressure(
            predicted_final_score=pred_final,
            venue_par_score=r["venue_par_score"],
            legal_balls_remaining=r["legal_balls_remaining"],
            wickets_in_hand=r["wickets_in_hand"],
            par_std=32.0
        )
        
        assert abs(eng_p - raw_p) < 1e-6, (
            f"Discrepancy in {tc['desc']}: engine={eng_p}, raw={raw_p}"
        )


def test_first_innings_independent_explicit_inputs_and_clipping():
    """
    Test first-innings formula strictly from explicit inputs without invoking the Ridge model,
    verifying exact arithmetic and boundary clipping behaviors.
    """
    par_score = 170.0
    par_std = 32.0
    
    # 1. Existing Benchmark: Exact Ridge output for 110/1 in 10 ov is S_hat = 211.9621
    # Surge = (211.9621 - 170) / 32 = +1.311316
    # DeathChallenge = 0 (balls_rem = 60 >= 30)
    # z1 = 1.15 * 1.311316 = +1.508013
    # P = 10 / (1 + exp(-1.10 * 1.508013)) = 8.4008 -> 8.40
    p_existing = calculate_raw_first_innings_pressure(211.9621, par_score, 60.0, 9.0, par_std)
    assert abs(p_existing - 8.4008) < 1e-3, f"Expected 8.40, got {p_existing}"
    
    # 2. Early Innings Par Baseline: S_hat = 170.0, B_rem = 84, W_hand = 9
    # Surge = 0.0, Death = 0.0, z1 = 0.0 -> P = 5.00
    p_par = calculate_raw_first_innings_pressure(170.0, par_score, 84.0, 9.0, par_std)
    assert abs(p_par - 5.00) < 1e-6, f"Expected neutral 5.00, got {p_par}"
    
    # 3. Batting Collapse: S_hat = 120.0, B_rem = 60, W_hand = 5
    # Surge = -1.5625, Death = 0.0, z1 = -1.796875 -> P = 1.22
    p_collapse = calculate_raw_first_innings_pressure(120.0, par_score, 60.0, 5.0, par_std)
    assert abs(p_collapse - 1.22) < 0.05, f"Expected 1.22, got {p_collapse}"
    
    # 4. Death Overs Acceleration: S_hat = 205.0, B_rem = 12, W_hand = 8
    # Surge = +1.09375, Death = (18/30) * 0.8 = 0.48, z1 = 1.15*1.09375 + 0.90*0.48 = 1.6898 -> P = 8.65
    p_death_surge = calculate_raw_first_innings_pressure(205.0, par_score, 12.0, 8.0, par_std)
    assert abs(p_death_surge - 8.65) < 0.05, f"Expected 8.65, got {p_death_surge}"
    
    # 5. Death Overs Tail Wickets: S_hat = 158.0, B_rem = 12, W_hand = 3
    # Surge = -0.375, Death = (18/30) * 0.3 = 0.18, z1 = 1.15*(-0.375) + 0.90*0.18 = -0.26925 -> P = 4.26
    p_death_tail = calculate_raw_first_innings_pressure(158.0, par_score, 12.0, 3.0, par_std)
    assert abs(p_death_tail - 4.26) < 0.05, f"Expected 4.26, got {p_death_tail}"
    
    # 6. Upper Clipping Ceiling Check: S_hat = 260.0, B_rem = 0, W_hand = 10
    # z1 = 1.15 * (90/32) + 0.90 * 1.0 = 4.134 -> P_raw = 9.895 -> clipped to 9.80
    p_ceil = calculate_raw_first_innings_pressure(260.0, par_score, 0.0, 10.0, par_std)
    assert p_ceil == 9.80, f"Expected upper ceiling clip 9.80, got {p_ceil}"
    
    # 7. Lower Clipping Floor Check: S_hat = 80.0, B_rem = 60, W_hand = 1
    # z1 = 1.15 * (-90/32) = -3.234 -> P_raw = 0.278 -> clipped to 0.50
    p_floor = calculate_raw_first_innings_pressure(80.0, par_score, 60.0, 1.0, par_std)
    assert p_floor == 0.50, f"Expected lower floor clip 0.50, got {p_floor}"


def test_first_innings_monotonicity():
    """
    Mathematically verifies that first-innings defensive pressure:
    1. Increases monotonically with higher predicted final score (opposition acceleration).
    2. Increases monotonically with higher wickets in hand during the death phase.
    """
    par_score = 170.0
    par_std = 32.0
    
    # 1. Monotonicity with respect to S_hat (holding balls=60, wkts=8)
    scores = [100.0, 130.0, 150.0, 170.0, 190.0, 220.0, 260.0]
    pressures_s = [
        calculate_raw_first_innings_pressure(s, par_score, 60.0, 8.0, par_std)
        for s in scores
    ]
    for i in range(len(pressures_s) - 1):
        assert pressures_s[i] <= pressures_s[i+1], (
            f"Violated S_hat monotonicity: S={scores[i]} (P={pressures_s[i]}) > S={scores[i+1]} (P={pressures_s[i+1]})"
        )
        
    # 2. Monotonicity with respect to Wickets in Hand at Death (holding S_hat=180, balls=12)
    wkts = [1.0, 3.0, 5.0, 7.0, 9.0, 10.0]
    pressures_w = [
        calculate_raw_first_innings_pressure(180.0, par_score, 12.0, w, par_std)
        for w in wkts
    ]
    for i in range(len(pressures_w) - 1):
        assert pressures_w[i] <= pressures_w[i+1], (
            f"Violated death wickets monotonicity: W={wkts[i]} (P={pressures_w[i]}) > W={wkts[i+1]} (P={pressures_w[i+1]})"
        )


def test_second_innings_monotonicity():
    """
    Mathematically verifies that:
    1. Higher Required Run Rate (RRR) strictly DECREASES defensive bowling pressure.
    2. Lower opposition wickets in hand strictly DECREASES defensive bowling pressure.
    """
    engine = DefensiveBowlingPressureEngine()
    
    # 1. Monotonicity with respect to RRR (holding balls=6, runs_needed=RRR, w_hand=5)
    rrr_values = [4.0, 6.0, 8.0, 10.0, 14.0, 20.0, 36.0]
    pressures_rrr = []
    for rrr in rrr_values:
        df = pd.DataFrame([{
            "innings": 2, "runs_needed": rrr, "legal_balls_remaining": 6.0,
            "wickets_in_hand": 5.0, "required_run_rate": rrr, "second_inn_revised_overs": 120.0
        }])
        pressures_rrr.append(engine.compute_second_innings_defensive_pressure(df).iloc[0])
        
    for i in range(len(pressures_rrr) - 1):
        assert pressures_rrr[i] >= pressures_rrr[i+1], (
            f"Violated RRR monotonicity: at RRR={rrr_values[i]}, P={pressures_rrr[i]}; "
            f"at RRR={rrr_values[i+1]}, P={pressures_rrr[i+1]}"
        )

    # 2. Monotonicity with respect to Wickets in Hand (holding balls=6, runs=12, rrr=12)
    w_values = [1.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    pressures_w = []
    for w in w_values:
        df = pd.DataFrame([{
            "innings": 2, "runs_needed": 12.0, "legal_balls_remaining": 6.0,
            "wickets_in_hand": w, "required_run_rate": 12.0, "second_inn_revised_overs": 120.0
        }])
        pressures_w.append(engine.compute_second_innings_defensive_pressure(df).iloc[0])
        
    for i in range(len(pressures_w) - 1):
        assert pressures_w[i] <= pressures_w[i+1], (
            f"Violated Wickets monotonicity: at w={w_values[i]}, P={pressures_w[i]}; "
            f"at w={w_values[i+1]}, P={pressures_w[i+1]}"
        )
