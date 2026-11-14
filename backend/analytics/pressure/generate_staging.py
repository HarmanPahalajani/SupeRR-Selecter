"""
Staging Pipeline Generator - SupeRR Intelligence
Generates isolated staging Parquet artifacts:
1. data/staging/fact_delivery_states_pressure_vNext.parquet
2. data/staging/fact_player_metrics_pressure_vNext.parquet
3. data/staging/staging_metadata_vNext.json

Uses Ridge Regression as primary expected-score model.
Preserves all original columns, IDs, and row alignments.
Zero modification to production tables or DuckDB.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from backend.analytics.pressure.engine import DynamicPressureEngine

def generate_staging_artifacts():
    print("=== EXECUTING RIDGE-PRIMARY STAGING PIPELINE ===")
    staging_dir = Path("data/staging")
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Initialize Ridge-Primary Dynamic Pressure Engine
    engine = DynamicPressureEngine(primary_model="ridge")
    
    # 2. Load Raw States
    states_path = "data/processed/fact_delivery_states.parquet"
    print(f"Loading raw states from {states_path}...")
    df_states = pd.read_parquet(states_path)
    matches = pd.read_parquet("data/processed/dim_match.parquet")
    
    if 'venue_id' not in df_states.columns or 'match_date' not in df_states.columns:
        match_meta = matches[['match_id', 'match_date', 'venue_id', 'season']].drop_duplicates()
        cols_to_add = [c for c in ['match_date', 'venue_id', 'season'] if c not in df_states.columns]
        if cols_to_add:
            df_states = df_states.merge(match_meta[['match_id'] + cols_to_add], on='match_id', how='left')
            
    print(f"Total states rows loaded: {len(df_states)}")
    
    # Create copy for vNext staging
    vnext_states = df_states.copy()
    
    # 3. Compute 1st Innings Dynamic Pressure (Ridge Primary)
    print("Computing 1st innings dynamic pressure using primary Ridge model...")
    inn1_mask = vnext_states['innings'] == 1
    inn1_sub = vnext_states[inn1_mask].copy()
    p1_series, exp_score_series = engine.compute_first_innings_pressure(inn1_sub)
    
    # 4. Compute 2nd Innings Dynamic Pressure (Decoupled Chase Engine)
    print("Computing 2nd innings dynamic pressure using decoupled chase engine...")
    inn2_mask = vnext_states['innings'] == 2
    inn2_sub = vnext_states[inn2_mask].copy()
    p2_series = engine.compute_second_innings_pressure(inn2_sub)
    
    # 5. Populate Staging Columns
    vnext_states['inn1_pressure_index'] = np.nan
    vnext_states.loc[inn1_mask, 'inn1_pressure_index'] = p1_series.values
    
    vnext_states['chase_pressure_index'] = np.nan
    vnext_states.loc[inn2_mask, 'chase_pressure_index'] = p2_series.values
    
    # Combined situational_pressure & pressure_index
    combined_pressure = np.full(len(vnext_states), 5.0, dtype=float)
    combined_pressure[inn1_mask] = p1_series.values
    combined_pressure[inn2_mask] = p2_series.values
    
    vnext_states['situational_pressure'] = combined_pressure
    vnext_states['pressure_index'] = combined_pressure
    
    # Defensive pressure index (for bowling perspective)
    vnext_states['defensive_pressure_index'] = combined_pressure
    
    # Pressure tiers
    tier_bins = [-0.1, 4.0, 6.5, 8.2, 10.1]
    tier_labels = ['low', 'moderate', 'high', 'extreme']
    vnext_states['pressure_tier'] = pd.cut(vnext_states['pressure_index'], bins=tier_bins, labels=tier_labels)
    
    # 6. Save Staging Delivery States
    out_states_path = staging_dir / "fact_delivery_states_pressure_vNext.parquet"
    print(f"Saving versioned staging states to {out_states_path}...")
    vnext_states.to_parquet(out_states_path, index=False)
    
    # -------------------------------------------------------------
    # 7. Recalculate Staging Player Metrics (Strict Primary Scope Enforcement)
    # -------------------------------------------------------------
    print("Recalculating staging player metrics strictly separating primary scope and emerging scope...")
    # Load base player metrics
    prod_metrics = pd.read_parquet("data/processed/fact_player_metrics.parquet")
    staging_metrics = prod_metrics.copy()
    
    # 7a. Primary Scope Deliveries (IPL + T20I: 193,988 deliveries)
    prim_mask = vnext_states['is_primary_scope'] == True
    prim_states = vnext_states[prim_mask].copy()
    prim_high_mask = prim_states['pressure_index'] >= 6.5
    
    # Primary Batting pressure calculations
    bat_press_prim = prim_states[prim_high_mask].groupby('striker_id').agg(
        staging_pressure_balls=('innings_ball_num', 'count'),
        staging_pressure_runs=('runs', 'sum'),
        staging_pressure_dots=('runs', lambda s: (s == 0).sum())
    ).reset_index().rename(columns={'striker_id': 'player_id'})
    
    # Primary Bowling pressure calculations
    bowl_press_prim = prim_states[prim_high_mask].groupby('bowler_id').agg(
        staging_pressure_balls_bowled=('innings_ball_num', 'count'),
        staging_pressure_runs_conceded=('runs', 'sum'),
        staging_pressure_wickets=('is_wicket', lambda s: s.fillna(False).astype(bool).sum())
    ).reset_index().rename(columns={'bowler_id': 'player_id'})
    
    # 7b. Emerging Scope Deliveries (OTHER_T20: 6,973 deliveries)
    emg_mask = vnext_states['is_primary_scope'] == False
    emg_states = vnext_states[emg_mask].copy()
    emg_high_mask = emg_states['pressure_index'] >= 6.5
    
    bat_press_emg = emg_states[emg_high_mask].groupby('striker_id').agg(
        emerging_pressure_balls=('innings_ball_num', 'count'),
        emerging_pressure_runs=('runs', 'sum')
    ).reset_index().rename(columns={'striker_id': 'player_id'})
    
    bowl_press_emg = emg_states[emg_high_mask].groupby('bowler_id').agg(
        emerging_pressure_balls_bowled=('innings_ball_num', 'count'),
        emerging_pressure_runs_conceded=('runs', 'sum'),
        emerging_pressure_wickets=('is_wicket', lambda s: s.fillna(False).astype(bool).sum())
    ).reset_index().rename(columns={'bowler_id': 'player_id'})
    
    # 7c. Merge Primary into staging_metrics
    staging_metrics = staging_metrics.merge(bat_press_prim, on='player_id', how='left')
    staging_metrics = staging_metrics.merge(bowl_press_prim, on='player_id', how='left')
    
    staging_metrics['staging_pressure_balls'] = staging_metrics['staging_pressure_balls'].fillna(0).astype(int)
    staging_metrics['staging_pressure_runs'] = staging_metrics['staging_pressure_runs'].fillna(0).astype(int)
    staging_metrics['staging_pressure_dots'] = staging_metrics['staging_pressure_dots'].fillna(0).astype(int)
    staging_metrics['staging_pressure_dot_pct'] = np.where(
        staging_metrics['staging_pressure_balls'] > 0,
        staging_metrics['staging_pressure_dots'] / staging_metrics['staging_pressure_balls'] * 100.0,
        0.0
    )
    staging_metrics['staging_pressure_sr'] = np.where(
        staging_metrics['staging_pressure_balls'] > 0,
        (staging_metrics['staging_pressure_runs'] / staging_metrics['staging_pressure_balls']) * 100.0,
        0.0
    )
    
    staging_metrics['staging_pressure_balls_bowled'] = staging_metrics['staging_pressure_balls_bowled'].fillna(0).astype(int)
    staging_metrics['staging_pressure_runs_conceded'] = staging_metrics['staging_pressure_runs_conceded'].fillna(0).astype(int)
    staging_metrics['staging_pressure_wickets'] = staging_metrics['staging_pressure_wickets'].fillna(0).astype(int)
    staging_metrics['staging_pressure_economy'] = np.where(
        staging_metrics['staging_pressure_balls_bowled'] > 0,
        staging_metrics['staging_pressure_runs_conceded'] / (staging_metrics['staging_pressure_balls_bowled'] / 6.0),
        0.0
    )
    
    # 7d. Merge Emerging into staging_metrics as supplementary discovery candidate fields
    staging_metrics = staging_metrics.merge(bat_press_emg, on='player_id', how='left')
    staging_metrics = staging_metrics.merge(bowl_press_emg, on='player_id', how='left')
    
    staging_metrics['emerging_pressure_balls'] = staging_metrics['emerging_pressure_balls'].fillna(0).astype(int)
    staging_metrics['emerging_pressure_runs'] = staging_metrics['emerging_pressure_runs'].fillna(0).astype(int)
    staging_metrics['emerging_pressure_sr'] = np.where(
        staging_metrics['emerging_pressure_balls'] > 0,
        (staging_metrics['emerging_pressure_runs'] / staging_metrics['emerging_pressure_balls']) * 100.0,
        0.0
    )
    
    staging_metrics['emerging_pressure_balls_bowled'] = staging_metrics['emerging_pressure_balls_bowled'].fillna(0).astype(int)
    staging_metrics['emerging_pressure_runs_conceded'] = staging_metrics['emerging_pressure_runs_conceded'].fillna(0).astype(int)
    staging_metrics['emerging_pressure_wickets'] = staging_metrics['emerging_pressure_wickets'].fillna(0).astype(int)
    staging_metrics['emerging_pressure_economy'] = np.where(
        staging_metrics['emerging_pressure_balls_bowled'] > 0,
        staging_metrics['emerging_pressure_runs_conceded'] / (staging_metrics['emerging_pressure_balls_bowled'] / 6.0),
        0.0
    )
    staging_metrics['is_emerging_candidate'] = (staging_metrics['emerging_pressure_balls'] > 0) | (staging_metrics['emerging_pressure_balls_bowled'] > 0)
    staging_metrics['competition_scope'] = "IPL_T20I"

    # Save Staging Player Metrics
    out_metrics_path = staging_dir / "fact_player_metrics_pressure_vNext.parquet"
    print(f"Saving versioned staging metrics to {out_metrics_path}...")
    staging_metrics.to_parquet(out_metrics_path, index=False)
    
    # 8. Record Staging Metadata
    meta = {
        "pipeline_version": "vNext_staging",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_expected_score_model": "Ridge (alpha=100.0)",
        "primary_expected_score_artifact": "backend/analytics/pressure/expected_score_ridge.joblib",
        "challenger_model": "CatBoost (expected_score_catboost.cbm)",
        "second_innings_engine": "Decoupled Monotonic Chase Stress (lambda_w=1.50, gamma=0.45, c_max=13.5)",
        "dataset_rows": len(vnext_states),
        "total_players": len(staging_metrics),
        "scope_breakdown": {
            "primary_scope": {
                "description": "Official Senior Scope (IPL + T20I)",
                "first_innings_deliveries": int((prim_states['innings'] == 1).sum()),
                "second_innings_deliveries": int((prim_states['innings'] == 2).sum()),
                "total_deliveries": int(len(prim_states)),
                "primary_scope_matches": 837,
                "regulation_matches": 805,
                "provisional_shortened_matches": 25
            },
            "emerging_scope": {
                "description": "Supplementary Discovery Scope (OTHER_T20)",
                "first_innings_deliveries": int((emg_states['innings'] == 1).sum()),
                "second_innings_deliveries": int((emg_states['innings'] == 2).sum()),
                "total_deliveries": int(len(emg_states))
            },
            "combined_total_deliveries": len(vnext_states)
        },
        "staging_artifacts": [
            str(out_states_path),
            str(out_metrics_path)
        ]
    }
    with open(staging_dir / "staging_metadata_vNext.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("STAGING ARTIFACTS GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    generate_staging_artifacts()
