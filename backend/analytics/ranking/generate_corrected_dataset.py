import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from backend.analytics.ranking.build_ratings import compute_evidence_based_ratings

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def generate_and_diagnose():
    staging_dir = Path("data/staging_ratings")
    staging_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = Path("artifacts/reports")
    rep_dir.mkdir(parents=True, exist_ok=True)

    print("--- 1. GENERATING VERSIONED STAGING PLAYER METRICS ---")
    df_new = compute_evidence_based_ratings()
    
    stg_parquet = staging_dir / "fact_player_metrics.parquet"
    df_new.to_parquet(stg_parquet, index=False)
    stg_hash = hash_file(stg_parquet)
    print(f"Staged dataset saved to {stg_parquet} (SHA256: {stg_hash})")

    # Load baseline pre-fix metrics for comparison
    df_old = pd.read_parquet("backup/production_pre_ratings_fix/fact_player_metrics.parquet")

    print("\n--- 2. FULL-DATASET POPULATION RECONCILIATION ---")
    tot_players = len(df_new)
    assert tot_players == 1217, f"Expected 1,217 players, got {tot_players}"

    elig_bat = int(df_new['batting_ranking_eligible'].sum())
    elig_bowl = int(df_new['bowling_ranking_eligible'].sum())
    elig_both = int((df_new['batting_ranking_eligible'] & df_new['bowling_ranking_eligible']).sum())
    
    lim_bat = int((df_new['batting_confidence_tier'] == 'LIMITED_EVIDENCE').sum())
    ins_bat = int((df_new['batting_confidence_tier'] == 'INSUFFICIENT_DATA').sum())
    
    lim_bowl = int((df_new['bowling_confidence_tier'] == 'LIMITED_EVIDENCE').sum())
    ins_bowl = int((df_new['bowling_confidence_tier'] == 'INSUFFICIENT_DATA').sum())

    ins_both = int((
        (df_new['batting_confidence_tier'] == 'INSUFFICIENT_DATA') & 
        (df_new['bowling_confidence_tier'] == 'INSUFFICIENT_DATA')
    ).sum())

    emerging_only = int((df_new['is_emerging_candidate'] & ~df_new['batting_ranking_eligible'] & ~df_new['bowling_ranking_eligible']).sum())

    reconciliation = {
        "total_players": tot_players,
        "eligible_batters": elig_bat,
        "eligible_bowlers": elig_bowl,
        "eligible_both_disciplines": elig_both,
        "limited_batting_evidence": lim_bat,
        "insufficient_batting_data": ins_bat,
        "limited_bowling_evidence": lim_bowl,
        "insufficient_bowling_data": ins_bowl,
        "insufficient_both_disciplines": ins_both,
        "officially_ranked_batters": elig_bat,
        "officially_ranked_bowlers": elig_bowl,
        "emerging_discovery_candidates": int(df_new['is_emerging_candidate'].sum()),
        "emerging_only_unranked": emerging_only,
        "accounting_check": {
            "batting_partition_sum": elig_bat + lim_bat + ins_bat,
            "bowling_partition_sum": elig_bowl + lim_bowl + ins_bowl,
            "expected_total": 1217
        }
    }
    
    assert reconciliation["accounting_check"]["batting_partition_sum"] == 1217
    assert reconciliation["accounting_check"]["bowling_partition_sum"] == 1217
    print(json.dumps(reconciliation, indent=2))

    with open(rep_dir / "player_ratings_reconciliation.json", "w") as f:
        json.dump(reconciliation, f, indent=2)

    print("\n--- 3. SPECIFIC INVESTIGATION OF ORIGINAL 99-RATED PLAYERS ---")
    # Identify who had 99 in old production
    old_99_bat = df_old[df_old['overall_batting_rating'] >= 99.0]['player_name'].tolist()
    old_99_bowl = df_old[df_old['overall_bowling_rating'] >= 99.0]['player_name'].tolist()

    print(f"Old 99 Batters count: {len(old_99_bat)}")
    print(f"Old 99 Bowlers count: {len(old_99_bowl)}")

    investigation_records = []
    all_99_players = list(set(old_99_bat + old_99_bowl))
    for pname in all_99_players:
        r_old = df_old[df_old['player_name'] == pname].iloc[0]
        r_new = df_new[df_new['player_name'] == pname].iloc[0]
        
        record = {
            "player_id": int(r_new['player_id']),
            "player_name": pname,
            "primary_role": str(r_new['primary_role']),
            "old_batting_rating": float(r_old['overall_batting_rating']),
            "new_batting_rating": float(r_new['batting_rating']) if pd.notnull(r_new['batting_rating']) else None,
            "batting_sample_size": int(r_new['batting_sample_size']),
            "batting_eligible": bool(r_new['batting_ranking_eligible']),
            "batting_tier": str(r_new['batting_confidence_tier']),
            "old_bowling_rating": float(r_old['overall_bowling_rating']),
            "new_bowling_rating": float(r_new['bowling_rating']) if pd.notnull(r_new['bowling_rating']) else None,
            "bowling_sample_size": int(r_new['bowling_sample_size']),
            "bowling_eligible": bool(r_new['bowling_ranking_eligible']),
            "bowling_tier": str(r_new['bowling_confidence_tier']),
            "status": "JUSTIFIED_LEGITIMATE_EVIDENCE" if (
                (pd.notnull(r_new['batting_rating']) and r_new['batting_rating'] >= 90 and r_new['batting_ranking_eligible']) or
                (pd.notnull(r_new['bowling_rating']) and r_new['bowling_rating'] >= 90 and r_new['bowling_ranking_eligible'])
            ) else "CORRECTED_INELIGIBLE_UNRATED"
        }
        investigation_records.append(record)

    df_inv = pd.DataFrame(investigation_records)
    print("\nSample of 99-Rating Investigation:")
    print(df_inv[['player_name', 'primary_role', 'old_batting_rating', 'new_batting_rating', 'batting_sample_size', 'old_bowling_rating', 'new_bowling_rating', 'bowling_sample_size', 'status']].to_string())

    with open(rep_dir / "ratings_99_investigation_report.json", "w") as f:
        json.dump(investigation_records, f, indent=2)

    print("\n--- 4. TOP 25 OFFICIAL DISCIPLINE LEADERBOARDS ---")
    top25_bat = df_new[df_new['batting_ranking_eligible']].sort_values(by='batting_ranking_score', ascending=False).head(25)
    top25_bowl = df_new[df_new['bowling_ranking_eligible']].sort_values(by='bowling_ranking_score', ascending=False).head(25)

    bat_leaderboard = []
    for rank, (_, r) in enumerate(top25_bat.iterrows(), 1):
        bat_leaderboard.append({
            "official_rank": rank,
            "player_id": int(r['player_id']),
            "player_name": str(r['player_name']),
            "primary_role": str(r['primary_role']),
            "matches": int(r['total_matches']),
            "balls_faced": int(r['balls_faced']),
            "runs": int(r['total_runs']),
            "strike_rate": round(float(r['batting_sr']), 1),
            "batting_rating": round(float(r['batting_rating']), 1),
            "confidence_tier": str(r['batting_confidence_tier']),
            "lcb_score": round(float(r['batting_ranking_score']), 3)
        })

    bowl_leaderboard = []
    for rank, (_, r) in enumerate(top25_bowl.iterrows(), 1):
        bowl_leaderboard.append({
            "official_rank": rank,
            "player_id": int(r['player_id']),
            "player_name": str(r['player_name']),
            "primary_role": str(r['primary_role']),
            "matches": int(r['total_matches']),
            "legal_balls": int(r['legal_balls_bowled']),
            "wickets": int(r['bowler_wickets']),
            "economy": round(float(r['bowling_econ']), 2),
            "bowling_rating": round(float(r['bowling_rating']), 1),
            "confidence_tier": str(r['bowling_confidence_tier']),
            "lcb_score": round(float(r['bowling_ranking_score']), 3)
        })

    with open(rep_dir / "official_batting_leaderboard_top25.json", "w") as f:
        json.dump(bat_leaderboard, f, indent=2)

    with open(rep_dir / "official_bowling_leaderboard_top25.json", "w") as f:
        json.dump(bowl_leaderboard, f, indent=2)

    print("Top 25 Leaderboards successfully exported.")

if __name__ == "__main__":
    generate_and_diagnose()
