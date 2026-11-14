"""
Chronological Validation Module for Pressure Bowling
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Evaluates out-of-sample repeatability, rank stability, and predictive validity
across chronological seasons (Train: 2022-2024 -> Val: 2025 -> Holdout: 2026).
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau, pearsonr


def run_chronological_bowling_validation(
    match_df: pd.DataFrame,
    min_eval_overs: float = 3.0,
    min_eval_matches: int = 2
) -> Dict[str, Any]:
    """
    Evaluates whether past high-pressure bowling metrics predict future high-pressure performance.
    Splits:
    - Train/Historical: Seasons <= 2024 (2022-2024)
    - Test/Future: Seasons >= 2025 (2025-2026)
    """
    if match_df.empty:
        return {"status": "EMPTY_DATA"}

    df = match_df.copy()
    df["season_num"] = pd.to_numeric(df["season"], errors="coerce")
    
    hist_mask = df["season_num"] <= 2024
    fut_mask = df["season_num"] >= 2025
    
    hist_matches = df[hist_mask]
    fut_matches = df[fut_mask]
    
    if hist_matches.empty or fut_matches.empty:
        return {"status": "INSUFFICIENT_SPLIT_DATA"}
        
    # Aggregate Historical Performance
    hist_summary = hist_matches.groupby(["player_id", "player_name"]).agg(
        hist_matches=("match_id", "nunique"),
        hist_balls=("hp_balls", "sum"),
        hist_overs=("hp_overs", "sum"),
        hist_runs_conceded=("hp_runs_conceded", "sum"),
        hist_runs_saved=("hp_runs_saved", "sum"),
        hist_wickets=("hp_wickets", "sum"),
        hist_wae=("hp_wae", "sum")
    ).reset_index()
    
    hist_summary["hist_rs_per_6"] = 6.0 * hist_summary["hist_runs_saved"] / np.maximum(hist_summary["hist_balls"], 1.0)
    hist_summary["hist_economy"] = 6.0 * hist_summary["hist_runs_conceded"] / np.maximum(hist_summary["hist_balls"], 1.0)
    hist_summary["hist_wae_per_6"] = 6.0 * hist_summary["hist_wae"] / np.maximum(hist_summary["hist_balls"], 1.0)

    # Simple Empirical Bayes shrinkage on historical data
    h_qual = (hist_summary["hist_overs"] >= min_eval_overs) & (hist_summary["hist_matches"] >= min_eval_matches)
    prior_mean = float(hist_summary.loc[h_qual, "hist_rs_per_6"].mean()) if h_qual.sum() >= 5 else 0.0
    tau2 = max(0.20, float(hist_summary.loc[h_qual, "hist_rs_per_6"].var(ddof=1)) * 0.45) if h_qual.sum() >= 5 else 0.80
    sigma2_i = 8.50 / np.maximum(hist_summary["hist_overs"], 0.20)
    b_i = sigma2_i / (tau2 + sigma2_i)
    hist_summary["hist_crai_rs_per_6"] = (1.0 - b_i) * hist_summary["hist_rs_per_6"] + b_i * prior_mean - 0.5 * np.sqrt(1.0 / (1.0 / tau2 + 1.0 / sigma2_i))

    # Aggregate Future Performance
    fut_summary = fut_matches.groupby(["player_id"]).agg(
        fut_matches=("match_id", "nunique"),
        fut_balls=("hp_balls", "sum"),
        fut_overs=("hp_overs", "sum"),
        fut_runs_conceded=("hp_runs_conceded", "sum"),
        fut_runs_saved=("hp_runs_saved", "sum"),
        fut_wickets=("hp_wickets", "sum"),
        fut_wae=("hp_wae", "sum")
    ).reset_index()
    
    fut_summary["fut_rs_per_6"] = 6.0 * fut_summary["fut_runs_saved"] / np.maximum(fut_summary["fut_balls"], 1.0)
    fut_summary["fut_economy"] = 6.0 * fut_summary["fut_runs_conceded"] / np.maximum(fut_summary["fut_balls"], 1.0)
    fut_summary["fut_wae_per_6"] = 6.0 * fut_summary["fut_wae"] / np.maximum(fut_summary["fut_balls"], 1.0)

    # Merge players active in both historical and future periods
    merged = hist_summary.merge(fut_summary, on="player_id", how="inner")
    
    # Filter to qualifying sample size in both periods
    eval_set = merged[
        (merged["hist_overs"] >= min_eval_overs) &
        (merged["fut_overs"] >= min_eval_overs) &
        (merged["hist_matches"] >= min_eval_matches) &
        (merged["fut_matches"] >= min_eval_matches)
    ].copy()
    
    n_eval = len(eval_set)
    if n_eval < 8:
        # Fallback to lower threshold if sample size is tight
        eval_set = merged[
            (merged["hist_overs"] >= 2.0) &
            (merged["fut_overs"] >= 2.0)
        ].copy()
        n_eval = len(eval_set)

    # 1. Runs Saved Prediction Correlations
    r_crai, p_crai = pearsonr(eval_set["hist_crai_rs_per_6"], eval_set["fut_rs_per_6"])
    spearman_crai, sp_pval = spearmanr(eval_set["hist_crai_rs_per_6"], eval_set["fut_rs_per_6"])
    kendall_crai, kp_pval = kendalltau(eval_set["hist_crai_rs_per_6"], eval_set["fut_rs_per_6"])
    
    # 2. Baseline Comparison: Raw Historical Economy Rate vs Future Runs Saved
    r_raw_econ, _ = pearsonr(-eval_set["hist_economy"], eval_set["fut_rs_per_6"])
    spearman_raw_econ, _ = spearmanr(-eval_set["hist_economy"], eval_set["fut_rs_per_6"])
    
    # 3. Baseline Comparison: Raw Historical Runs Saved vs Future Runs Saved
    r_raw_rs, _ = pearsonr(eval_set["hist_rs_per_6"], eval_set["fut_rs_per_6"])
    spearman_raw_rs, _ = spearmanr(eval_set["hist_rs_per_6"], eval_set["fut_rs_per_6"])

    # 4. Wickets Above Expected Correlations
    r_wae, _ = pearsonr(eval_set["hist_wae_per_6"], eval_set["fut_wae_per_6"])
    spearman_wae, _ = spearmanr(eval_set["hist_wae_per_6"], eval_set["fut_wae_per_6"])

    # 5. Top-Performer Stability: Precision@10 & Precision@20
    eval_set_sorted_hist = eval_set.sort_values(by="hist_crai_rs_per_6", ascending=False).reset_index(drop=True)
    eval_set_sorted_fut = eval_set.sort_values(by="fut_rs_per_6", ascending=False).reset_index(drop=True)
    
    top10_hist = set(eval_set_sorted_hist.head(10)["player_id"])
    top10_fut = set(eval_set_sorted_fut.head(10)["player_id"])
    precision_10 = len(top10_hist.intersection(top10_fut)) / 10.0 if n_eval >= 10 else np.nan
    
    top20_hist = set(eval_set_sorted_hist.head(20)["player_id"])
    top20_fut = set(eval_set_sorted_fut.head(20)["player_id"])
    precision_20 = len(top20_hist.intersection(top20_fut)) / 20.0 if n_eval >= 20 else np.nan

    return {
        "status": "VALIDATED",
        "sample_size": n_eval,
        "runs_saved_crai": {
            "pearson_r": float(r_crai),
            "p_value": float(p_crai),
            "spearman_rho": float(spearman_crai),
            "spearman_p": float(sp_pval),
            "kendall_tau": float(kendall_crai),
            "kendall_p": float(kp_pval)
        },
        "baselines_comparison": {
            "crai_shrunk_rs_rho": float(spearman_crai),
            "raw_rs_rho": float(spearman_raw_rs),
            "raw_economy_rho": float(spearman_raw_econ)
        },
        "wickets_above_expected": {
            "pearson_r": float(r_wae),
            "spearman_rho": float(spearman_wae)
        },
        "top_performer_stability": {
            "precision_at_10": float(precision_10) if not np.isnan(precision_10) else None,
            "precision_at_20": float(precision_20) if not np.isnan(precision_20) else None
        }
    }
