import pandas as pd
import numpy as np

def reconcile():
    dim_player = pd.read_parquet("data/processed/dim_player.parquet")
    df_can = pd.read_parquet("data/processed/fact_delivery_canonical.parquet")
    
    all_player_ids = set(dim_player["player_id"].unique())
    print(f"1. Total unique players in dim_player: {len(all_player_ids)}")
    
    # Primary regular deliveries
    df_primary = df_can[(df_can["is_primary_scope"] == True) & (df_can["is_super_over"] == False)]
    primary_batters = set(df_primary["striker_id"].unique())
    primary_bowlers = set(df_primary["bowler_id"].unique())
    primary_players = primary_batters.union(primary_bowlers)
    print(f"2. Players with IPL/T20I (primary) regular data: {len(primary_players)}")
    
    # Emerging regular deliveries
    df_emerging = df_can[(df_can["is_primary_scope"] == False) & (df_can["is_super_over"] == False)]
    emerging_batters = set(df_emerging["striker_id"].unique())
    emerging_bowlers = set(df_emerging["bowler_id"].unique())
    emerging_players = emerging_batters.union(emerging_bowlers)
    print(f"3. Players with Emerging competition data: {len(emerging_players)}")
    
    # Both scopes
    both_scopes = primary_players.intersection(emerging_players)
    print(f"4. Players appearing in BOTH scopes: {len(both_scopes)}")
    
    # Emerging only
    emerging_only = emerging_players - primary_players
    print(f"5. Emerging-only players: {len(emerging_only)}")
    
    # Primary only
    primary_only = primary_players - emerging_players
    print(f"   Primary-only players: {len(primary_only)}")
    
    # Neither scope (in dim_player but no deliveries, e.g. squad members who didn't bat or bowl)
    neither = all_player_ids - (primary_players.union(emerging_players))
    print(f"   Players in dim_player with 0 deliveries in either scope: {len(neither)}")
    
    # Super over only?
    df_so = df_can[df_can["is_super_over"] == True]
    so_players = set(df_so["striker_id"].unique()).union(set(df_so["bowler_id"].unique()))
    so_only = so_players - (primary_players.union(emerging_players))
    print(f"10. Super-over-only players: {len(so_only)}")

    # Check metrics
    metrics = pd.read_parquet("data/processed/fact_player_metrics.parquet")
    print(f"\nTotal rows in fact_player_metrics: {len(metrics)}")
    bat_eligible = set(metrics[metrics["batting_ranking_eligible"] == True]["player_id"].unique())
    bowl_eligible = set(metrics[metrics["bowling_ranking_eligible"] == True]["player_id"].unique())
    both_eligible = bat_eligible.intersection(bowl_eligible)
    
    print(f"6. Official batting-eligible players: {len(bat_eligible)}")
    print(f"7. Official bowling-eligible players: {len(bowl_eligible)}")
    print(f"8. Dual-discipline eligible players: {len(both_eligible)}")
    
    insufficient = all_player_ids - bat_eligible - bowl_eligible
    print(f"9. Players with insufficient evidence in BOTH disciplines: {len(insufficient)}")
    
    # Verification sum
    print(f"\nReconciliation check:")
    print(f"  Primary regular deliveries: {len(df_primary)}")
    print(f"  Primary super over deliveries: {len(df_can[(df_can['is_primary_scope'] == True) & (df_can['is_super_over'] == True)])}")
    print(f"  Emerging regular deliveries: {len(df_emerging)}")
    print(f"  Emerging super over deliveries: {len(df_can[(df_can['is_primary_scope'] == False) & (df_can['is_super_over'] == True)])}")
    print(f"  Total canonical deliveries: {len(df_can)}")

if __name__ == "__main__":
    reconcile()
