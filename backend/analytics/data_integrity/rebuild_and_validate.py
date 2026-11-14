import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import shutil
import pandas as pd
import numpy as np
from backend.analytics.ranking.build_ratings import compute_evidence_based_ratings
from backend.analytics.export.build_dashboard_tables import build_dashboard_storage

def run_rebuild():
    print("=== STEP 1: COMPUTING EVIDENCE-BASED RATINGS WITH STRICT SCOPE ISOLATION ===")
    staging_dir = Path("data/staging_ratings")
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_file = staging_dir / "fact_player_metrics.parquet"

    metrics = compute_evidence_based_ratings(
        proc_path=Path("data/processed"),
        p11_raw_path=Path("data/raw/playing_eleven.csv")
    )
    
    print(f"Computed metrics for {len(metrics)} players.")
    metrics.to_parquet(staging_file, index=False)
    print(f"Saved staged metrics to {staging_file}")

    print("\n=== STEP 2: VERIFYING INVARIANTS ON STAGED METRICS ===")
    # 1. Total players
    assert len(metrics) == 1217, f"Expected 1217 players, got {len(metrics)}"
    
    # 2. Non-negative counts
    assert (metrics["legal_balls_bowled"] >= 0).all(), "Negative balls bowled found"
    assert (metrics["runs_conceded"] >= 0).all(), "Negative runs conceded found"
    assert (metrics["bowler_wickets"] >= 0).all(), "Negative bowler wickets found"
    assert (metrics["balls_faced"] >= 0).all(), "Negative balls faced found"
    assert (metrics["total_runs"] >= 0).all(), "Negative total runs found"

    # 3. Fin Allen checks
    fin = metrics[metrics["player_id"] == 4847].iloc[0]
    assert fin["legal_balls_bowled"] == 0, "Finn Allen must have 0 legal balls bowled"
    assert pd.isna(fin["bowling_econ"]), f"Finn Allen must have NaN bowling_econ, got {fin['bowling_econ']}"
    assert pd.isna(fin["bowling_rating"]), "Finn Allen must have NaN bowling_rating"
    assert pd.isna(fin["bowling_official_rank"]), "Finn Allen must have NaN bowling_official_rank"
    assert fin["batting_ranking_eligible"] == True, "Finn Allen must be batting eligible"
    assert pd.notnull(fin["batting_rating"]), "Finn Allen must have batting rating"
    print("✓ Fin Allen checks passed: 0 legal balls, null economy, null bowling rating/rank, valid batting rating.")

    # 4. Zero balls bowled -> null economy
    zero_balls = metrics[metrics["legal_balls_bowled"] == 0]
    assert len(zero_balls) > 0, "Expected non-bowlers"
    assert zero_balls["bowling_econ"].isna().all(), "All 0-ball bowlers must have NaN bowling_econ"
    assert zero_balls["bowling_sr"].isna().all(), "All 0-ball bowlers must have NaN bowling_sr"
    assert zero_balls["bowling_avg"].isna().all(), "All 0-ball bowlers must have NaN bowling_avg"
    assert zero_balls["bowling_rating"].isna().all(), "All 0-ball bowlers must have NaN bowling_rating"
    assert zero_balls["bowling_official_rank"].isna().all(), "All 0-ball bowlers must have NaN bowling_official_rank"
    print(f"✓ All {len(zero_balls)} non-bowlers verified: 100% NaN economy, strike rate, average, rating, and rank.")

    # 5. Positive balls bowled -> exact economy formula
    pos_balls = metrics[metrics["legal_balls_bowled"] > 0]
    expected_econ = (pos_balls["runs_conceded"] * 6.0) / pos_balls["legal_balls_bowled"]
    diff = np.abs(pos_balls["bowling_econ"] - expected_econ).max()
    assert diff < 1e-9, f"Economy calculation mismatch, max diff: {diff}"
    print(f"✓ All {len(pos_balls)} bowlers with positive balls match exact cricket economy formula (max diff {diff}).")

    # 6. Zero balls faced -> null batting SR
    zero_bat = metrics[metrics["balls_faced"] == 0]
    assert len(zero_bat) > 0, "Expected non-batters"
    assert zero_bat["batting_sr"].isna().all(), "All 0-ball batters must have NaN batting_sr"
    assert zero_bat["batting_avg"].isna().all(), "All 0-ball batters must have NaN batting_avg"
    assert zero_bat["batting_rating"].isna().all(), "All 0-ball batters must have NaN batting_rating"
    assert zero_bat["batting_official_rank"].isna().all(), "All 0-ball batters must have NaN batting_official_rank"
    print(f"✓ All {len(zero_bat)} non-batters verified: 100% NaN batting SR, average, rating, and rank.")

    # 7. Official ranking eligibility and ranks
    bat_elig = metrics[metrics["batting_ranking_eligible"] == True]
    bowl_elig = metrics[metrics["bowling_ranking_eligible"] == True]
    assert (bat_elig["batting_rating"].notnull()).all(), "Eligible batters must have rating"
    assert (bowl_elig["bowling_rating"].notnull()).all(), "Eligible bowlers must have rating"
    assert (bat_elig["batting_official_rank"].notnull()).all(), "Eligible batters must have rank"
    assert (bowl_elig["bowling_official_rank"].notnull()).all(), "Eligible bowlers must have rank"
    
    inelig_bat = metrics[metrics["batting_ranking_eligible"] == False]
    inelig_bowl = metrics[metrics["bowling_ranking_eligible"] == False]
    assert (inelig_bat["batting_official_rank"].isna()).all(), "Ineligible batters must have NaN rank"
    assert (inelig_bowl["bowling_official_rank"].isna()).all(), "Ineligible bowlers must have NaN rank"
    print(f"✓ Official ranking integrity passed: {len(bat_elig)} ranked batters, {len(bowl_elig)} ranked bowlers.")

    # 8. Promote staging to production
    print("\n=== STEP 3: PROMOTING TO PRODUCTION ===")
    prod_file = Path("data/processed/fact_player_metrics.parquet")
    shutil.copy2(staging_file, prod_file)
    print(f"Promoted {staging_file} -> {prod_file}")

    print("\n=== STEP 4: REBUILDING DUCKDB AND STORAGE VIEWS ===")
    build_dashboard_storage(processed_dir="data/processed", app_dir="data/app")
    print("Storage rebuild complete.")

if __name__ == "__main__":
    run_rebuild()
