import sys
import os
sys.path.insert(0, os.path.abspath("."))

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

from backend.analytics.pressure_performers.pressure_opportunities import tag_high_pressure_deliveries
from backend.analytics.pressure_performers.contribution import compute_delivery_contributions
from backend.analytics.pressure_performers.match_aggregation import aggregate_player_matches
from backend.analytics.pressure_performers.reliability import compute_career_pressure_metrics
from backend.analytics.pressure_performers.ranking import compute_pressure_rankings
from backend.analytics.pressure_performers.classification import classify_dataframe

def run_all_checks():
    con = duckdb.connect()
    con.execute("ATTACH 'data/app/analytics.duckdb' AS db")

    print("=" * 70)
    print("ITEM 1: CRAI SENSITIVITY ANALYSIS")
    print("=" * 70)

    # 1. Full Dataset Current Production Rankings across k
    df_batters = con.execute("""
        SELECT player_id, player_name, hp_balls, hp_matches, hp_raw_rae_per_100,
               hp_posterior_mean, hp_posterior_se, is_pressure_ranked
        FROM db.fact_player_pressure_metrics
        WHERE competition_scope = 'IPL_T20I' AND pressure_context = 'ALL' AND hp_balls > 0
    """).df()

    k_values = [0.00, 0.25, 0.50, 0.75, 1.00]

    rankings_by_k = {}
    top10_by_k = {}
    top25_by_k = {}

    for k in k_values:
        df = df_batters.copy()
        df[f"crai_{k}"] = df["hp_posterior_mean"] - k * df["hp_posterior_se"]
        qualified = (df["hp_balls"] >= 25) & (df["hp_matches"] >= 3) & (df["hp_posterior_mean"] > 0)
        df_qual = df[qualified].sort_values(
            by=[f"crai_{k}", "hp_posterior_mean", "hp_balls", "player_id"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)
        df_qual[f"rank_{k}"] = np.arange(1, len(df_qual) + 1)
        rankings_by_k[k] = df_qual.set_index("player_id")[f"rank_{k}"]
        top10_by_k[k] = list(df_qual.head(10)["player_name"])
        top25_by_k[k] = list(df_qual.head(25)["player_name"])

    print("\nTop 10 Batters across Uncertainty Multipliers k:")
    for k in k_values:
        print(f"k = {k:.2f}: {', '.join(top10_by_k[k][:5])} | 6-10: {', '.join(top10_by_k[k][5:10])}")

    # Overlap / Jaccard similarity vs k = 0.50 (current production)
    print("\nOverlap with Current Production (k = 0.50):")
    base_top10 = set(top10_by_k[0.50])
    base_top25 = set(top25_by_k[0.50])
    for k in k_values:
        t10_overlap = len(base_top10.intersection(set(top10_by_k[k])))
        t25_overlap = len(base_top25.intersection(set(top25_by_k[k])))
        print(f"k = {k:.2f}: Top 10 Overlap = {t10_overlap}/10 ({t10_overlap*10}%), Top 25 Overlap = {t25_overlap}/25 ({t25_overlap*4}%)")

    # Rank correlation vs k = 0.50
    base_ranks = rankings_by_k[0.50]
    print(f"\nRank Stability (Kendall tau & Spearman rho vs k = 0.50 across all N = {len(base_ranks)} ranked):")
    for k in k_values:
        common_ids = base_ranks.index.intersection(rankings_by_k[k].index)
        r_base = base_ranks.loc[common_ids]
        r_k = rankings_by_k[k].loc[common_ids]
        sp_r, _ = stats.spearmanr(r_base, r_k)
        kd_t, _ = stats.kendalltau(r_base, r_k)
        print(f"k = {k:.2f}: Spearman rho = {sp_r:.4f}, Kendall tau = {kd_t:.4f}")

    # Pairwise rank correlation between adjacent k
    print("\nAdjacent Step Stability (k_i vs k_{i+1}):")
    for i in range(len(k_values)-1):
        k1, k2 = k_values[i], k_values[i+1]
        c_ids = rankings_by_k[k1].index.intersection(rankings_by_k[k2].index)
        sp_r, _ = stats.spearmanr(rankings_by_k[k1].loc[c_ids], rankings_by_k[k2].loc[c_ids])
        kd_t, _ = stats.kendalltau(rankings_by_k[k1].loc[c_ids], rankings_by_k[k2].loc[c_ids])
        print(f"k = {k1:.2f} vs {k2:.2f}: Spearman rho = {sp_r:.4f}, Kendall tau = {kd_t:.4f}")

    # Chronological Out-of-Sample Validation
    print("\n--- Chronological Out-of-Sample Validation (Train <= 2024, Test >= 2025) ---")
    df_del = con.execute("""
        SELECT * FROM read_parquet('data/processed/fact_delivery_scored.parquet')
        WHERE is_primary_scope = true
    """).df()

    df_hp_all = tag_high_pressure_deliveries(df_del, is_primary=True)
    df_hp_all = compute_delivery_contributions(df_hp_all)
    df_hp = df_hp_all[df_hp_all["is_high_pressure"]].copy()
    
    df_hp["season_int"] = pd.to_numeric(df_hp["season"].astype(str).str[:4], errors="coerce").fillna(2000).astype(int)

    train_hp = df_hp[df_hp["season_int"] <= 2024].copy()
    test_hp = df_hp[df_hp["season_int"] >= 2025].copy()

    train_match = aggregate_player_matches(train_hp)
    test_match = aggregate_player_matches(test_hp)

    test_perf = test_match.groupby("player_id").agg(
        future_hp_balls=("hp_balls", "sum"),
        future_hp_rae=("hp_rae", "sum"),
    ).reset_index()
    test_perf["future_hp_rae_per_100"] = 100.0 * test_perf["future_hp_rae"] / np.maximum(test_perf["future_hp_balls"], 1.0)

    # Players with >= 10 balls in test period
    test_eval = test_perf[test_perf["future_hp_balls"] >= 10].copy()
    print(f"Qualifying players with >= 10 pressure balls in 2025: N = {len(test_eval)}")
    print(f"Future positive RAE prevalence in test cohort: {(test_eval['future_hp_rae_per_100'] > 0).mean()*100:.1f}%")

    train_metrics = compute_career_pressure_metrics(train_match, min_eval_balls=20, min_eval_matches=3, n_bootstrap=200)

    for k in k_values:
        train_metrics[f"crai_{k}"] = train_metrics["hp_posterior_mean"] - k * train_metrics["hp_posterior_se"]
        merged = train_metrics.merge(test_eval, on="player_id", how="inner")
        sp_r, sp_p = stats.spearmanr(merged[f"crai_{k}"], merged["future_hp_rae_per_100"])
        kd_t, kd_p = stats.kendalltau(merged[f"crai_{k}"], merged["future_hp_rae_per_100"])

        ranked_top = merged.sort_values(by=f"crai_{k}", ascending=False)
        p_at_10 = (ranked_top.head(10)["future_hp_rae_per_100"] > 0).mean()
        p_at_20 = (ranked_top.head(20)["future_hp_rae_per_100"] > 0).mean() if len(ranked_top) >= 20 else np.nan

        print(f"k = {k:.2f}: Spearman rho = {sp_r:.4f} (p={sp_p:.4f}), Kendall tau = {kd_t:.4f}, P@10 = {p_at_10*100:.1f}%, P@20 = {p_at_20*100:.1f}%")

    print("\n" + "=" * 70)
    print("ITEM 3: EMERGING POPULATION RECONCILIATION")
    print("=" * 70)

    dim_players = con.execute("SELECT * FROM read_parquet('data/processed/dim_player.parquet')").df()
    emerging_players = dim_players[dim_players["is_emerging"] == True].copy()
    total_emerging = len(emerging_players)
    print(f"Total Emerging participants in dim_player: {total_emerging}")

    all_scope_metrics = con.execute("""
        SELECT * FROM db.fact_player_pressure_metrics
        WHERE competition_scope = 'ALL' AND pressure_context = 'ALL'
    """).df()

    emerging_metrics = all_scope_metrics.merge(emerging_players[["player_id"]], on="player_id", how="inner")
    print(f"Emerging players in fact_player_pressure_metrics (ALL scope & ALL context): {len(emerging_metrics)}")

    assessed = emerging_metrics[emerging_metrics["hp_balls"] > 0]
    not_assessed = emerging_metrics[emerging_metrics["hp_balls"] == 0]
    print(f"Assessed batters (hp_balls > 0): {len(assessed)}")
    print(f"Not assessed / Zero hp_balls: {len(not_assessed)}")
    
    missing_ids = set(emerging_players["player_id"]) - set(emerging_metrics["player_id"])
    print(f"Emerging players entirely absent from metrics table: {len(missing_ids)}")

    # Check deliveries faced by these players in the whole dataset
    del_batters = con.execute("""
        SELECT batter_id as player_id, count(*) as career_balls_faced,
               sum(CASE WHEN is_high_pressure THEN 1 ELSE 0 END) as career_hp_balls
        FROM read_parquet('data/processed/fact_delivery_scored.parquet')
        GROUP BY batter_id
    """).df()
    
    del_bowlers = con.execute("""
        SELECT bowler_id as player_id, count(*) as career_balls_bowled
        FROM read_parquet('data/processed/fact_delivery_scored.parquet')
        GROUP BY bowler_id
    """).df()

    not_assessed_details = not_assessed.merge(del_batters, on="player_id", how="left").merge(del_bowlers, on="player_id", how="left")
    not_assessed_details["career_balls_faced"] = not_assessed_details["career_balls_faced"].fillna(0).astype(int)
    not_assessed_details["career_hp_balls"] = not_assessed_details["career_hp_balls"].fillna(0).astype(int)
    not_assessed_details["career_balls_bowled"] = not_assessed_details["career_balls_bowled"].fillna(0).astype(int)

    def classify_reason(row):
        if row["career_balls_faced"] == 0 and row["career_balls_bowled"] > 0:
            return "Specialist Bowler (0 balls faced, active bowler)"
        elif row["career_balls_faced"] == 0 and row["career_balls_bowled"] == 0:
            return "Squad Reserve (0 balls faced, 0 balls bowled)"
        elif row["career_balls_faced"] > 0 and row["career_hp_balls"] == 0:
            return f"Batted only in Low/Medium Pressure (Faced {row['career_balls_faced']} balls, 0 HP)"
        else:
            return "Other"

    not_assessed_details["exclusion_reason"] = not_assessed_details.apply(classify_reason, axis=1)
    
    print("\nExclusion Reason Summary for the 58 unassessed Emerging players:")
    print(not_assessed_details["exclusion_reason"].value_counts())

    print("\nBreakdown table of all 58 unassessed Emerging players:")
    cols_to_print = ["player_id", "player_name", "career_balls_faced", "career_hp_balls", "career_balls_bowled", "exclusion_reason"]
    print(not_assessed_details[cols_to_print].to_string(index=False))

    dual_scope = emerging_players[emerging_players["is_primary_scope"] == True]
    print(f"\nDual-Scope players (in both Emerging and IPL/T20I): {len(dual_scope)}")
    for _, r in dual_scope.iterrows():
        print(f"  ID {r['player_id']}: {r['player_name']} (Emerging: True, Primary Scope: True)")

    print("\n" + "=" * 70)
    print("ITEM 4: BATTING RAE CORRECTNESS")
    print("=" * 70)

    sample_del = con.execute("""
        SELECT match_id, inning, over, ball, batter_id, bowler_id,
               runs_batter, runs_extra, runs_total,
               expected_batter_runs, expected_runs,
               is_high_pressure, pressure_index
        FROM read_parquet('data/processed/fact_delivery_scored.parquet')
        WHERE is_high_pressure = true AND runs_extra > 0
        LIMIT 10
    """).df()

    print("\nSample high-pressure deliveries with extras (runs_extra > 0):")
    for _, r in sample_del.iterrows():
        print(f"Match {r['match_id']} Ov {r['over']}.{r['ball']}: runs_batter={r['runs_batter']}, extras={r['runs_extra']}, total={r['runs_total']} | exp_batter_runs={r['expected_batter_runs']:.3f}, exp_total_runs={r['expected_runs']:.3f}")

    con.close()

if __name__ == "__main__":
    run_all_checks()
