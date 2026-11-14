"""
Comprehensive Multi-Cut Historical Outcome Validation
SupeRR Intelligence - Advanced Analytics Engine

Evaluates outcomes strictly AFTER the pre-delivery state:
- Segmented by Competition (IPL vs T20I)
- Segmented by Innings Stage (Powerplay 1-6, Middle 7-15, Death 16-20)
- Segmented by Wickets in Hand bands
- Segmented by Required Run Rate bands
"""

import pandas as pd
import numpy as np
from backend.analytics.pressure.engine import DynamicPressureEngine

def run_segmented_validation():
    print("=== EXECUTING MULTI-CUT HISTORICAL OUTCOME VALIDATION ===")
    engine = DynamicPressureEngine()
    df = engine.load_data()
    engine.train_expected_score_model(df)
    
    inn1 = df[df['innings'] == 1].copy()
    inn2 = df[df['innings'] == 2].copy()
    
    p1, _ = engine.compute_first_innings_pressure(inn1)
    p2 = engine.compute_second_innings_pressure(inn2)
    
    inn1['pressure'] = p1
    inn2['pressure'] = p2
    
    bins = [-0.1, 4.0, 6.5, 8.2, 10.1]
    labels = ['Low (<4.0)', 'Moderate (4.0-6.5)', 'High (6.5-8.2)', 'Extreme (>=8.2)']
    inn1['tier'] = pd.cut(inn1['pressure'], bins=bins, labels=labels)
    inn2['tier'] = pd.cut(inn2['pressure'], bins=bins, labels=labels)
    
    # -------------------------------------------------------------
    # 1. BY COMPETITION (IPL VS T20I)
    # -------------------------------------------------------------
    print("\n--- 1. First Innings Outcomes by Competition (IPL vs T20I) ---")
    for comp in ['IPL', 'T20I']:
        sub = inn1[inn1['format_scope'] == comp]
        print(f"\n{comp} - First Innings ({len(sub)} deliveries):")
        grp = sub.groupby('tier', observed=False).agg(
            delivs=('batter_runs', 'count'),
            rpo=('batter_runs', lambda s: s.mean() * 6.0),
            wkt_pct=('is_wicket', lambda s: s.mean() * 100.0),
            dot_pct=('batter_runs', lambda s: (s == 0).mean() * 100.0)
        )
        print(grp)

    print("\n--- 2. Second Innings Outcomes by Competition (IPL vs T20I) ---")
    for comp in ['IPL', 'T20I']:
        sub = inn2[inn2['format_scope'] == comp]
        print(f"\n{comp} - Second Innings ({len(sub)} deliveries):")
        grp = sub.groupby('tier', observed=False).agg(
            delivs=('batter_runs', 'count'),
            rpo=('batter_runs', lambda s: s.mean() * 6.0),
            wkt_pct=('is_wicket', lambda s: s.mean() * 100.0),
            dot_pct=('batter_runs', lambda s: (s == 0).mean() * 100.0)
        )
        print(grp)

    # -------------------------------------------------------------
    # 3. SECOND INNINGS CONTROLLED BY MATCH PHASE
    # -------------------------------------------------------------
    print("\n--- 3. Second Innings Controlled by Innings Phase ---")
    inn2['phase_calc'] = np.where(inn2['pre_ball_legal_balls'] < 36, 'Powerplay', np.where(inn2['pre_ball_legal_balls'] < 90, 'Middle', 'Death'))
    for ph in ['Powerplay', 'Middle', 'Death']:
        sub = inn2[inn2['phase_calc'] == ph]
        print(f"\nPhase: {ph} ({len(sub)} deliveries):")
        grp = sub.groupby('tier', observed=False).agg(
            delivs=('batter_runs', 'count'),
            rpo=('batter_runs', lambda s: s.mean() * 6.0),
            wkt_pct=('is_wicket', lambda s: s.mean() * 100.0),
            dot_pct=('batter_runs', lambda s: (s == 0).mean() * 100.0)
        )
        print(grp)

    # -------------------------------------------------------------
    # 4. SECOND INNINGS CONTROLLED BY WICKETS IN HAND BANDS
    # -------------------------------------------------------------
    print("\n--- 4. Second Innings Controlled by Wickets in Hand Bands ---")
    inn2['wkt_band'] = pd.cut(inn2['wickets_in_hand'], bins=[0, 3, 6, 10], labels=['Tail (1-3 in hand)', 'Middle (4-6 in hand)', 'Top (7-10 in hand)'])
    for w_band in ['Top (7-10 in hand)', 'Middle (4-6 in hand)', 'Tail (1-3 in hand)']:
        sub = inn2[inn2['wkt_band'] == w_band]
        print(f"\nWickets Band: {w_band} ({len(sub)} deliveries):")
        grp = sub.groupby('tier', observed=False).agg(
            delivs=('batter_runs', 'count'),
            rpo=('batter_runs', lambda s: s.mean() * 6.0),
            wkt_pct=('is_wicket', lambda s: s.mean() * 100.0),
            dot_pct=('batter_runs', lambda s: (s == 0).mean() * 100.0)
        )
        print(grp)

    print("\n=== MULTI-CUT VALIDATION COMPLETE ===")

if __name__ == "__main__":
    run_segmented_validation()
