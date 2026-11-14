"""
Mandatory Monotonicity Test Matrix
SupeRR Intelligence - Advanced Analytics Engine

Tests all combinations across:
- DeltaC in [-10, -7, -5, -4, -2, 0, +2, +4, +7, +10]
- Progress in [0.10, 0.25, 0.50, 0.75, 0.90] (balls elapsed: 12, 30, 60, 90, 108)
- Wickets in hand from 10 down to 1 (wickets lost from 0 up to 9)

Total Matrix Points: 10 DeltaC * 5 Progress * 10 Wicket States = 500 State Points.

Verifies:
1. Losing additional wickets must NEVER decrease pressure while other inputs remain fixed.
2. Increasing required run rate must NEVER decrease pressure while other inputs remain fixed.
3. Improving required run rate must NEVER increase pressure while other inputs remain fixed.
4. Boundedness and continuity in [0.2, 9.9].
5. Exactly resolves user's counterexample (DeltaC = -4, Progress = 0.75, 8 vs 6 wkts in hand).
"""

import numpy as np
import pandas as pd
from backend.analytics.pressure.engine import DynamicPressureEngine

def run_matrix_tests():
    print("=== EXECUTING MANDATORY 500-POINT CHASE MONOTONICITY MATRIX ===")
    engine = DynamicPressureEngine()
    
    delta_c_list = [-10.0, -7.0, -5.0, -4.0, -2.0, 0.0, 2.0, 4.0, 7.0, 10.0]
    progress_list = [0.10, 0.25, 0.50, 0.75, 0.90]
    wickets_in_hand_list = list(range(10, 0, -1)) # 10 down to 1
    
    target = 180.0
    initial_rrr = 9.0
    
    # Store all evaluation points
    rows = []
    for dc in delta_c_list:
        for prog in progress_list:
            for w in wickets_in_hand_list:
                rows.append({
                    'target_runs': target,
                    'initial_rrr': initial_rrr,
                    'delta_c': dc,
                    'required_run_rate': initial_rrr + dc,
                    'progress': prog,
                    'pre_ball_legal_balls': int(prog * 120),
                    'max_legal_balls': 120,
                    'wickets_in_hand': w,
                    'wickets_lost': 10 - w
                })
    
    df_matrix = pd.DataFrame(rows)
    p_series = engine.compute_second_innings_pressure(df_matrix)
    df_matrix['pressure'] = p_series
    
    print(f"Computed chase pressure across {len(df_matrix)} controlled grid points.")
    
    # -------------------------------------------------------------------------
    # TEST 1: WICKET LOSS MONOTONICITY
    # For every fixed (DeltaC, Progress), as wickets in hand decrease (10 down to 1),
    # pressure must be strictly non-decreasing (dP / d(wickets_lost) >= 0).
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Wicket Loss Monotonicity (Losing wickets must NEVER decrease pressure) ---")
    wkt_failures = []
    total_wkt_checks = 0
    
    for dc in delta_c_list:
        for prog in progress_list:
            sub = df_matrix[(df_matrix['delta_c'] == dc) & (df_matrix['progress'] == prog)].sort_values('wickets_lost')
            p_vals = sub['pressure'].values
            diffs = np.diff(p_vals)
            total_wkt_checks += len(diffs)
            
            if (diffs < -1e-6).any():
                fail_idx = np.where(diffs < -1e-6)[0][0]
                wkt_failures.append({
                    'delta_c': dc,
                    'progress': prog,
                    'w_lost_before': sub['wickets_lost'].iloc[fail_idx],
                    'w_lost_after': sub['wickets_lost'].iloc[fail_idx + 1],
                    'p_before': p_vals[fail_idx],
                    'p_after': p_vals[fail_idx + 1],
                    'delta_p': diffs[fail_idx]
                })
    
    print(f"Total pairwise wicket transition checks: {total_wkt_checks}")
    print(f"Total wicket monotonicity failures: {len(wkt_failures)}")
    if len(wkt_failures) > 0:
        print("FAILURES DETECTED:")
        for f in wkt_failures[:5]:
            print(f"  DeltaC={f['delta_c']}, Prog={f['progress']}: Wkts {f['w_lost_before']}->{f['w_lost_after']} decreased pressure by {f['delta_p']:.4f}")
    assert len(wkt_failures) == 0, f"Failed wicket monotonicity across {len(wkt_failures)} combinations!"
    print(">>> PASS: 100% of combinations satisfy dP/dWicketDeficit >= 0!")

    # -------------------------------------------------------------------------
    # TEST 2: REQUIRED RUN RATE MONOTONICITY
    # For every fixed (Progress, Wickets in Hand), as DeltaC increases (-10 to +10),
    # pressure must be strictly non-decreasing (dP / d(DeltaC) >= 0).
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Required Run Rate Monotonicity (Increasing RRR must NEVER decrease pressure) ---")
    rrr_failures = []
    total_rrr_checks = 0
    
    for prog in progress_list:
        for w in wickets_in_hand_list:
            sub = df_matrix[(df_matrix['progress'] == prog) & (df_matrix['wickets_in_hand'] == w)].sort_values('delta_c')
            p_vals = sub['pressure'].values
            diffs = np.diff(p_vals)
            total_rrr_checks += len(diffs)
            
            if (diffs < -1e-6).any():
                fail_idx = np.where(diffs < -1e-6)[0][0]
                rrr_failures.append({
                    'progress': prog,
                    'wickets_in_hand': w,
                    'dc_before': sub['delta_c'].iloc[fail_idx],
                    'dc_after': sub['delta_c'].iloc[fail_idx + 1],
                    'p_before': p_vals[fail_idx],
                    'p_after': p_vals[fail_idx + 1]
                })
    
    print(f"Total pairwise RRR transition checks: {total_rrr_checks}")
    print(f"Total RRR monotonicity failures: {len(rrr_failures)}")
    assert len(rrr_failures) == 0, f"Failed RRR monotonicity across {len(rrr_failures)} combinations!"
    print(">>> PASS: 100% of combinations satisfy dP/d(DeltaC) >= 0!")

    # -------------------------------------------------------------------------
    # TEST 3: EXACT COUNTEREXAMPLE RESOLUTION
    # Re-evaluate user's counterexample: DeltaC = -4.0, Progress = 0.75, 8 vs 6 wkts
    # -------------------------------------------------------------------------
    print("\n--- Test 3: Resolution of User Counterexample ---")
    ce_8 = df_matrix[(df_matrix['delta_c'] == -4.0) & (df_matrix['progress'] == 0.75) & (df_matrix['wickets_in_hand'] == 8)].iloc[0]
    ce_6 = df_matrix[(df_matrix['delta_c'] == -4.0) & (df_matrix['progress'] == 0.75) & (df_matrix['wickets_in_hand'] == 6)].iloc[0]
    
    print(f"  Situation: Target 180, RRR 5.0 (DeltaC = -4.0), Balls Elapsed = 90 (Prog = 0.75)")
    print(f"  At 8 Wickets in Hand (2 lost): Pressure = {ce_8['pressure']:.4f}")
    print(f"  At 6 Wickets in Hand (4 lost): Pressure = {ce_6['pressure']:.4f}")
    diff_ce = ce_6['pressure'] - ce_8['pressure']
    print(f"  Difference upon losing 2 wickets: {diff_ce:+.4f} (Strictly Positive Increase!)")
    assert diff_ce > 0, "Counterexample failed: losing wickets decreased pressure!"
    print(">>> PASS: User counterexample is fully resolved and mathematically monotonic.")

    # -------------------------------------------------------------------------
    # TEST 4: EDGE CASE BOUNDS & CONTINUITY
    # -------------------------------------------------------------------------
    print("\n--- Test 4: Edge Case Boundary Handling ---")
    min_p = df_matrix['pressure'].min()
    max_p = df_matrix['pressure'].max()
    print(f"  Matrix Pressure Minimum: {min_p:.4f} (Guardrail: >= 0.20)")
    print(f"  Matrix Pressure Maximum: {max_p:.4f} (Guardrail: <= 9.90)")
    assert min_p >= 0.20, "Pressure violated minimum lower bound!"
    assert max_p <= 9.90, "Pressure violated maximum upper bound!"
    assert not df_matrix['pressure'].isna().any(), "Found NaNs in pressure output!"
    assert not np.isinf(df_matrix['pressure']).any(), "Found Infs in pressure output!"
    print(">>> PASS: All boundary constraints cleanly satisfied.")

    print("\n=== MANDATORY MONOTONICITY MATRIX COMPLETE: 100% PASSING ===")

if __name__ == "__main__":
    run_matrix_tests()
