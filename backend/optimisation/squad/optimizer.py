import json
import sqlite3
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

def optimize_squad(
    budget_remaining: int = 450000000,
    players_to_acquire: int = 5,
    locked_player_ids: list = None,
    excluded_player_ids: list = None,
    strategy: str = "balanced", # balanced, upside, risk_controlled
    role_requirements: dict = None,
    max_overseas: int = 8,
    current_overseas: int = 4,
    db_path: str = "data/app/analytics.duckdb",
    user_db_path: str = "data/app/user_store.db"
):
    locked_player_ids = set(locked_player_ids or [])
    excluded_player_ids = set(excluded_player_ids or [])
    
    con = duckdb.connect(db_path, read_only=True)
    players_df = con.execute("""
        SELECT 
            player_id, player_name, primary_role, bat_style, bowl_style, pace_or_spin, is_wk,
            overall_batting_rating, overall_bowling_rating, batting_rating, bowling_rating,
            batting_ranking_eligible, bowling_ranking_eligible,
            eb_batting_impact, eb_bowling_impact,
            batting_uncertainty, bowling_uncertainty, death_overs_bowled, pp_overs_bowled,
            total_matches, confidence_tier
        FROM fact_player_metrics
        WHERE total_matches >= 3
    """).df()
    con.close()

    # Merge prices from SQLite user pool
    conn = sqlite3.connect(user_db_path)
    prices_df = pd.read_sql_query("SELECT player_id, overseas_status, is_available, estimated_price_low, estimated_price_mid, estimated_price_high FROM player_auction_pool", conn)
    conn.close()

    df = players_df.merge(prices_df, on='player_id', how='left')
    df['estimated_price_mid'] = df['estimated_price_mid'].fillna(20000000).astype(int)
    df['estimated_price_low'] = df['estimated_price_low'].fillna(10000000).astype(int)
    df['estimated_price_high'] = df['estimated_price_high'].fillna(40000000).astype(int)
    df['overseas_status'] = df['overseas_status'].fillna('Unknown')
    df['is_available'] = df['is_available'].fillna(1).astype(int)

    # Filter available and non-excluded
    df = df[df['is_available'] == 1]
    df = df[~df['player_id'].isin(excluded_player_ids)]

    # Compute strategy utility
    # Integer utility scaled by 100 for CP-SAT
    if strategy == "upside":
        bat_val = df['eb_batting_impact'] + 1.2 * df['batting_uncertainty']
        bowl_val = df['eb_bowling_impact'] + 1.2 * df['bowling_uncertainty']
        cost_series = df['estimated_price_mid']
    elif strategy == "risk_controlled":
        bat_val = df['eb_batting_impact'] - 0.8 * df['batting_uncertainty']
        bowl_val = df['eb_bowling_impact'] - 0.8 * df['bowling_uncertainty']
        cost_series = df['estimated_price_high'] # Conservative high cost
    else: # balanced
        bat_val = df['eb_batting_impact']
        bowl_val = df['eb_bowling_impact']
        cost_series = df['estimated_price_mid']

    # Evidence-conditioned utility: an unevidenced discipline must never inflate player utility
    bat_contrib = np.where(df['batting_ranking_eligible'], bat_val * 100.0 + 50.0, 30.0)
    bowl_contrib = np.where(df['bowling_ranking_eligible'], bowl_val * 100.0 + 50.0, 30.0)

    raw_utility = np.where(
        df['primary_role'].isin(['BATTER', 'WICKETKEEPER', 'batter', 'wicketkeeper_batter']),
        np.where(df['bowling_ranking_eligible'], 0.85 * bat_contrib + 0.15 * bowl_contrib, bat_contrib),
        np.where(
            df['primary_role'].isin(['BOWLER', 'bowler']),
            np.where(df['batting_ranking_eligible'], 0.85 * bowl_contrib + 0.15 * bat_contrib, bowl_contrib),
            # Genuine All-rounder
            np.where(
                df['batting_ranking_eligible'] & df['bowling_ranking_eligible'],
                0.50 * bat_contrib + 0.50 * bowl_contrib + 10.0,
                np.where(df['batting_ranking_eligible'], bat_contrib, np.where(df['bowling_ranking_eligible'], bowl_contrib, 25.0))
            )
        )
    )
    df['utility'] = np.clip(raw_utility, 10.0, 150.0).astype(int)
    df['cost'] = cost_series.astype(int)

    # Setup CP-SAT Model
    model = cp_model.CpModel()
    n_players = len(df)
    x = [model.NewBoolVar(f"select_{df.iloc[i]['player_id']}") for i in range(n_players)]

    # Constraint 1: Exact player acquisition count
    model.Add(sum(x[i] for i in range(n_players)) == players_to_acquire)

    # Constraint 2: Budget limit (scaled to Lakhs to prevent 32-bit overflow)
    scale = 100000 # 1 Lakh INR
    budget_scaled = int(budget_remaining // scale)
    costs_scaled = [int(df.iloc[i]['cost'] // scale) for i in range(n_players)]
    model.Add(sum(x[i] * costs_scaled[i] for i in range(n_players)) <= budget_scaled)

    # Constraint 3: Overseas slots
    available_overseas_slots = max(0, max_overseas - current_overseas)
    is_overseas = [1 if df.iloc[i]['overseas_status'] == 'Overseas' else 0 for i in range(n_players)]
    model.Add(sum(x[i] * is_overseas[i] for i in range(n_players)) <= available_overseas_slots)

    # Constraint 4: Locked players
    for i in range(n_players):
        if df.iloc[i]['player_id'] in locked_player_ids:
            model.Add(x[i] == 1)

    # Role constraints if specified
    if role_requirements:
        for role, limits in role_requirements.items():
            min_r = limits.get('min', 0)
            max_r = limits.get('max', players_to_acquire)
            if role in ['top_order_batter', 'batter']:
                role_mask = [1 if df.iloc[i]['primary_role'] in ['BATTER', 'WICKETKEEPER', 'batter', 'wicketkeeper_batter'] else 0 for i in range(n_players)]
            elif role in ['middle_order_batter']:
                role_mask = [1 if df.iloc[i]['primary_role'] in ['BATTER', 'ALL_ROUNDER', 'batter', 'all_rounder'] else 0 for i in range(n_players)]
            elif role in ['wicketkeeper_batter', 'wicketkeeper']:
                role_mask = [1 if df.iloc[i]['primary_role'] in ['WICKETKEEPER', 'wicketkeeper_batter'] or df.iloc[i]['is_wk'] else 0 for i in range(n_players)]
            elif role in ['bowler']:
                role_mask = [1 if df.iloc[i]['primary_role'] in ['BOWLER', 'bowler'] else 0 for i in range(n_players)]
            elif role in ['all_rounder']:
                role_mask = [1 if df.iloc[i]['primary_role'] in ['ALL_ROUNDER', 'all_rounder'] else 0 for i in range(n_players)]
            elif role == 'pace_bowler':
                role_mask = [1 if df.iloc[i]['pace_or_spin'] == 'Pace' else 0 for i in range(n_players)]
            elif role == 'spin_bowler':
                role_mask = [1 if df.iloc[i]['pace_or_spin'] == 'Spin' else 0 for i in range(n_players)]
            elif role == 'death_overs_specialist':
                role_mask = [1 if df.iloc[i]['death_overs_bowled'] >= 8.0 else 0 for i in range(n_players)]
            else:
                role_mask = [1 if df.iloc[i]['primary_role'].upper() == role.upper() else 0 for i in range(n_players)]

            model.Add(sum(x[i] * role_mask[i] for i in range(n_players)) >= min_r)
            model.Add(sum(x[i] * role_mask[i] for i in range(n_players)) <= max_r)

    # Objective: Maximise utility
    utilities = df['utility'].tolist()
    model.Maximize(sum(x[i] * utilities[i] for i in range(n_players)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    status_name = solver.StatusName(status)
    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return {
            "status": status_name,
            "strategy": strategy,
            "players": [],
            "total_spend": 0,
            "budget_remaining": budget_remaining,
            "message": "No feasible squad combination satisfies all constraints (budget or role minimums)."
        }

    selected_indices = [i for i in range(n_players) if solver.Value(x[i]) == 1]
    selected_df = df.iloc[selected_indices].copy()

    total_spend = int(selected_df['cost'].sum())
    rem_purse = budget_remaining - total_spend

    players_list = []
    for _, r in selected_df.iterrows():
        players_list.append({
            "player_id": int(r['player_id']),
            "player_name": str(r['player_name']),
            "primary_role": str(r['primary_role']),
            "bat_style": str(r['bat_style']),
            "bowl_style": str(r['bowl_style']),
            "pace_or_spin": str(r['pace_or_spin']),
            "cost_inr": int(r['cost']),
            "utility_score": int(r['utility']),
            "overseas_status": str(r['overseas_status']),
            "confidence_tier": str(r['confidence_tier'])
        })

    return {
        "status": status_name,
        "strategy": strategy,
        "players": players_list,
        "total_spend": total_spend,
        "budget_remaining": rem_purse,
        "overseas_count": sum(1 for p in players_list if p['overseas_status'] == 'Overseas'),
        "role_breakdown": {
            "batters": sum(1 for p in players_list if p['primary_role'].upper() in ['BATTER', 'WICKETKEEPER']),
            "bowlers": sum(1 for p in players_list if p['primary_role'].upper() == 'BOWLER'),
            "all_rounders": sum(1 for p in players_list if p['primary_role'].upper() == 'ALL_ROUNDER'),
            "wicketkeepers": sum(1 for p in players_list if p['primary_role'].upper() == 'WICKETKEEPER')
        }
    }
