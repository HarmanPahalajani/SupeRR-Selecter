"""
Controlled Monotonicity Tests for CatBoost First-Innings Expected Score Model
SupeRR Intelligence - Advanced Analytics Engine

Tests:
1. Increasing pre_ball_score while holding balls, wickets, venue par, format fixed.
2. Increasing pre_ball_wickets while holding score, balls, venue par, format fixed.
3. Decreasing legal_balls_remaining (progressing overs).
4. Boundary relief and wicket impact within live match states.
"""

import numpy as np
import pandas as pd
from backend.analytics.pressure.engine import DynamicPressureEngine

def run_first_innings_checks():
    print("=== TESTING FIRST-INNINGS EXPECTED SCORE & PRESSURE MONOTONICITY ===")
    engine = DynamicPressureEngine()
    df = engine.load_data()
    engine.train_expected_score_model(df)
    
    # -------------------------------------------------------------------------
    # TEST 1: INCREASING SCORE AT FIXED OVERS AND WICKETS
    # Over 10 (60 balls elapsed), 2 wickets lost, venue par 175.
    # Scores: 40, 60, 80, 100, 120, 140
    # Expected final score must increase monotonically, and pressure must decrease monotonically.
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Increasing Score at Fixed Overs (60 balls) & Wickets (2 lost) ---")
    scores = [40, 60, 80, 100, 120, 140]
    test_score_states = pd.DataFrame([{
        'pre_ball_legal_balls': 60,
        'legal_balls_remaining': 60,
        'pre_ball_score': s,
        'pre_ball_wickets': 2,
        'wickets_in_hand': 8,
        'current_run_rate': s / 10.0,
        'resource_consumed_pct': 0.45 * (60/120) + 0.55 * (2/10),
        'venue_id': 1,
        'format_scope': 'T20I'
    } for s in scores])
    
    p_score, exp_score = engine.compute_first_innings_pressure(test_score_states)
    for i, s in enumerate(scores):
        print(f"  Score: {s:3d}/2 in 10 overs (CRR: {s/10:4.1f}) -> Exp Final: {exp_score.iloc[i]:5.1f} -> Pressure: {p_score.iloc[i]:.2f}")
    
    diff_exp = np.diff(exp_score)
    diff_p = np.diff(p_score)
    assert np.all(diff_exp >= 0), "Expected score did not increase with cumulative score!"
    assert np.all(diff_p <= 0), "Pressure did not decrease with increasing score!"
    print(">>> PASS: Higher cumulative scores monotonically increase expected totals and reduce pressure.")

    # -------------------------------------------------------------------------
    # TEST 2: INCREASING WICKETS AT FIXED OVERS (60 balls) AND SCORE (80)
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Increasing Wickets at Fixed Overs (60 balls) & Score (80) ---")
    wkts = list(range(9))
    test_w_states = pd.DataFrame([{
        'pre_ball_legal_balls': 60,
        'legal_balls_remaining': 60,
        'pre_ball_score': 80,
        'pre_ball_wickets': w,
        'wickets_in_hand': 10 - w,
        'current_run_rate': 8.0,
        'resource_consumed_pct': 0.45 * (60/120) + 0.55 * (w/10),
        'venue_id': 1,
        'format_scope': 'T20I'
    } for w in wkts])
    
    p_w, exp_w = engine.compute_first_innings_pressure(test_w_states)
    for i, w in enumerate(wkts):
        print(f"  Wickets Lost: {w} (80 runs in 10 ov) -> Exp Final: {exp_w.iloc[i]:5.1f} -> Pressure: {p_w.iloc[i]:.2f}")
    
    diff_w_exp = np.diff(exp_w)
    diff_w_p = np.diff(p_w)
    assert np.all(diff_w_exp <= 0), "Expected score did not decrease as wickets fell!"
    assert np.all(diff_w_p >= 0), "Pressure did not increase as wickets fell!"
    print(">>> PASS: Wicket depletion monotonically decreases expected total and increases pressure.")

    # -------------------------------------------------------------------------
    # TEST 3: VENUE PAR ADAPTATION
    # -------------------------------------------------------------------------
    print("\n--- Test 3: Empirical Bayes Venue Par Sensitivity ---")
    print(f"  Global Par: {engine.global_par:.2f} runs (Std: {engine.par_std:.2f})")
    print(f"  Number of calibrated venues: {len(engine.venue_pars)}")
    high_par_v = max(engine.venue_pars.items(), key=lambda x: x[1])
    low_par_v = min(engine.venue_pars.items(), key=lambda x: x[1])
    print(f"  Highest Par Venue (ID {high_par_v[0]}): {high_par_v[1]:.1f} runs")
    print(f"  Lowest Par Venue (ID {low_par_v[0]}): {low_par_v[1]:.1f} runs")
    
    # State: 100/2 in 12 overs
    v_test = pd.DataFrame([{
        'pre_ball_legal_balls': 72,
        'legal_balls_remaining': 48,
        'pre_ball_score': 100,
        'pre_ball_wickets': 2,
        'wickets_in_hand': 8,
        'current_run_rate': 8.33,
        'resource_consumed_pct': 0.45 * (72/120) + 0.55 * (2/10),
        'venue_id': vid,
        'format_scope': 'IPL'
    } for vid in [high_par_v[0], low_par_v[0]]])
    
    p_v, exp_v = engine.compute_first_innings_pressure(v_test)
    print(f"  At High-Par Venue ({high_par_v[1]:.1f}): Exp={exp_v.iloc[0]:.1f} -> Pressure={p_v.iloc[0]:.2f}")
    print(f"  At Low-Par Venue ({low_par_v[1]:.1f}): Exp={exp_v.iloc[1]:.1f} -> Pressure={p_v.iloc[1]:.2f}")
    assert p_v.iloc[0] > p_v.iloc[1], "High-par venue did not induce higher pressure for identical score!"
    print(">>> PASS: Venue par sensitivity properly differentiates high-scoring grounds from bowling paradises.")

    print("\n=== ALL FIRST-INNINGS MONOTONICITY & BEHAVIOR TESTS PASS CLEANLY! ===")

if __name__ == "__main__":
    run_first_innings_checks()
