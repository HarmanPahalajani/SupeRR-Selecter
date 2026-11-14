"""
Promotes corrected evidence-based ratings dataset to production.
"""

import shutil
import hashlib
import json
from pathlib import Path
import duckdb
import pandas as pd
from backend.analytics.export.build_dashboard_tables import build_dashboard_storage

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def promote():
    print("=== PROMOTING EVIDENCE-BASED RATINGS FIX TO PRODUCTION ===")
    
    stg_path = Path("data/staging_ratings/fact_player_metrics.parquet")
    prod_path = Path("data/processed/fact_player_metrics.parquet")
    duckdb_path = Path("data/app/analytics.duckdb")
    user_db_path = Path("data/app/user_store.db")
    
    assert stg_path.exists(), "Staging dataset missing!"
    
    # 1. Promote Parquet
    print(f"Promoting {stg_path} -> {prod_path}...")
    shutil.copy2(stg_path, prod_path)
    h_prod = hash_file(prod_path)
    print(f"  Production fact_player_metrics.parquet updated (SHA256: {h_prod[:16]}...)")
    
    # 2. Update DuckDB views
    print(f"Updating DuckDB views in {duckdb_path}...")
    con = duckdb.connect(str(duckdb_path))
    con.execute("CREATE OR REPLACE VIEW fact_player_metrics AS SELECT * FROM read_parquet('data/processed/fact_player_metrics.parquet');")
    p_cnt = con.execute("SELECT count(*) FROM fact_player_metrics;").fetchone()[0]
    con.close()
    print(f"  DuckDB view refreshed: {p_cnt} players active.")
    assert p_cnt == 1217, f"Expected 1,217 players in DuckDB, got {p_cnt}"
    
    # 3. Update SQLite player_auction_pool
    print(f"Updating SQLite player_auction_pool in {user_db_path}...")
    build_dashboard_storage(processed_dir="data/processed", app_dir="data/app")
    print("  SQLite user_store.db updated with evidence-based baseline pricing.")
    
    # 4. Save state manifest
    manifest = {
        "release_version": "vNext_ratings_fix_v1",
        "timestamp_utc": pd.Timestamp.utcnow().isoformat(),
        "fact_player_metrics_sha256": h_prod,
        "total_players": p_cnt
    }
    with open("data/active_ratings_release.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("=== RATINGS PROMOTION COMPLETE ===")

if __name__ == "__main__":
    promote()
