import sqlite3
import numpy as np
import pandas as pd
import duckdb

def simulate_auction(
    target_player_id: int,
    bid_cap: int,
    user_budget: int = 150000000,
    n_simulations: int = 1000,
    random_seed: int = 42,
    inflation_factor: float = 1.0,
    db_path: str = "data/app/analytics.duckdb",
    user_db_path: str = "data/app/user_store.db"
):
    np.random.seed(random_seed)

    # Fetch player details and price assumptions
    conn = sqlite3.connect(user_db_path)
    cur = conn.cursor()
    target_row = cur.execute("""
        SELECT player_id, player_name, primary_role, estimated_price_low, estimated_price_mid, estimated_price_high, price_confidence, price_source
        FROM player_auction_pool WHERE player_id = ?
    """, (target_player_id,)).fetchone()
    conn.close()

    if not target_row:
        return {"error": f"Player ID {target_player_id} not found in auction pool."}

    pid, pname, prole, p_low, p_mid, p_high, p_conf, p_source = target_row
    p_low = int(p_low * inflation_factor)
    p_mid = int(p_mid * inflation_factor)
    p_high = int(p_high * inflation_factor)

    # Simulate final market bidding price using triangular distribution
    # Triangular(low, mode, high)
    simulated_market_prices = np.random.triangular(p_low, p_mid, p_high, size=n_simulations)

    # Acquisition frequency: our bid cap >= simulated market price AND bid_cap <= user_budget
    won_mask = (bid_cap >= simulated_market_prices) & (simulated_market_prices <= user_budget)
    acquisition_frequency = float(np.mean(won_mask))

    # Expected spend if won
    won_prices = simulated_market_prices[won_mask]
    avg_spend = float(np.mean(won_prices)) if len(won_prices) > 0 else 0.0

    # Bid curve across varying bid levels (from 0.5 * mid to 1.5 * high)
    bid_steps = np.linspace(p_low * 0.8, p_high * 1.3, 10)
    bid_curve = []
    for step in bid_steps:
        prob = float(np.mean(step >= simulated_market_prices))
        bid_curve.append({
            "bid_amount": int(step),
            "acquisition_frequency": round(prob, 3),
            "win_probability": round(prob, 3)  # preserved for backward compatibility
        })

    # Replacement priority tree if target is lost
    con = duckdb.connect(db_path, read_only=True)
    if prole.upper() in ['BOWLER']:
        sort_clause = "bowling_ranking_score DESC NULLS LAST"
        elig_filter = "bowling_ranking_eligible = true"
    elif prole.upper() in ['BATTER', 'WICKETKEEPER']:
        sort_clause = "batting_ranking_score DESC NULLS LAST"
        elig_filter = "batting_ranking_eligible = true"
    else:
        sort_clause = "overall_player_rating DESC NULLS LAST"
        elig_filter = "(batting_ranking_eligible = true OR bowling_ranking_eligible = true)"

    replacements_df = con.execute(f"""
        SELECT player_id, player_name, primary_role, overall_batting_rating, overall_bowling_rating, confidence_tier
        FROM fact_player_metrics
        WHERE UPPER(primary_role) = UPPER('{prole}') AND player_id != {target_player_id} AND {elig_filter}
        ORDER BY {sort_clause}
        LIMIT 4
    """).df()
    con.close()

    conn = sqlite3.connect(user_db_path)
    prices_df = pd.read_sql_query("SELECT player_id, estimated_price_mid FROM player_auction_pool", conn)
    conn.close()

    replacements_df = replacements_df.merge(prices_df, on='player_id', how='left')
    replacements_df['estimated_price_mid'] = replacements_df['estimated_price_mid'].fillna(20000000).astype(int)

    replacement_tree = []
    for _, r in replacements_df.iterrows():
        replacement_tree.append({
            "player_id": int(r['player_id']),
            "player_name": str(r['player_name']),
            "primary_role": str(r['primary_role']),
            "estimated_price": int(r['estimated_price_mid']),
            "confidence_tier": str(r['confidence_tier'])
        })

    return {
        "target_player": {
            "player_id": pid,
            "player_name": pname,
            "primary_role": prole,
            "price_low": p_low,
            "price_mid": p_mid,
            "price_high": p_high,
            "price_confidence": p_conf,
            "price_source": p_source
        },
        "bid_cap": bid_cap,
        "user_budget": user_budget,
        "n_simulations": n_simulations,
        "acquisition_frequency": round(acquisition_frequency, 3),
        "win_probability": round(acquisition_frequency, 3),  # backward compatibility alias
        "expected_expenditure_if_won": int(avg_spend),
        "risk_of_exceeding_budget": round(float(np.mean(simulated_market_prices > user_budget)), 3),
        "bid_curve": bid_curve,
        "replacement_tree": replacement_tree
    }
