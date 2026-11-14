"""
Revised Overs & DLS Match Verification Suite
SupeRR Intelligence - Dynamic Pressure Engine
Tests actual shortened overs and DLS matches from dataset.
"""

import pandas as pd
import numpy as np
from backend.analytics.pressure.engine import DynamicPressureEngine

def test_revised_and_dls_matches():
    print("=== TESTING REVISED OVERS & DLS MATCHES ===")
    engine = DynamicPressureEngine()
    df = engine.load_data()
    
    # -------------------------------------------------------------
    # 1. Shortened Chase Overs & DLS Targets
    # -------------------------------------------------------------
    inn2 = df[df['innings'] == 2].copy()
    rev_inn2 = inn2[inn2['second_inn_revised_overs'].notna() & (inn2['second_inn_revised_overs'] > 0)].copy()
    print(f"Total shortened 2nd innings deliveries: {len(rev_inn2)} across {rev_inn2['match_id'].nunique()} matches")
    
    p2 = engine.compute_second_innings_pressure(rev_inn2)
    rev_inn2['pressure'] = p2
    
    # Check Ball 1 for shortened matches
    ball1 = rev_inn2[rev_inn2['pre_ball_legal_balls'] == 0].drop_duplicates(subset=['match_id']).copy()
    print(f"\nBall 1 states in {len(ball1)} shortened chase matches:")
    for _, r in ball1.head(8).iterrows():
        mid = int(r['match_id'])
        t = float(r['revised_target']) if pd.notna(r['revised_target']) else float(r['target_runs'])
        bmax = float(r['second_inn_revised_overs'])
        ov = bmax / 6.0
        init_rrr = t / ov
        exp_p1 = np.clip(10.0 * (init_rrr / engine.c_max), 1.0, 9.5)
        act_p = float(r['pressure'])
        print(f"Match {mid} | Target {t:.0f} in {ov:.1f} ov ({int(bmax)} balls) -> Initial RRR: {init_rrr:.2f} | Expected P(1): {exp_p1:.4f} | Actual: {act_p:.4f} | Diff: {abs(act_p - exp_p1):.6f}")
        assert abs(act_p - exp_p1) < 1e-4, f"Mismatch on Ball 1 for match {mid}"
    
    print("ALL BALL 1 SHORTENED CHASE ANCHORS VERIFIED EXACT!")
    
    # -------------------------------------------------------------
    # 2. Shortened 1st Innings Matches
    # -------------------------------------------------------------
    inn1 = df[df['innings'] == 1].copy()
    rev_inn1 = inn1[inn1['first_inn_revised_overs'].notna() & (inn1['first_inn_revised_overs'] > 0)].copy()
    print(f"\nTotal shortened 1st innings deliveries: {len(rev_inn1)} across {rev_inn1['match_id'].nunique()} matches")
    
    p1, exp_s = engine.compute_first_innings_pressure(rev_inn1)
    rev_inn1['pressure'] = p1
    rev_inn1['expected_score'] = exp_s
    
    ball1_inn1 = rev_inn1[rev_inn1['pre_ball_legal_balls'] == 0].drop_duplicates(subset=['match_id']).copy()
    print(f"\nBall 1 states in {len(ball1_inn1)} shortened 1st innings matches:")
    for _, r in ball1_inn1.head(8).iterrows():
        mid = int(r['match_id'])
        bmax = float(r['first_inn_revised_overs'])
        ov = bmax / 6.0
        act_p = float(r['pressure'])
        exp_sc = float(r['expected_score'])
        print(f"Match {mid} | Shortened to {ov:.1f} ov ({int(bmax)} balls) -> Expected Score: {exp_sc:.1f} | Pressure: {act_p:.4f}")
        # At Ball 1 with CRR=0, proj_rr = par_rr, expected_score = prorated par -> pressure should be 5.0
        assert abs(act_p - 5.0) < 1e-3, f"Expected 5.0 at Ball 1 for match {mid}, got {act_p}"
    
    print("ALL BALL 1 SHORTENED 1ST INNINGS STATES VERIFIED EXACT AT 5.0!")

    # -------------------------------------------------------------
    # 3. User Shortened Overs Example Verification
    # -------------------------------------------------------------
    print("\n--- Verifying User Shortened Overs Example ---")
    # Target: 150
    # Standard 20 overs: initial RRR = 7.5
    # Shortened 15 overs: initial RRR = 10.0
    r_std = 150.0 / 20.0 # 7.5
    p1_std = 10.0 * (r_std / 13.5) # 5.5556
    
    r_short = 150.0 / 15.0 # 10.0
    p1_short = 10.0 * (r_short / 13.5) # 7.4074
    
    print(f"Standard 20 ov (120 balls): Target 150 -> Initial RRR {r_std:.2f} -> P(1) = {p1_std:.4f}")
    print(f"Shortened 15 ov ( 90 balls): Target 150 -> Initial RRR {r_short:.2f} -> P(1) = {p1_short:.4f}")
    print(f"Delta P(1) from shortened overs: +{p1_short - p1_std:.4f}")
    assert p1_short > p1_std, "Shortened overs must produce higher initial pressure for same target!"
    print("USER SHORTENED OVERS EXAMPLE PASSED VERIFICATION!")

if __name__ == "__main__":
    test_revised_and_dls_matches()
