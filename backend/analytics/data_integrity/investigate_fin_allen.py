import pandas as pd
import numpy as np

def investigate():
    print("=== INVESTIGATING FIN ALLEN & DATASET SCOPE ===")
    
    # 1. Look up dim_player
    df_players = pd.read_parquet("data/processed/dim_player.parquet")
    print(f"Total players in dim_player: {len(df_players)}")
    fin_players = df_players[df_players["player_name"].str.contains("Allen|Fin", case=False, na=False)]
    print("\nMatching players in dim_player:")
    print(fin_players)

    # 2. Check canonical deliveries
    df_deliv = pd.read_parquet("data/processed/fact_delivery_canonical.parquet")
    print(f"\nTotal canonical deliveries: {len(df_deliv)}")
    
    # Batting deliveries for Finn Allen (4847)
    bat_deliv = df_deliv[df_deliv["striker_id"] == 4847]
    print(f"\nDeliveries as striker (ID 4847): {len(bat_deliv)}")
    if len(bat_deliv) > 0:
        print("Competitions as striker:")
        print(bat_deliv["comp_name"].value_counts())
        print("is_primary_scope as striker:")
        print(bat_deliv["is_primary_scope"].value_counts())
    
    # Bowling deliveries for Finn Allen (4847)
    bowl_deliv = df_deliv[df_deliv["bowler_id"] == 4847]
    print(f"\nDeliveries as bowler (ID 4847): {len(bowl_deliv)}")
    if len(bowl_deliv) > 0:
        print(bowl_deliv)
    else:
        print("Finn Allen has ZERO deliveries as bowler across ALL canonical deliveries!")
        
    # Check fact_player_metrics.parquet
    df_metrics = pd.read_parquet("data/processed/fact_player_metrics.parquet")
    print(f"\nTotal players in fact_player_metrics: {len(df_metrics)}")
    fin_metrics = df_metrics[df_metrics["player_id"] == 4847]
    if len(fin_metrics) > 0:
        row = fin_metrics.iloc[0]
        print(f"\nFinn Allen metrics in fact_player_metrics.parquet:")
        cols_to_show = [c for c in df_metrics.columns if any(k in c.lower() for k in ["bowl", "econ", "wicket", "overs", "ball", "bat", "rate", "rank"])]
        for c in cols_to_show:
            print(f"  {c}: {row.get(c)}")
            
    # Check all players where legal_balls_bowled == 0 or overs_bowled == 0
    zero_balls = df_metrics[(df_metrics["legal_balls_bowled"] == 0) | (df_metrics["legal_balls_bowled"].isna())]
    print(f"\nTotal players with 0 or NaN legal_balls_bowled: {len(zero_balls)}")
    print("Distinct bowling_econ values for players with 0 legal_balls_bowled:")
    print(zero_balls["bowling_econ"].value_counts(dropna=False).head(10))

if __name__ == "__main__":
    investigate()
