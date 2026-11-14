import sqlite3
from pathlib import Path
import duckdb
import pandas as pd

def build_dashboard_storage(processed_dir: str = "data/processed", app_dir: str = "data/app"):
    proc_path = Path(processed_dir)
    app_path = Path(app_dir)
    app_path.mkdir(parents=True, exist_ok=True)

    duckdb_file = app_path / "analytics.duckdb"
    sqlite_file = app_path / "user_store.db"

    print(f"Initializing DuckDB analytical store at {duckdb_file}...")
    con = duckdb.connect(str(duckdb_file))

    # Create analytical views directly over Parquet files
    con.execute(f"CREATE OR REPLACE VIEW fact_delivery AS SELECT * FROM read_parquet('{proc_path}/fact_delivery_scored.parquet');")
    con.execute(f"CREATE OR REPLACE VIEW fact_player_metrics AS SELECT * FROM read_parquet('{proc_path}/fact_player_metrics.parquet');")
    con.execute(f"CREATE OR REPLACE VIEW dim_match AS SELECT * FROM read_parquet('{proc_path}/dim_match.parquet');")
    con.execute(f"CREATE OR REPLACE VIEW dim_player AS SELECT * FROM read_parquet('{proc_path}/dim_player.parquet');")
    con.execute(f"CREATE OR REPLACE VIEW dim_competition AS SELECT * FROM read_parquet('{proc_path}/dim_competition.parquet');")

    # Verify query
    player_count = con.execute("SELECT count(*) FROM fact_player_metrics;").fetchone()[0]
    delivery_count = con.execute("SELECT count(*) FROM fact_delivery;").fetchone()[0]
    print(f"DuckDB views loaded: {player_count} players, {delivery_count} deliveries.")
    con.close()

    print(f"Initializing SQLite user store at {sqlite_file}...")
    conn = sqlite3.connect(str(sqlite_file))
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS watchlists (
        watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS watchlist_players (
        watchlist_id INTEGER,
        player_id INTEGER,
        priority TEXT DEFAULT 'Medium',
        target_role TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (watchlist_id, player_id),
        FOREIGN KEY (watchlist_id) REFERENCES watchlists(watchlist_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_notes (
        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        author TEXT DEFAULT 'Analyst',
        content TEXT NOT NULL,
        verdict TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_scenarios (
        scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_name TEXT NOT NULL,
        config_json TEXT NOT NULL,
        solution_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Editable player auction pool (price assumptions, nationality, availability)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_auction_pool (
        player_id INTEGER PRIMARY KEY,
        player_name TEXT NOT NULL,
        primary_role TEXT,
        overseas_status TEXT DEFAULT 'Unknown',
        is_available INTEGER DEFAULT 1,
        estimated_price_low INTEGER DEFAULT 5000000,
        estimated_price_mid INTEGER DEFAULT 20000000,
        estimated_price_high INTEGER DEFAULT 50000000,
        price_confidence TEXT DEFAULT 'Medium',
        price_source TEXT DEFAULT 'Analyst Reference'
    );
    """)

    # Populate default auction pool if empty from fact_player_metrics
    cur.execute("DELETE FROM player_auction_pool;")
    p_df = pd.read_parquet(proc_path / "fact_player_metrics.parquet")
    insert_records = []
    for _, row in p_df.iterrows():
        pid = int(row['player_id'])
        pname = str(row['player_name'])
        prole = str(row['primary_role'])
        # Generate plausible baseline reference prices based on verified discipline rating
        rating = None
        if prole.upper() in ['BATTER', 'WICKETKEEPER']:
            r_val = row.get('batting_rating')
            if pd.notnull(r_val):
                rating = float(r_val)
        elif prole.upper() == 'BOWLER':
            r_val = row.get('bowling_rating')
            if pd.notnull(r_val):
                rating = float(r_val)
        else:
            r_val = row.get('overall_player_rating')
            if pd.notnull(r_val):
                rating = float(r_val)

        if rating is None:
            low, mid, high = 2000000, 5000000, 10000000      # 20L - 1 Cr (unrated/insufficient sample)
        elif rating > 85:
            low, mid, high = 80000000, 120000000, 160000000 # 8-16 Cr
        elif rating > 70:
            low, mid, high = 40000000, 70000000, 100000000 # 4-10 Cr
        elif rating > 55:
            low, mid, high = 15000000, 30000000, 50000000   # 1.5-5 Cr
        else:
            low, mid, high = 3000000, 8000000, 15000000     # 30L-1.5 Cr

        insert_records.append((pid, pname, prole, 'Unknown', 1, low, mid, high, 'Medium', 'Model Base Reference'))

    cur.executemany("""
    INSERT INTO player_auction_pool (player_id, player_name, primary_role, overseas_status, is_available, estimated_price_low, estimated_price_mid, estimated_price_high, price_confidence, price_source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, insert_records)
    print(f"Populated {len(insert_records)} players into player_auction_pool.")

    # Create default watchlist if none
    wl_count = cur.execute("SELECT count(*) FROM watchlists;").fetchone()[0]
    if wl_count == 0:
        cur.execute("INSERT INTO watchlists (name, description) VALUES ('Top Auction Targets 2027', 'Priority high-pressure performers and undervalued recruits');")
        wl_id = cur.lastrowid
        # Add top undervalued talents
        p_df = pd.read_parquet(proc_path / "fact_player_metrics.parquet")
        top_undervalued = p_df[p_df['is_undervalued_talent'] == True].head(5)
        for _, r in top_undervalued.iterrows():
            cur.execute("INSERT INTO watchlist_players (watchlist_id, player_id, priority, target_role) VALUES (?, ?, 'High', ?);", (wl_id, int(r['player_id']), str(r['primary_role'])))

    conn.commit()
    conn.close()
    print("Dashboard storage initialized successfully!")

if __name__ == "__main__":
    build_dashboard_storage()
