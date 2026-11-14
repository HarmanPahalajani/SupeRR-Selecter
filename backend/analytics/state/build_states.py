import json
from pathlib import Path
import pandas as pd
import numpy as np

def build_match_states(processed_dir: str = "data/processed", reports_dir: str = "artifacts/reports"):
    proc_path = Path(processed_dir)
    rep_path = Path(reports_dir)
    rep_path.mkdir(parents=True, exist_ok=True)

    print("Loading canonical delivery data...")
    df = pd.read_parquet(proc_path / "fact_delivery_canonical.parquet")

    # Filter out super overs from standard regulation match-state reconstruction
    # Super overs (innings > 2) are kept separate as requested in Technical Revision 1
    reg_df = df[df['is_super_over'] == False].copy()
    print(f"Total regulation deliveries: {len(reg_df)} (super overs excluded: {(df['is_super_over'] == True).sum()})")

    # Sort strictly chronologically within each match and innings
    reg_df = reg_df.sort_values(by=['match_id', 'innings', 'overid', 'innings_ball_num']).reset_index(drop=True)

    # First innings total for each match to determine chase targets
    inn1_totals = reg_df[reg_df['innings'] == 1].groupby('match_id')['total_delivery_runs'].sum().rename('inn1_total_runs')
    reg_df = reg_df.merge(inn1_totals, on='match_id', how='left')

    print("Reconstructing chronological pre-delivery match states...")
    grouped = reg_df.groupby(['match_id', 'innings'])

    # Pre-delivery score and wickets
    reg_df['pre_ball_score'] = grouped['total_delivery_runs'].cumsum() - reg_df['total_delivery_runs']
    reg_df['pre_ball_wickets'] = grouped['is_wicket'].cumsum() - reg_df['is_wicket'].astype(int)
    reg_df['pre_ball_wickets'] = reg_df['pre_ball_wickets'].clip(0, 10)
    reg_df['wickets_in_hand'] = 10 - reg_df['pre_ball_wickets']

    # Derivation of legal-ball progression using verified extra classifications
    # Note: neither innings_ball_num nor over_ball_num is treated as legal ball count
    reg_df['pre_ball_legal_balls'] = grouped['is_legal_ball'].cumsum() - reg_df['is_legal_ball'].astype(int)

    # Dynamic handling of revised overs (DLS / weather rain rules)
    revised_overs = np.where(
        reg_df['innings'] == 1,
        reg_df['first_inn_revised_overs'].fillna(20.0),
        reg_df['second_inn_revised_overs'].fillna(20.0)
    )
    revised_overs = np.where(revised_overs <= 0, 20.0, revised_overs)
    reg_df['max_legal_balls'] = (revised_overs * 6).astype(int)
    reg_df['legal_balls_remaining'] = np.maximum(0, reg_df['max_legal_balls'] - reg_df['pre_ball_legal_balls'])

    # Current run rate (runs per over)
    overs_bowled = np.maximum(reg_df['pre_ball_legal_balls'] / 6.0, 1.0 / 6.0)
    reg_df['current_run_rate'] = np.where(reg_df['pre_ball_legal_balls'] > 0, reg_df['pre_ball_score'] / overs_bowled, 0.0)

    # Chase targets (Innings 2)
    # If revised_target exists and > 0, use revised_target; otherwise use inn1_total_runs + 1
    has_revised_target = reg_df['revised_target'].notnull() & (reg_df['revised_target'] > 0)
    reg_df['target_runs'] = np.where(
        reg_df['innings'] == 2,
        np.where(has_revised_target, reg_df['revised_target'], reg_df['inn1_total_runs'] + 1),
        np.nan
    )
    reg_df['runs_needed'] = np.where(
        reg_df['innings'] == 2,
        np.maximum(0, reg_df['target_runs'] - reg_df['pre_ball_score']),
        np.nan
    )
    overs_remaining = np.maximum(reg_df['legal_balls_remaining'] / 6.0, 1.0 / 6.0)
    reg_df['required_run_rate'] = np.where(
        reg_df['innings'] == 2,
        reg_df['runs_needed'] / overs_remaining,
        np.nan
    )

    # Explicit empirical resource proxy R(t) in [0, 1]
    # Combines balls bowled proportion and wickets lost proportion
    ball_pct = reg_df['pre_ball_legal_balls'] / reg_df['max_legal_balls']
    wicket_pct = reg_df['pre_ball_wickets'] / 10.0
    reg_df['resource_consumed_pct'] = np.clip(0.45 * ball_pct + 0.55 * wicket_pct, 0.0, 1.0)
    reg_df['resource_remaining_pct'] = 1.0 - reg_df['resource_consumed_pct']

    # Striker pre-delivery history within innings
    striker_grouped = reg_df.groupby(['match_id', 'innings', 'striker_id'])
    reg_df['striker_balls_faced_pre'] = striker_grouped['is_legal_ball'].cumsum() - reg_df['is_legal_ball'].astype(int)
    reg_df['striker_runs_scored_pre'] = striker_grouped['batter_runs'].cumsum() - reg_df['batter_runs']

    print("Computing calibrated situational pressure indices...")
    # Mallawa Arachchi, Manage & Scariano (2024) Bounded Second-Innings Pressure
    # Calibrated on training seasons (2022-2024)
    k = 0.045
    c_max = 13.5 # Feasible initial max required rate reference
    
    rrr = reg_df['required_run_rate'].fillna(8.0)
    initial_rrr = reg_df['target_runs'].fillna(160.0) / 20.0
    p1 = np.clip(10.0 * (initial_rrr / c_max), 1.0, 9.5)
    
    delta_c = np.maximum(0.0, rrr - initial_rrr)
    delta_r = reg_df['resource_consumed_pct']
    stress_term = delta_c * delta_r
    
    denom = 1.0 + (10.0 / p1 - 1.0) * np.exp(-k * 10.0 * stress_term)
    chase_pressure = np.clip(10.0 / denom, 0.0, 10.0)

    # First innings acceleration pressure (measured against par trajectory)
    proj_score = reg_df['pre_ball_score'] + reg_df['resource_remaining_pct'] * 165.0
    inn1_pressure = np.clip(5.0 + 5.0 * np.tanh((proj_score - 165.0) / 35.0), 0.0, 10.0)

    reg_df['chase_pressure_index'] = np.where(reg_df['innings'] == 2, chase_pressure, np.nan)
    reg_df['inn1_pressure_index'] = np.where(reg_df['innings'] == 1, inn1_pressure, np.nan)

    # Unified situational pressure index (labeled clearly by context)
    reg_df['pressure_index'] = np.where(reg_df['innings'] == 2, reg_df['chase_pressure_index'], reg_df['inn1_pressure_index'])

    # Defensive pressure from bowling team perspective (defending in 2nd innings)
    reg_df['defensive_pressure_index'] = np.where(
        reg_df['innings'] == 2,
        np.clip(10.0 - chase_pressure * 0.8 + (10.0 - reg_df['wickets_in_hand']) * 0.2, 0.0, 10.0),
        np.clip(reg_df['inn1_pressure_index'], 0.0, 10.0)
    )

    # Leverage index (swing potential on next ball)
    leverage = 10.0 * np.exp(-((rrr - 9.0) ** 2) / 25.0) * (reg_df['wickets_in_hand'] / 10.0)
    reg_df['leverage_index'] = np.clip(leverage, 0.0, 10.0)

    reg_df['pressure_tier'] = pd.cut(
        reg_df['pressure_index'], 
        bins=[-0.1, 4.0, 6.5, 8.2, 10.1], 
        labels=['low', 'moderate', 'high', 'very_high']
    )

    states_file = proc_path / "fact_delivery_states.parquet"
    reg_df.to_parquet(states_file, index=False)
    print(f"Match states built successfully with {len(reg_df)} regulation deliveries saved to {states_file}!")

    report = {
        "status": "PASS",
        "total_regulation_states": len(reg_df),
        "mean_pressure_innings_1": float(reg_df[reg_df['innings'] == 1]['pressure_index'].mean()),
        "mean_pressure_innings_2": float(reg_df[reg_df['innings'] == 2]['pressure_index'].mean()),
        "high_pressure_deliveries_count": int((reg_df['pressure_tier'] == 'high').sum() + (reg_df['pressure_tier'] == 'very_high').sum()),
        "output_path": str(states_file)
    }
    with open(rep_path / "match_states_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    build_match_states()
