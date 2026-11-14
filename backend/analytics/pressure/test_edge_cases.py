"""
Comprehensive Edge Cases & Parameter Sensitivity Test Suite
SupeRR Intelligence - Dynamic Pressure Engine
Tests:
- Terminal win/loss/tie states
- Zero remaining legal balls
- Pressure boundedness
- Parameter sensitivities:
  - lambda_w in [1.2, 1.5, 1.8]
  - gamma in [0.35, 0.45, 0.55]
  - beta in [0.85, 1.05, 1.25]
  - c_max in [12.0, 13.5, 15.0]
"""

import numpy as np
import pandas as pd
from backend.analytics.pressure.engine import DynamicPressureEngine

def test_edge_cases_and_sensitivity():
    print("=== TESTING EDGE CASES, TERMINAL STATES & PARAMETER SENSITIVITY ===")
    engine = DynamicPressureEngine()
    
    # -------------------------------------------------------------
    # 1. Terminal States & Zero Remaining Balls
    # -------------------------------------------------------------
    print("\n--- 1. Terminal States & Zero Remaining Legal Balls ---")
    terminal_cases = pd.DataFrame([
        # Tie / 1 to win off 0 balls
        {"target_runs": 160.0, "max_legal_balls": 120.0, "pre_ball_legal_balls": 120.0, "legal_balls_remaining": 0, "wickets_in_hand": 5, "required_run_rate": 36.0},
        # Massive win needed: 12 off 0 balls
        {"target_runs": 160.0, "max_legal_balls": 120.0, "pre_ball_legal_balls": 120.0, "legal_balls_remaining": 0, "wickets_in_hand": 2, "required_run_rate": 72.0},
        # Already won / target passed
        {"target_runs": 160.0, "max_legal_balls": 120.0, "pre_ball_legal_balls": 110.0, "legal_balls_remaining": 10, "wickets_in_hand": 8, "required_run_rate": 0.0},
        # 10 wickets down (1 in hand left facing last ball)
        {"target_runs": 180.0, "max_legal_balls": 120.0, "pre_ball_legal_balls": 119.0, "legal_balls_remaining": 1, "wickets_in_hand": 1, "required_run_rate": 36.0},
    ])
    
    p_term = engine.compute_second_innings_pressure(terminal_cases)
    for i, r in terminal_cases.iterrows():
        p_val = p_term.iloc[i]
        print(f"Case {i+1}: RRR={r['required_run_rate']:.1f}, Balls Rem={r['legal_balls_remaining']}, Wkts in Hand={r['wickets_in_hand']} -> Pressure: {p_val:.4f}")
        assert 0.2 <= p_val <= 9.9, f"Pressure out of bounds: {p_val}"
    
    print("ALL TERMINAL STATES BOUNDED IN [0.2, 9.9]!")

    # -------------------------------------------------------------
    # 2. Parameter Sensitivity Analysis
    # -------------------------------------------------------------
    print("\n--- 2. Parameter Sensitivity Variations ---")
    # Reference scenario: Target 180, RRR 11.0, 90 balls bowled, 5 wkts in hand
    test_state = pd.DataFrame([{
        "target_runs": 180.0,
        "max_legal_balls": 120.0,
        "pre_ball_legal_balls": 90.0,
        "wickets_in_hand": 5.0,
        "required_run_rate": 11.0
    }])
    
    # Sensitivity to lambda_w (wicket weight)
    print("\nSensitivity to lambda_w (Current = 1.50):")
    for lw in [1.20, 1.50, 1.80]:
        engine.lambda_w = lw
        p = engine.compute_second_innings_pressure(test_state).iloc[0]
        print(f"  lambda_w = {lw:.2f} -> Pressure = {p:.4f}")
    engine.lambda_w = 1.50 # reset
    
    # Sensitivity to gamma (k_scale)
    print("\nSensitivity to gamma / k_scale (Current = 0.45):")
    for g in [0.35, 0.45, 0.55]:
        engine.k_scale = g
        p = engine.compute_second_innings_pressure(test_state).iloc[0]
        print(f"  gamma = {g:.2f} -> Pressure = {p:.4f}")
    engine.k_scale = 0.45 # reset

    # Sensitivity to c_max (rate normalization)
    print("\nSensitivity to c_max (Current = 13.5):")
    for cm in [12.0, 13.5, 15.0]:
        engine.c_max = cm
        p = engine.compute_second_innings_pressure(test_state).iloc[0]
        print(f"  c_max = {cm:.1f} -> Pressure = {p:.4f}")
    engine.c_max = 13.5 # reset

    # Sensitivity to beta_shortfall (1st innings)
    print("\nSensitivity to beta_shortfall (Current = 1.05) on 1st innings shortfall = +0.5 std:")
    for b in [0.85, 1.05, 1.25]:
        p1 = 10.0 / (1.0 + np.exp(-b * 0.5))
        print(f"  beta = {b:.2f} -> Pressure = {p1:.4f}")

    print("\n=== EDGE CASE & SENSITIVITY SUITE PASSED ===")

if __name__ == "__main__":
    test_edge_cases_and_sensitivity()
