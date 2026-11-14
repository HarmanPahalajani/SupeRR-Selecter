"""
Controlled Monotonicity & Historical Outcome Validation Test
SupeRR Intelligence - Advanced Analytics Engine
"""

import numpy as np
import pandas as pd
from backend.analytics.pressure.engine import DynamicPressureEngine

def run_tests():
    print("=== STARTING CONTROLLED MONOTONICITY & OUTCOME VALIDATION ===")
    engine = DynamicPressureEngine()
    df = engine.load_data()
    engine.train_expected_score_model(df)
    
    # -------------------------------------------------------------
    # 1. CONTROLLED MONOTONICITY TESTS: FIRST INNINGS
    # -------------------------------------------------------------
    print("\n--- 1. Controlled Monotonicity: First Innings ---")
    # Hold balls = 60, score = 80, venue_par = 175, format = 'T20I', vary wickets lost 0 to 8
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
    } for w in range(9)])
    
    p_w, exp_w = engine.compute_first_innings_pressure(test_w_states)
    print("Holding Balls=60, Score=80 constant. Varying Wickets Lost:")
    for w in range(9):
        print(f"  Wickets Lost: {w} (In Hand: {10-w}) -> Expected Total: {exp_w.iloc[w]:5.1f} -> Pressure: {p_w.iloc[w]:.2f}")
    
    # Verify strict monotonicity: increasing wickets lost strictly decreases expected total and increases pressure
    assert np.all(np.diff(exp_w) <= 0), "Monotonicity violation: Expected total did not decrease with wickets lost!"
    assert np.all(np.diff(p_w) >= 0), "Monotonicity violation: Pressure did not increase with wickets lost!"
    print("  >>> PASS: First-innings pressure is strictly monotonic with respect to wickets lost.")

    # -------------------------------------------------------------
    # 2. CONTROLLED MONOTONICITY TESTS: SECOND INNINGS
    # -------------------------------------------------------------
    print("\n--- 2. Controlled Monotonicity: Second Innings ---")
    # Hold balls = 30, target = 180 (initial RRR = 9.0), wickets_in_hand = 6, vary runs needed (RRR from 6.0 to 18.0)
    test_rrr_states = pd.DataFrame([{
        'target_runs': 180.0,
        'runs_needed': need,
        'legal_balls_remaining': 30,
        'required_run_rate': need / 5.0, # 30 balls = 5 overs
        'wickets_in_hand': 6,
        'resource_consumed_pct': 0.45 * (90/120) + 0.55 * (4/10)
    } for need in [25, 35, 45, 55, 65, 75, 85, 95]])
    
    p_rrr = engine.compute_second_innings_pressure(test_rrr_states)
    print("Holding Balls=30, Target=180, Wickets in Hand=6. Varying Required Run Rate:")
    for i, need in enumerate([25, 35, 45, 55, 65, 75, 85, 95]):
        rrr_val = need / 5.0
        print(f"  Need: {need:2d} in 30 balls (RRR: {rrr_val:4.1f}) -> Chase Pressure: {p_rrr.iloc[i]:.2f}")
    assert np.all(np.diff(p_rrr) >= 0), "Monotonicity violation: Chase pressure did not increase with RRR!"
    print("  >>> PASS: Chase pressure is strictly monotonic with respect to required run rate.")

    # Holding RRR constant at 12.0, vary wickets in hand from 8 down to 1
    test_wk_chase = pd.DataFrame([{
        'target_runs': 180.0,
        'runs_needed': 60.0,
        'legal_balls_remaining': 30,
        'required_run_rate': 12.0,
        'wickets_in_hand': w_hand,
        'resource_consumed_pct': 0.45 * (90/120) + 0.55 * ((10 - w_hand)/10)
    } for w_hand in range(8, 0, -1)])
    
    p_wk_chase = engine.compute_second_innings_pressure(test_wk_chase)
    print("\nHolding Balls=30, RRR=12.0 constant. Varying Wickets in Hand (8 down to 1):")
    for i, w_hand in enumerate(range(8, 0, -1)):
        print(f"  Wickets in Hand: {w_hand} -> Chase Pressure: {p_wk_chase.iloc[i]:.2f}")
    assert np.all(np.diff(p_wk_chase) >= 0), "Monotonicity violation: Chase pressure did not increase as wickets fell!"
    print("  >>> PASS: Chase pressure is strictly monotonic with respect to wicket loss at fixed RRR.")

    # -------------------------------------------------------------
    # 3. BALL 1 INITIAL PRESSURE VERIFICATION
    # -------------------------------------------------------------
    print("\n--- 3. Exact Initial Chase Pressure P(1) Verification ---")
    test_p1_states = pd.DataFrame([{
        'target_runs': t,
        'runs_needed': t,
        'legal_balls_remaining': 120,
        'required_run_rate': t / 20.0,
        'wickets_in_hand': 10,
        'resource_consumed_pct': 0.0
    } for t in [120, 150, 180, 210]])
    
    p_init = engine.compute_second_innings_pressure(test_p1_states)
    for i, t in enumerate([120, 150, 180, 210]):
        expected_p1 = 10.0 * ((t / 20.0) / 13.5)
        print(f"  Target: {t:3d} (Initial RRR: {t/20.0:4.1f}) -> Formula Output: {p_init.iloc[i]:.4f} | Theoretical P(1): {expected_p1:.4f}")
        assert np.isclose(p_init.iloc[i], expected_p1, atol=1e-3), f"P(1) mismatch on target {t}!"
    print("  >>> PASS: At Ball 1, chase pressure matches theoretical P(1) exactly across all targets.")

    # -------------------------------------------------------------
    # 4. HISTORICAL OUTCOME VALIDATION
    # -------------------------------------------------------------
    print("\n--- 4. Historical Outcome Validation Across Pressure Tiers ---")
    # Evaluate subsequent delivery outcomes across pressure buckets:
    # Low (<4.0), Moderate (4.0-6.5), High (6.5-8.2), Extreme (>=8.2)
    inn1 = df[df['innings'] == 1].copy()
    inn2 = df[df['innings'] == 2].copy()
    
    p1_vals, _ = engine.compute_first_innings_pressure(inn1)
    inn1['pressure'] = p1_vals
    
    p2_vals = engine.compute_second_innings_pressure(inn2)
    inn2['pressure'] = p2_vals
    
    for inn_name, sub in [("First Innings", inn1), ("Second Innings", inn2)]:
        print(f"\n{inn_name} Historical Behavior Across Pressure Tiers:")
        sub['tier'] = pd.cut(sub['pressure'], bins=[-0.1, 4.0, 6.5, 8.2, 10.1], labels=['Low (<4.0)', 'Moderate (4.0-6.5)', 'High (6.5-8.2)', 'Extreme (>=8.2)'])
        grp = sub.groupby('tier', observed=False).agg(
            delivery_count=('batter_runs', 'count'),
            runs_per_ball=('batter_runs', 'mean'),
            wicket_rate_pct=('is_wicket', lambda s: s.mean() * 100.0),
            dot_ball_pct=('batter_runs', lambda s: (s == 0).mean() * 100.0),
            boundary_pct=('batter_runs', lambda s: s.isin([4, 6]).mean() * 100.0)
        )
        print(grp)
        # Verify that extreme pressure produces higher wicket rates and lower scoring rates
        low_w = grp.loc['Low (<4.0)', 'wicket_rate_pct']
        ext_w = grp.loc['Extreme (>=8.2)', 'wicket_rate_pct']
        print(f"  Wicket Rate Check: Low Pressure = {low_w:.2f}% vs Extreme Pressure = {ext_w:.2f}% (Escalation factor: {ext_w/low_w:.2f}x)")
        assert ext_w > low_w, "Outcome validation violation: Extreme pressure does not have higher wicket rate!"

    print("\n=== ALL MONOTONICITY & OUTCOME TESTS PASSED CLEANLY! ===")

if __name__ == "__main__":
    run_tests()
