import sys
import os
sys.path.insert(0, os.path.abspath("."))

import pandas as pd
import numpy as np

def analyze_emerging():
    dim_player = pd.read_parquet("data/processed/dim_player.parquet")
    df_can = pd.read_parquet("data/processed/fact_delivery_canonical.parquet")
    df_scored = pd.read_parquet("data/processed/fact_delivery_scored.parquet")
    
    # Emerging regular deliveries
    df_emerging = df_can[(df_can["is_primary_scope"] == False) & (df_can["is_super_over"] == False)]
    emerging_batters = set(df_emerging["striker_id"].unique())
    emerging_bowlers = set(df_emerging["bowler_id"].unique())
    emerging_players = emerging_batters.union(emerging_bowlers)
    
    print(f"Total Emerging participants: {len(emerging_players)}")
    print(f"Emerging batters who faced >= 1 regular ball in Emerging comps: {len(emerging_batters)}")
    print(f"Emerging bowlers who bowled >= 1 regular ball in Emerging comps: {len(emerging_bowlers)}")
    
    # Primary players
    df_primary = df_can[(df_can["is_primary_scope"] == True) & (df_can["is_super_over"] == False)]
    primary_players = set(df_primary["striker_id"].unique()).union(set(df_primary["bowler_id"].unique()))
    both_scopes = emerging_players.intersection(primary_players)
    emerging_only = emerging_players - primary_players
    print(f"Dual-scope players (in Emerging AND Primary IPL/T20I): {len(both_scopes)}")
    print(f"Emerging-only players: {len(emerging_only)}")
    
    # Now check high-pressure deliveries in emerging competitions
    # High pressure in Emerging scope
    df_scored_emerging = df_scored[(df_scored["is_primary_scope"] == False) & (df_scored["is_super_over"] == False)]
    
    from backend.analytics.pressure_performers.pressure_opportunities import tag_high_pressure_deliveries
    df_hp_emg = tag_high_pressure_deliveries(df_scored_emerging, is_primary=False)
    df_hp_emg_pos = df_hp_emg[df_hp_emg["is_high_pressure"]]
    
    hp_batters_emerging = set(df_hp_emg_pos["striker_id"].unique())
    print(f"Batters who faced >= 1 qualifying high-pressure delivery in Emerging comps: {len(hp_batters_emerging)}")
    
    # Let's check fact_player_pressure_metrics for scope = 'EMERGING'
    import duckdb
    con = duckdb.connect("data/app/analytics.duckdb", read_only=True)
    metrics_emg = con.execute("""
        SELECT player_id, player_name, hp_balls, hp_matches, hp_raw_rae_per_100,
               hp_posterior_mean, hp_risk_adjusted_impact, is_pressure_ranked, pressure_rank
        FROM fact_player_pressure_metrics
        WHERE competition_scope = 'EMERGING' AND pressure_context = 'ALL'
    """).df()
    print(f"Rows in fact_player_pressure_metrics with scope='EMERGING' & context='ALL': {len(metrics_emg)}")
    assessed_in_db = metrics_emg[metrics_emg["hp_balls"] > 0]
    print(f"Assessed batters in DB with hp_balls > 0: {len(assessed_in_db)}")
    ranked_in_db = metrics_emg[metrics_emg["is_pressure_ranked"] == True]
    print(f"Ranked batters in DB: {len(ranked_in_db)}")
    
    # 58 Unassessed Players
    assessed_ids = set(assessed_in_db["player_id"].unique())
    unassessed_ids = emerging_players - assessed_ids
    print(f"\nRemaining unassessed emerging players: {len(unassessed_ids)}")
    
    unassessed_list = []
    for pid in sorted(unassessed_ids):
        p_name = dim_player[dim_player["player_id"] == pid]["player_name"].iloc[0] if pid in dim_player["player_id"].values else "Unknown"
        
        # Balls faced in emerging
        emg_bf = len(df_emerging[df_emerging["striker_id"] == pid])
        emg_hp_bf = len(df_hp_emg_pos[df_hp_emg_pos["striker_id"] == pid])
        
        # Balls bowled in emerging
        emg_bb = len(df_emerging[df_emerging["bowler_id"] == pid])
        
        # Comp name(s)
        comps = list(df_emerging[(df_emerging["striker_id"] == pid) | (df_emerging["bowler_id"] == pid)]["comp_name"].unique())
        comp_str = "; ".join(comps) if comps else "None"
        
        # Scope status
        is_dual = pid in both_scopes
        scope_str = "Dual-Scope (IPL/T20I + Emerging)" if is_dual else "Emerging-Only"
        
        # Reason
        if emg_bf == 0 and emg_bb > 0:
            reason = "Specialist Bowler: Did not bat in Emerging tournament (0 balls faced, active bowler)"
        elif emg_bf > 0 and emg_hp_bf == 0:
            reason = f"Batted only in Low/Medium Pressure: Faced {emg_bf} balls in Emerging comps, but 0 qualifying high-pressure balls"
        elif emg_bf == 0 and emg_bb == 0:
            reason = "Squad Member: Did not bat or bowl in Emerging tournament deliveries"
        else:
            reason = f"Unassessed: {emg_bf} balls, {emg_hp_bf} HP balls"
            
        unassessed_list.append({
            "player_id": pid,
            "player_name": p_name,
            "scope_membership": scope_str,
            "competitions": comp_str,
            "emerging_balls_faced": emg_bf,
            "emerging_hp_balls_faced": emg_hp_bf,
            "emerging_balls_bowled": emg_bb,
            "exclusion_reason": reason
        })
        
    df_unassessed = pd.DataFrame(unassessed_list)
    print("\nBreakdown of 58 unassessed reasons:")
    print(df_unassessed["exclusion_reason"].value_counts())
    
    print("\nBreakdown by Scope Membership:")
    print(df_unassessed["scope_membership"].value_counts())
    
    # Save unassessed reconciliation table to csv / markdown
    df_unassessed.to_csv("artifacts/reports/emerging_58_unassessed_reconciliation.csv", index=False)
    print("\nSaved unassessed table to artifacts/reports/emerging_58_unassessed_reconciliation.csv")

    con.close()

if __name__ == "__main__":
    analyze_emerging()
