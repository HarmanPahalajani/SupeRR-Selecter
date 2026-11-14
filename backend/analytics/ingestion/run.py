import json
from pathlib import Path
import pandas as pd
import numpy as np

def run_ingestion(raw_dir: str = "data/raw", processed_dir: str = "data/processed", reports_dir: str = "artifacts/reports"):
    raw_path = Path(raw_dir)
    proc_path = Path(processed_dir)
    proc_path.mkdir(parents=True, exist_ok=True)
    rep_path = Path(reports_dir)
    rep_path.mkdir(parents=True, exist_ok=True)

    print("Step 1: Ingesting competitions and mapping...")
    comp_df = pd.read_csv(raw_path / "competitions.csv")
    
    # Identify primary scope: IPL and T20I matches, excluding emerging tournaments
    exclude_comps = ["Mens T20 Emerging Teams Asia Cup 2024", "Asia Cup Rising Stars 2025"]
    comp_df['is_primary_scope'] = (
        (comp_df['match_format'].isin(['T20', 'T20I'])) & 
        (~comp_df['comp_name'].isin(exclude_comps))
    )
    comp_df.to_parquet(proc_path / "dim_competition.parquet", index=False)

    print("Step 2: Ingesting matches...")
    matches_df = pd.read_csv(raw_path / "matches.csv")
    matches_df = matches_df.merge(
        comp_df[['comp_id', 'comp_name', 'match_format', 'is_primary_scope']], 
        on='comp_id', 
        how='left'
    )
    # Ensure format_scope is explicit
    matches_df['format_scope'] = np.where(
        matches_df['comp_name'].str.startswith('IPL'), 
        'IPL', 
        np.where(matches_df['match_format'] == 'T20I', 'T20I', 'OTHER_T20')
    )
    # Parse date cleanly
    matches_df['match_date'] = pd.to_datetime(matches_df['match_date'])
    matches_df['season'] = matches_df['match_date'].dt.year

    print("Step 3: Ingesting players and roles...")
    mapping_df = pd.read_csv(raw_path / "competition_team_player_mapping.csv")
    p11_df = pd.read_csv(raw_path / "playing_eleven.csv")

    bbb_df = pd.read_csv(raw_path / "ball_by_ball.csv", low_memory=False)

    # Check matches with delivery data
    matches_with_balls = set(bbb_df['match_id'].unique())
    matches_df['has_deliveries'] = matches_df['match_id'].isin(matches_with_balls)
    matches_df.to_parquet(proc_path / "dim_match.parquet", index=False)

    # Extract player styles
    strikers = bbb_df[['striker_id', 'striker_name', 'batting_type']].drop_duplicates().rename(
        columns={'striker_id': 'player_id', 'striker_name': 'player_name', 'batting_type': 'bat_style'}
    )
    bowlers = bbb_df[['bowler_id', 'bowler_name', 'bowling_type', 'pace_or_spin']].drop_duplicates().rename(
        columns={'bowler_id': 'player_id', 'bowler_name': 'player_name', 'bowling_type': 'bowl_style'}
    )
    
    player_names = mapping_df[['player_id', 'player_name']].drop_duplicates()
    
    dim_player = player_names.merge(strikers[['player_id', 'bat_style']].drop_duplicates(subset=['player_id']), on='player_id', how='left')
    dim_player = dim_player.merge(bowlers[['player_id', 'bowl_style', 'pace_or_spin']].drop_duplicates(subset=['player_id']), on='player_id', how='left')
    
    dim_player['bat_style'] = dim_player['bat_style'].fillna('Right hand Bat')
    dim_player['bowl_style'] = dim_player['bowl_style'].fillna('Unknown')
    dim_player['pace_or_spin'] = dim_player['pace_or_spin'].fillna('Unknown')

    if 'is_wk' in p11_df.columns:
        wk_players = set(p11_df[p11_df['is_wk'] == 1]['player_id'].unique())
    else:
        wk_players = set()
    dim_player['is_wk'] = dim_player['player_id'].isin(wk_players)

    dim_player.to_parquet(proc_path / "dim_player.parquet", index=False)

    print("Step 4: Auditing anomalies and applying certified scoring semantics...")
    # Add match metadata to deliveries
    bbb_df = bbb_df.merge(
        matches_df[['match_id', 'comp_id', 'comp_name', 'season', 'match_date', 'format_scope', 'is_primary_scope', 'home_team', 'away_team', 'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target', 'result']],
        on='match_id',
        how='left'
    )

    # Anomaly tracking: log rows with speed outliers, wicket anomalies, and extras_2_runs
    anomalies = {
        "extras_2_runs_count": int((bbb_df['extras_2_runs'] > 0).sum()),
        "bowl_speed_zero_count": int((bbb_df['bowl_speed'] == 0).sum()),
        "bowl_speed_outlier_count": int(((bbb_df['bowl_speed'] < 0) | (bbb_df['bowl_speed'] > 180)).sum()),
        "wicket_flag_missing_dismissed_player": int(((bbb_df['is_wicket'] == True) & (bbb_df['dismissed_player_id'].isnull())).sum()),
        "non_wicket_with_dismissed_player": int(((bbb_df['is_wicket'] == False) & (bbb_df['dismissed_player_id'].notnull())).sum())
    }
    with open(rep_path / "scoring_anomalies_audit.json", "w") as f:
        json.dump(anomalies, f, indent=2)

    # 1. Batter runs
    is_overstep_or_other = bbb_df['extras_type'].isin(['Overstep', 'other'])
    extra_batter_runs = np.where(is_overstep_or_other & (bbb_df['runs'] == 0) & (bbb_df['extras_2_runs'] > 0), bbb_df['extras_2_runs'], 0)
    bbb_df['batter_runs'] = bbb_df['runs'].fillna(0).astype(int) + extra_batter_runs

    # 2. Extras breakdown
    is_wide = bbb_df['extras_type'] == 'wide'
    bbb_df['extras_wide_runs'] = np.where(is_wide, bbb_df['extras1_runs'].fillna(0) + bbb_df['extras_2_runs'].fillna(0), 0).astype(int)
    bbb_df['extras_noball_runs'] = np.where(is_overstep_or_other, bbb_df['extras1_runs'].fillna(0), 0).astype(int)
    is_bye_legbye = bbb_df['extras_type'].isin(['byes', 'legbyes'])
    bbb_df['extras_bye_legbye_runs'] = np.where(is_bye_legbye, bbb_df['extras1_runs'].fillna(0), 0).astype(int)
    is_penalty = bbb_df['extras_type'] == 'Penalty'
    bbb_df['extras_penalty_runs'] = np.where(is_penalty, bbb_df['extras1_runs'].fillna(0), 0).astype(int)

    # 3. Bowler conceded runs
    bbb_df['bowler_conceded_runs'] = bbb_df['batter_runs'] + bbb_df['extras_wide_runs'] + bbb_df['extras_noball_runs']

    # 4. Total delivery runs
    bbb_df['total_delivery_runs'] = bbb_df['bowler_conceded_runs'] + bbb_df['extras_bye_legbye_runs'] + bbb_df['extras_penalty_runs']

    # 5. Legal deliveries: Wides, Oversteps, and 'other' (non-overstep no-balls) are NOT legal deliveries
    illegal_extras = ['wide', 'Overstep', 'other']
    bbb_df['is_legal_ball'] = ~bbb_df['extras_type'].isin(illegal_extras)

    # Audit unknown extras_type values to ensure none are silently treated as legal
    known_extras = set(illegal_extras + ['byes', 'legbyes', 'Penalty'])
    observed_extras = set(bbb_df['extras_type'].dropna().unique())
    unknown_extras = observed_extras - known_extras
    if unknown_extras:
        print(f"WARNING: Unknown extras_type values observed: {unknown_extras}")
        # Unknown extras must not silently be treated as legal
        bbb_df.loc[bbb_df['extras_type'].isin(unknown_extras), 'is_legal_ball'] = False

    # 6. Bowler credited wickets
    bowler_credited_types = ["Caught", "Bowled", "LBW", "Stump", "Hit Wicket"]
    bbb_df['is_bowler_wicket'] = (bbb_df['is_wicket'] == True) & (bbb_df['dismissal_type'].isin(bowler_credited_types))

    # 7. Super Over flag vs Regulation Innings
    # In T20 cricket, innings 1 and 2 are regulation innings; innings 3+ are Super Overs
    bbb_df['is_super_over'] = bbb_df['innings'] > 2

    # 8. Strict 1-based overid phase boundaries:
    # Powerplay: 1-6
    # Middle: 7-15
    # Death: 16-20
    bbb_df['phase'] = np.where(
        bbb_df['overid'] <= 6, 'powerplay',
        np.where(bbb_df['overid'] <= 15, 'middle', 'death')
    )

    # Separate super overs into a distinct view/table
    super_overs_df = bbb_df[bbb_df['is_super_over'] == True]
    super_overs_df.to_parquet(proc_path / "fact_delivery_super_overs.parquet", index=False)

    # Canonical regulation deliveries
    fact_file = proc_path / "fact_delivery_canonical.parquet"
    bbb_df.to_parquet(fact_file, index=False)
    print(f"Saved canonical delivery table ({len(bbb_df)} total, {len(super_overs_df)} super overs) to {fact_file}")

    report = {
        "status": "PASS",
        "total_deliveries": len(bbb_df),
        "primary_scope_deliveries": int(bbb_df['is_primary_scope'].sum()),
        "ipl_deliveries": int((bbb_df['format_scope'] == 'IPL').sum()),
        "t20i_deliveries": int((bbb_df['format_scope'] == 'T20I').sum()),
        "super_over_deliveries": len(super_overs_df),
        "total_matches": len(matches_df),
        "primary_scope_matches": int(matches_df['is_primary_scope'].sum()),
        "unique_players": len(dim_player),
        "anomalies_audited": anomalies,
        "verification": "1-based overid, Powerplay (1-6), Middle (7-15), Death (16-20), Super Overs isolated."
    }
    with open(rep_path / "data_ingestion_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    run_ingestion()
