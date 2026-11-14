import sys
import os
sys.path.insert(0, os.path.abspath("."))

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

def run_bowler_closure_analyses():
    con = duckdb.connect()
    con.execute("ATTACH 'data/app/analytics.duckdb' AS db")
    
    print("=" * 75)
    print("ITEM 1: FORMULA VERIFICATION (SITUATION A & B)")
    print("=" * 75)
    
    from backend.analytics.pressure_bowlers.pressure_engine import DefensiveBowlingPressureEngine
    engine = DefensiveBowlingPressureEngine()
    
    # Independent mathematical verification of Second-Innings Formula
    def independent_second_innings_pressure(r_rem, b_rem, w_hand, rrr, b_max=120.0):
        w_cap = 6.0 + 0.55 * w_hand
        threat_ratio = w_cap / max(rrr, 1.0)
        progress = (b_max - b_rem) / b_max
        margin_stress = np.exp(-r_rem / 16.0) * (1.0 if b_rem <= 18.0 else 0.0) * (w_hand / 10.0)
        z2 = 1.85 * (threat_ratio - 1.0) + 1.50 * margin_stress + 0.75 * progress * (1.0 if threat_ratio > 0.80 else 0.0)
        p = 10.0 / (1.0 + np.exp(-1.20 * z2))
        return np.clip(p, 0.5, 9.8)

    # Independent mathematical verification of First-Innings Formula
    def independent_first_innings_pressure(surge, balls_rem, wkts_in_hand):
        death_challenge = np.clip((30.0 - balls_rem) / 30.0, 0.0, 1.0) * (wkts_in_hand / 10.0)
        z1 = 1.15 * surge + 0.90 * death_challenge
        p_inn1 = 10.0 / (1.0 + np.exp(-1.10 * z1))
        return np.clip(p_inn1, 0.5, 9.8)

    # Situation A: Defending 8 from 6 balls (assuming w_hand=5, 4, 10)
    for w in [10.0, 5.0, 4.0]:
        df_a = pd.DataFrame([{"innings": 2, "runs_needed": 8.0, "legal_balls_remaining": 6.0, "wickets_in_hand": w, "required_run_rate": 8.0}])
        eng_p = engine.compute_second_innings_defensive_pressure(df_a).iloc[0]
        ind_p = independent_second_innings_pressure(8.0, 6.0, w, 8.0)
        print(f"Situation A (8 off 6, w={w}): Engine={eng_p:.4f}, Independent Calc={ind_p:.4f}, Diff={abs(eng_p - ind_p):.2e}")

    # Situation B: Defending 35 from 6 balls
    for w in [10.0, 5.0]:
        df_b = pd.DataFrame([{"innings": 2, "runs_needed": 35.0, "legal_balls_remaining": 6.0, "wickets_in_hand": w, "required_run_rate": 35.0}])
        eng_p = engine.compute_second_innings_defensive_pressure(df_b).iloc[0]
        ind_p = independent_second_innings_pressure(35.0, 6.0, w, 35.0)
        print(f"Situation B (35 off 6, w={w}): Engine={eng_p:.4f}, Independent Calc={ind_p:.4f}, Diff={abs(eng_p - ind_p):.2e}")

    # Innings 1 check
    df_inn1_surge = pd.DataFrame([{
        "innings": 1, "pre_ball_legal_balls": 60.0, "legal_balls_remaining": 60.0,
        "pre_ball_score": 110.0, "pre_ball_wickets": 1.0, "wickets_in_hand": 9.0,
        "current_run_rate": 11.0, "resource_consumed_pct": 0.30, "venue_par_score": 170.0
    }])
    p_inn1_eng = engine.compute_first_innings_defensive_pressure(df_inn1_surge).iloc[0]
    print(f"Innings 1 Opposition Surging (110/1 in 10 ov): Engine = {p_inn1_eng:.4f}")

    print("\n" + "=" * 75)
    print("ITEM 3A: CRAI SENSITIVITY ANALYSIS FOR BOWLING LEADERBOARD")
    print("=" * 75)
    
    # Read qualified bowlers from fact_player_pressure_bowling_metrics
    df_bowlers = con.execute("""
        SELECT player_id, player_name, hp_overs, hp_matches, hp_raw_runs_saved_per_6,
               hp_posterior_mean, hp_posterior_se, hp_risk_adjusted_impact, is_pressure_ranked
        FROM db.fact_player_pressure_bowling_metrics
        WHERE competition_scope = 'IPL_T20I' AND hp_overs > 0
    """).df()
    
    k_values = [0.00, 0.25, 0.50, 0.75, 1.00]
    rankings_by_k = {}
    top10_by_k = {}
    top25_by_k = {}

    for k in k_values:
        df = df_bowlers.copy()
        df[f"crai_{k}"] = df["hp_posterior_mean"] - k * df["hp_posterior_se"]
        qualified = (df["hp_overs"] >= 4.0) & (df["hp_matches"] >= 3) & (df["hp_posterior_mean"] > 0)
        df_qual = df[qualified].sort_values(
            by=[f"crai_{k}", "hp_posterior_mean", "hp_overs", "player_id"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)
        df_qual[f"rank_{k}"] = np.arange(1, len(df_qual) + 1)
        rankings_by_k[k] = df_qual.set_index("player_id")[f"rank_{k}"]
        top10_by_k[k] = list(df_qual.head(10)["player_name"])
        top25_by_k[k] = list(df_qual.head(25)["player_name"])

    print("\nTop 10 Bowlers across Uncertainty Multipliers k:")
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

    print("\n" + "=" * 75)
    print("ITEM 3B: RIGOROUS CHRONOLOGICAL OUT-OF-SAMPLE VALIDATION")
    print("=" * 75)

    from backend.analytics.pressure_bowlers.pressure_opportunities import tag_high_pressure_bowling_deliveries
    from backend.analytics.pressure_bowlers.contribution import compute_bowling_delivery_contributions
    from backend.analytics.pressure_bowlers.match_aggregation import aggregate_bowler_matches
    from backend.analytics.pressure_bowlers.reliability import compute_career_bowler_pressure_metrics

    df_del = con.execute("""
        SELECT * FROM read_parquet('data/processed/fact_delivery_scored.parquet')
        WHERE is_primary_scope = true
    """).df()

    df_del["bowling_pressure_index"] = engine.compute_defensive_pressure(df_del)
    df_tagged = tag_high_pressure_bowling_deliveries(df_del, is_primary=True)
    df_contrib = compute_bowling_delivery_contributions(df_tagged)
    df_hp = df_contrib[df_contrib["is_high_pressure_bowling"]].copy()
    df_hp["season_int"] = pd.to_numeric(df_hp["season"].astype(str).str[:4], errors="coerce").fillna(2000).astype(int)

    train_hp = df_hp[df_hp["season_int"] <= 2024].copy()
    test_hp = df_hp[df_hp["season_int"] >= 2025].copy()

    train_match = aggregate_bowler_matches(train_hp)
    test_match = aggregate_bowler_matches(test_hp)

    # Future performance metrics in test period (2025)
    test_perf = test_match.groupby("player_id").agg(
        future_hp_balls=("hp_balls", "sum"),
        future_hp_overs=("hp_overs", "sum"),
        future_hp_runs_saved=("hp_runs_saved", "sum"),
        future_hp_wickets=("hp_wickets", "sum"),
        future_hp_exp_wickets=("hp_exp_wickets", "sum"),
        future_hp_wae=("hp_wae", "sum"),
        future_hp_matches=("match_id", "nunique"),
    ).reset_index()

    test_perf["future_runs_saved_per_6"] = test_perf["future_hp_runs_saved"] / np.maximum(test_perf["future_hp_overs"], 0.1)
    test_perf["future_wickets_per_6"] = test_perf["future_hp_wickets"] / np.maximum(test_perf["future_hp_overs"], 0.1)
    test_perf["future_wae_per_6"] = test_perf["future_hp_wae"] / np.maximum(test_perf["future_hp_overs"], 0.1)

    # Filter to bowlers with >= 2.0 overs in future test period
    test_eval = test_perf[test_perf["future_hp_overs"] >= 2.0].copy()
    print(f"Qualifying bowlers with >= 2.0 overs in 2025 forward test: N = {len(test_eval)}")
    
    pos_runs_saved_prev = (test_eval["future_runs_saved_per_6"] > 0).mean()
    pos_wickets_prev = (test_eval["future_hp_wickets"] >= 2).mean()
    pos_wae_prev = (test_eval["future_wae_per_6"] > 0).mean()
    print(f"Base prevalence of positive runs saved in test period: {pos_runs_saved_prev*100:.1f}%")
    print(f"Base prevalence of >= 2 wickets under pressure: {pos_wickets_prev*100:.1f}%")
    print(f"Base prevalence of positive WAE under pressure: {pos_wae_prev*100:.1f}%")

    train_summary = df_del[df_del["season"] <= 2024].groupby("bowler_id").agg(
        career_matches=("match_id", "nunique"),
        career_balls_bowled=("is_legal_ball", "sum"),
        career_runs_conceded=("bowler_conceded_runs", "sum"),
        career_wickets=("is_bowler_wicket", "sum")
    ).reset_index().rename(columns={"bowler_id": "player_id"})

    train_metrics = compute_career_bowler_pressure_metrics(train_match, career_summary_df=train_summary, min_eval_overs=3.0, min_eval_matches=3, n_bootstrap=200)

    # 1. Run Prevention Validation across k
    print("\n--- 1. Run-Prevention Out-of-Sample Performance across k ---")
    for k in k_values:
        train_metrics[f"crai_{k}"] = train_metrics["hp_posterior_mean"] - k * train_metrics["hp_posterior_se"]
        merged = train_metrics.merge(test_eval, on="player_id", how="inner")
        
        sp_r, sp_p = stats.spearmanr(merged[f"crai_{k}"], merged["future_runs_saved_per_6"])
        kd_t, kd_p = stats.kendalltau(merged[f"crai_{k}"], merged["future_runs_saved_per_6"])
        
        # Fisher z 95% CI
        z = np.arctanh(sp_r)
        se_z = 1.0 / np.sqrt(len(merged) - 3)
        ci_low, ci_high = np.tanh(z - 1.96 * se_z), np.tanh(z + 1.96 * se_z)

        ranked_top = merged.sort_values(by=f"crai_{k}", ascending=False)
        p_at_10 = (ranked_top.head(10)["future_runs_saved_per_6"] > 0).mean()
        p_at_20 = (ranked_top.head(20)["future_runs_saved_per_6"] > 0).mean()

        print(f"k = {k:.2f}: Spearman rho = {sp_r:.4f} (95% CI: [{ci_low:.4f}, {ci_high:.4f}], p={sp_p:.4f}), Kendall tau = {kd_t:.4f}, P@10 = {p_at_10*100:.1f}%, P@20 = {p_at_20*100:.1f}%")

    # 2. Wicket-Creation Predictive Performance
    print("\n--- 2. Wicket-Creation Predictive Performance under Pressure ---")
    merged_prod = train_metrics.merge(test_eval, on="player_id", how="inner")
    
    wkt_col = "hp_wickets_per_match" if "hp_wickets_per_match" in merged_prod.columns else "hp_wickets"
    wae_col = "hp_wae_crai" if "hp_wae_crai" in merged_prod.columns else ("hp_wae_per_6" if "hp_wae_per_6" in merged_prod.columns else "hp_wae")

    sp_wkt, p_wkt = stats.spearmanr(merged_prod[wkt_col], merged_prod["future_wickets_per_6"])
    sp_wae, p_wae = stats.spearmanr(merged_prod[wae_col], merged_prod["future_wae_per_6"])
    
    z_wkt = np.arctanh(sp_wkt)
    se_wkt = 1.0 / np.sqrt(len(merged_prod) - 3)
    ci_wkt_low, ci_wkt_high = np.tanh(z_wkt - 1.96 * se_wkt), np.tanh(z_wkt + 1.96 * se_wkt)

    top_wkt_bowlers = merged_prod.sort_values(by=wkt_col, ascending=False)
    p10_wkt = (top_wkt_bowlers.head(10)["future_hp_wickets"] >= 2).mean()
    p20_wkt = (top_wkt_bowlers.head(20)["future_hp_wickets"] >= 2).mean()

    top_wae_bowlers = merged_prod.sort_values(by=wae_col, ascending=False)
    p10_wae = (top_wae_bowlers.head(10)["future_wae_per_6"] > 0).mean()
    p20_wae = (top_wae_bowlers.head(20)["future_wae_per_6"] > 0).mean()

    print(f"Wicket Volume ({wkt_col}): Spearman rho = {sp_wkt:.4f} (95% CI: [{ci_wkt_low:.4f}, {ci_wkt_high:.4f}], p={p_wkt:.4f}), P@10 = {p10_wkt*100:.1f}%, P@20 = {p20_wkt*100:.1f}% (Base: {pos_wickets_prev*100:.1f}%)")
    print(f"Wickets Above Expected ({wae_col}): Spearman rho = {sp_wae:.4f} (p={p_wae:.4f}), P@10 = {p10_wae*100:.1f}%, P@20 = {p20_wae*100:.1f}% (Base: {pos_wae_prev*100:.1f}%)")

    # 3. Naive Baseline Comparison: Does Pressure Rating Outperform Career Economy?
    print("\n--- 3. Benchmark against Naive Career Baseline ---")
    merged_prod["neg_career_econ"] = -1.0 * (merged_prod["career_runs_conceded"] / np.maximum(merged_prod["career_balls_bowled"] / 6.0, 1.0))
    sp_base, p_base = stats.spearmanr(merged_prod["neg_career_econ"], merged_prod["future_runs_saved_per_6"])
    print(f"Naive Career Economy vs Future Pressure Runs Saved: Spearman rho = {sp_base:.4f} (p={p_base:.4f})")
    
    crai_rho, crai_p = stats.spearmanr(merged_prod["crai_0.5"], merged_prod["future_runs_saved_per_6"])
    print(f"SupeRR Pressure CRAI (k=0.50) vs Future Pressure Runs Saved: Spearman rho = {crai_rho:.4f} (p={crai_p:.4f})")
    print(f"Relative Predictive Improvement of Pressure CRAI over Naive Economy: +{((crai_rho - sp_base)/abs(sp_base))*100:.1f}%")

    print("\n" + "=" * 75)
    print("ITEM 3C: POPULATION RECONCILIATION & ARITHMETIC")
    print("=" * 75)

    dim_player = pd.read_parquet("data/processed/dim_player.parquet")
    df_can = pd.read_parquet("data/processed/fact_delivery_canonical.parquet")

    all_ids = set(dim_player["player_id"].unique())
    
    # Primary regular deliveries
    df_pri = df_can[(df_can["is_primary_scope"] == True) & (df_can["is_super_over"] == False)]
    pri_batters = set(df_pri["striker_id"].unique())
    pri_bowlers = set(df_pri["bowler_id"].unique())
    pri_players = pri_batters.union(pri_bowlers)

    # Emerging regular deliveries
    df_emg = df_can[(df_can["is_primary_scope"] == False) & (df_can["is_super_over"] == False)]
    emg_batters = set(df_emg["striker_id"].unique())
    emg_bowlers = set(df_emg["bowler_id"].unique())
    emg_players = emg_batters.union(emg_bowlers)

    both_scopes = pri_players.intersection(emg_players)
    emg_only = emg_players - pri_players
    pri_only = pri_players - emg_players
    neither = all_ids - (pri_players.union(emg_players))

    pri_pure_batters = pri_batters - pri_bowlers

    print(f"Total Master Player Identities in dim_player: {len(all_ids)}")
    print(f"1. Total Primary-Scope Participants: {len(pri_players)}")
    print(f"   ├── Primary-Scope Bowlers (bowled >= 1 ball in primary): {len(pri_bowlers)}")
    print(f"   └── Primary-Scope Pure Batters (0 balls bowled in primary): {len(pri_pure_batters)}")
    print(f"   Arithmetic Check: {len(pri_bowlers)} + {len(pri_pure_batters)} = {len(pri_bowlers) + len(pri_pure_batters)}")
    print(f"2. Emerging-Only Participants (0 primary balls): {len(emg_only)}")
    print(f"3. Squad Reserves / Zero Delivery Participants: {len(neither)}")
    print(f"Grand Total Check: {len(pri_players)} + {len(emg_only)} + {len(neither)} = {len(pri_players) + len(emg_only) + len(neither)}")

    con.close()

if __name__ == "__main__":
    run_bowler_closure_analyses()
