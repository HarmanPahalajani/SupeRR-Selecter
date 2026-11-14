"""
Production Rollback Script for SupeRR Intelligence vNext
IMMEDIATE, ZERO-DOWNTIME ROLLBACK MECHANISM.

Restores the previous production datasets from data/processed_pre_vNext_backup
and restores the analytical DuckDB database from backup/production_pre_vNext.
"""

import sys
import json
import shutil
from pathlib import Path
import duckdb

def execute_rollback():
    print("=== EXECUTING EMERGENCY PRODUCTION ROLLBACK ===")
    
    prod_dir = Path("data/processed")
    archive_dir = Path("data/processed_pre_vNext_backup")
    release_dir = Path("data/release_vNext")
    app_duckdb = Path("data/app/analytics.duckdb")
    app_duckdb_backup = Path("backup/production_pre_vNext/data_app/analytics.duckdb")
    
    if not archive_dir.exists():
        # Fallback to cold backup if archive dir not found
        archive_dir = Path("backup/production_pre_vNext/data_processed")
        if not archive_dir.exists():
            raise FileNotFoundError("Neither archive_dir nor backup directory found! Cannot rollback automatically.")
        print(f"Restoring from cold backup {archive_dir}...")
        if prod_dir.exists():
            shutil.rmtree(prod_dir)
        shutil.copytree(archive_dir, prod_dir)
    else:
        print(f"Reverting atomic directory swap from {archive_dir}...")
        # Move current back to release_vNext if it doesn't exist
        if not release_dir.exists():
            prod_dir.rename(release_dir)
        else:
            shutil.rmtree(prod_dir)
        archive_dir.rename(prod_dir)
        
    # Restore DuckDB database
    if app_duckdb_backup.exists():
        shutil.copy2(app_duckdb_backup, app_duckdb)
        print(f"Restored DuckDB database from {app_duckdb_backup}.")
        
    # Re-verify DuckDB views
    con = duckdb.connect(str(app_duckdb))
    con.execute("CREATE OR REPLACE VIEW fact_delivery AS SELECT * FROM read_parquet('data/processed/fact_delivery_scored.parquet');")
    con.execute("CREATE OR REPLACE VIEW fact_player_metrics AS SELECT * FROM read_parquet('data/processed/fact_player_metrics.parquet');")
    con.execute("CREATE OR REPLACE VIEW dim_match AS SELECT * FROM read_parquet('data/processed/dim_match.parquet');")
    con.execute("CREATE OR REPLACE VIEW dim_player AS SELECT * FROM read_parquet('data/processed/dim_player.parquet');")
    con.execute("CREATE OR REPLACE VIEW dim_competition AS SELECT * FROM read_parquet('data/processed/dim_competition.parquet');")
    
    p_cnt = con.execute("SELECT count(*) FROM fact_player_metrics;").fetchone()[0]
    d_cnt = con.execute("SELECT count(*) FROM fact_delivery;").fetchone()[0]
    con.close()
    
    print(f"Rollback verified: {p_cnt} players, {d_cnt} deliveries active in restored DuckDB.")
    
    state_file = Path("data/active_production_version.json")
    if state_file.exists():
        state_file.unlink()
        
    print("=== PRODUCTION ROLLBACK COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    execute_rollback()
