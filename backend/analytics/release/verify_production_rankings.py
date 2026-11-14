import duckdb
import pandas as pd
import numpy as np

def verify_production_rankings():
    print("=== VERIFYING PRODUCTION RANKINGS & METRICS ===")
    
    df_players = pd.read_parquet("data/processed/fact_player_metrics.parquet")
    df_deliv = pd.read_parquet("data/processed/fact_delivery_scored.parquet")
    
    print(f"Total Players: {len(df_players)}")
    print(f"Total Deliveries: {len(df_deliv)}")
    
    # 1. Scope Separation
    assert 'competition_scope' in df_players.columns, "competition_scope missing"
    assert 'is_emerging_candidate' in df_players.columns, "is_emerging_candidate missing"
    
    # 2. Batting and Bowling Ratings
    print("\nTop 10 Batters (Primary Senior Scope):")
    top_batters = df_players.sort_values(by="overall_batting_rating", ascending=False).head(10)
    for idx, row in top_batters.iterrows():
        print(f"  {row['player_name']:25} | Role: {row['primary_role']:12} | Rating: {row['overall_batting_rating']:5.1f} | EB Impact: {row['eb_batting_impact']:+6.3f} | BF: {row['balls_faced']:4.0f}")
        
    print("\nTop 10 Bowlers (Primary Senior Scope):")
    top_bowlers = df_players.sort_values(by="overall_bowling_rating", ascending=False).head(10)
    for idx, row in top_bowlers.iterrows():
        print(f"  {row['player_name']:25} | Role: {row['primary_role']:12} | Rating: {row['overall_bowling_rating']:5.1f} | EB Impact: {row['eb_bowling_impact']:+6.3f} | BB: {row['legal_balls_bowled']:4.0f}")
        
    # 3. Pressure Stats Distribution
    print("\nDelivery Pressure Distribution:")
    p_series = df_deliv['situational_pressure']
    print(f"  Mean:   {p_series.mean():.3f}")
    print(f"  Std:    {p_series.std():.3f}")
    print(f"  Median: {p_series.median():.3f}")
    print(f"  P10:    {p_series.quantile(0.10):.3f}")
    print(f"  P90:    {p_series.quantile(0.90):.3f}")
    
    # Check Pressure Tiers in Deliveries
    tier_counts = df_deliv['pressure_tier'].value_counts()
    print("\nPressure Tier Counts in Promoted Deliveries:")
    for tier, count in tier_counts.items():
        print(f"  {tier:12}: {count:7d} ({count/len(df_deliv)*100:5.1f}%)")
        
    # Check 1st Innings vs Chase Deliveries
    inn1_cnt = (df_deliv['innings'] == 1).sum()
    inn2_cnt = (df_deliv['innings'] == 2).sum()
    print(f"\nInnings Split: Innings 1 = {inn1_cnt:,} | Innings 2 = {inn2_cnt:,}")
    
    # Check Emerging Discovery Candidates
    emg_cand = df_players[df_players['is_emerging_candidate'] == True]
    print(f"\nEmerging Discovery Candidates: {len(emg_cand)} players")
    for idx, row in emg_cand.head(5).iterrows():
        print(f"  [Discovery Candidate] {row['player_name']:25} | Emerging Balls: {row['emerging_pressure_balls']} | Emerging Runs: {row['emerging_pressure_runs']}")

    print("\n=== PRODUCTION RANKINGS & METRIC VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    verify_production_rankings()
