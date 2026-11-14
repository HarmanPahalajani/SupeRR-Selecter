import urllib.request
import json
import duckdb
import pandas as pd
from pathlib import Path
import hashlib

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_post_switch():
    print("=== POST-SWITCH VERIFICATION AUDIT ===")
    
    # 1. Verify Active Release Version Marker
    v_file = Path("data/active_production_version.json")
    assert v_file.exists(), "Active production version file missing!"
    with open(v_file) as f:
        v_info = json.load(f)
    print(f"Active Release: {v_info.get('active_version')} (Switched at: {v_info.get('switched_at_utc')})")
    
    # 2. Check Models A, B, C, D Checksums Unchanged
    print("\n--- Model Checksums vs Backup ---")
    with open("backup/production_pre_vNext/backup_manifest.json") as f:
        b_manifest = json.load(f)
    model_entries = [x for x in b_manifest if "artifacts\\models" in x["source_path"]]
    for m in model_entries:
        sp = Path(m["source_path"])
        curr_hash = hash_file(sp)
        assert curr_hash == m["sha256"], f"Model {sp} hash mismatch!"
        print(f"  [VERIFIED UNCHANGED] {sp.name}: {curr_hash[:16]}...")
        
    # 3. DuckDB Production Data Check
    print("\n--- DuckDB Active View Row Counts ---")
    con = duckdb.connect("data/app/analytics.duckdb")
    p_cnt = con.execute("SELECT count(*) FROM fact_player_metrics;").fetchone()[0]
    d_cnt = con.execute("SELECT count(*) FROM fact_delivery;").fetchone()[0]
    m_cnt = con.execute("SELECT count(*) FROM dim_match;").fetchone()[0]
    c_cnt = con.execute("SELECT count(*) FROM dim_competition;").fetchone()[0]
    
    # Check top primary players
    top_bat = con.execute("SELECT player_name, overall_batting_rating, eb_batting_impact, total_runs FROM fact_player_metrics ORDER BY overall_batting_rating DESC LIMIT 5;").fetchall()
    top_bowl = con.execute("SELECT player_name, overall_bowling_rating, eb_bowling_impact, bowler_wickets FROM fact_player_metrics ORDER BY overall_bowling_rating DESC LIMIT 5;").fetchall()
    
    # Verify competition scope separation in fact_player_metrics
    primary_scope_players = con.execute("SELECT count(*) FROM fact_player_metrics WHERE competition_scope = 'primary_scope';").fetchone()[0]
    emerging_scope_players = con.execute("SELECT count(*) FROM fact_player_metrics WHERE is_emerging_candidate = 1;").fetchone()[0]
    
    con.close()
    
    print(f"  Active Deliveries: {d_cnt} (Expected: 200,961)")
    print(f"  Active Players:    {p_cnt} (Expected: 1,217)")
    print(f"  Active Matches:    {m_cnt} (Expected: 883)")
    print(f"  Active Competitions: {c_cnt} (Expected: 141)")
    print(f"  Primary Scope Players:  {p_cnt}")
    print(f"  Emerging Discovery Candidates: {emerging_scope_players}")
    assert d_cnt == 200961, f"Expected 200,961 deliveries, got {d_cnt}"
    assert p_cnt == 1217, f"Expected 1,217 players, got {p_cnt}"
    
    print("\nTop 5 Batters in Active Production:")
    for b in top_bat:
        print(f"  {b[0]:25} | Rating: {b[1]:.2f} | EB Impact: {b[2]:.2f} | Runs: {b[3]}")
        
    print("\nTop 5 Bowlers in Active Production:")
    for b in top_bowl:
        print(f"  {b[0]:25} | Rating: {b[1]:.2f} | EB Impact: {b[2]:.2f} | Wickets: {b[3]}")

    # 4. API Endpoint Health
    print("\n--- Live FastAPI v1 Endpoints (Supporting All 8 Frontend Modules) ---")
    endpoints = [
        ("Health (/meta/health)", "http://127.0.0.1:8000/api/v1/meta/health"),
        ("Coverage (/meta/coverage)", "http://127.0.0.1:8000/api/v1/meta/coverage"),
        ("Model Status (/meta/model-status)", "http://127.0.0.1:8000/api/v1/meta/model-status"),
        ("Players List (/players)", "http://127.0.0.1:8000/api/v1/players?limit=5"),
        ("Rankings Batters (/rankings/batters)", "http://127.0.0.1:8000/api/v1/rankings/batters?limit=5"),
        ("Rankings Bowlers (/rankings/bowlers)", "http://127.0.0.1:8000/api/v1/rankings/bowlers?limit=5"),
        ("Auction Pool (/auction/pool)", "http://127.0.0.1:8000/api/v1/auction/pool"),
        ("Watchlists (/watchlists)", "http://127.0.0.1:8000/api/v1/watchlists"),
        ("Methodology (/methodology)", "http://127.0.0.1:8000/api/v1/methodology"),
        ("Methodology Validation (/methodology/validation)", "http://127.0.0.1:8000/api/v1/methodology/validation"),
        ("Staging Meta (/staging/meta)", "http://127.0.0.1:8000/api/v1/staging/meta"),
        ("Staging Pressure Comparison (/staging/pressure-comparison)", "http://127.0.0.1:8000/api/v1/staging/pressure-comparison?limit=5")
    ]
    
    for name, url in endpoints:
        req = urllib.request.urlopen(url, timeout=5)
        res_data = json.loads(req.read().decode('utf-8'))
        print(f"  [OK 200] {name:40} -> {type(res_data).__name__} (status: {req.status})")
        
    print("\n=== POST-SWITCH VERIFICATION SUCCESSFUL ===")

if __name__ == "__main__":
    verify_post_switch()
