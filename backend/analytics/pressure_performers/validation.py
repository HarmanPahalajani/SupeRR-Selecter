"""
Enhanced Validation and Chronological Future Performance Evaluation Module
Part of SupeRR Intelligence — Pressure Performer Intelligence

Performs rolling chronological out-of-sample validation across transitions:
- Fold 1 (Validation): Train <= 2024 -> Test 2025
- Fold 2 (Holdout): Train <= 2025 -> Test 2026

Calculates:
1. Spearman rank correlation with Fisher z-transform 95% CIs.
2. Kendall tau correlation with asymptotic 95% CIs.
3. Future positive-contribution prevalence baseline.
4. Precision@10 and Precision@20 with lift over baseline.
5. Distribution of future pressure opportunities (balls and matches).
6. Separate IPL and T20I validation splits.
7. Separate Chase (Innings 2) and First-Innings (Innings 1) validation splits.
8. Future performance broken down by historical classification.
9. Threshold sensitivity on training/validation fold only.
"""

from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats

from backend.analytics.pressure_performers.pressure_opportunities import tag_high_pressure_deliveries
from backend.analytics.pressure_performers.contribution import compute_delivery_contributions
from backend.analytics.pressure_performers.match_aggregation import aggregate_player_matches
from backend.analytics.pressure_performers.reliability import compute_career_pressure_metrics
from backend.analytics.pressure_performers.classification import classify_dataframe
from backend.analytics.pressure_performers.ranking import compute_pressure_rankings


def compute_spearman_ci(r: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes Fisher z-transform 95% confidence interval for Spearman rho."""
    if n <= 3 or np.isnan(r) or abs(r) >= 1.0:
        return (float(r), float(r))
    z = np.arctanh(r)
    se_z = 1.0 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf((1.0 + confidence) / 2.0)
    z_low = z - z_crit * se_z
    z_high = z + z_crit * se_z
    return float(np.tanh(z_low)), float(np.tanh(z_high))


def compute_kendall_ci(tau: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes asymptotic 95% confidence interval for Kendall tau."""
    if n <= 3 or np.isnan(tau) or abs(tau) >= 1.0:
        return (float(tau), float(tau))
    se_tau = np.sqrt(2.0 * (2.0 * n + 5.0) / (9.0 * n * (n - 1.0)))
    z_crit = stats.norm.ppf((1.0 + confidence) / 2.0)
    return float(tau - z_crit * se_tau), float(tau + z_crit * se_tau)


def evaluate_future_fold_enhanced(
    df_deliveries: pd.DataFrame,
    train_end_season: int,
    test_season: int,
    threshold_variant: str = "p75",
    min_future_hp_balls: int = 15,
    format_filter: Optional[str] = None,
    innings_filter: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Evaluates a chronological fold with comprehensive uncertainty and baseline statistics.
    """
    # 1. Historical train split
    train_deliveries = df_deliveries[df_deliveries["season"] <= train_end_season].copy()
    test_deliveries = df_deliveries[df_deliveries["season"] == test_season].copy()
    
    if format_filter is not None:
        test_deliveries = test_deliveries[test_deliveries["format_scope"] == format_filter].copy()
    if innings_filter is not None:
        test_deliveries = test_deliveries[test_deliveries["innings"] == innings_filter].copy()
        
    train_tagged = tag_high_pressure_deliveries(train_deliveries, threshold_variant, is_primary=True)
    train_contrib = compute_delivery_contributions(train_tagged)
    train_hp = train_contrib[train_contrib["is_high_pressure"]].copy()
    
    if train_hp.empty:
        return {"error": f"No training pressure deliveries for <= {train_end_season}"}
        
    train_matches = aggregate_player_matches(train_hp)
    train_summary = train_deliveries.groupby("striker_id").agg(
        career_matches=("match_id", "nunique"),
        career_balls_faced=("is_legal_ball", "sum"),
        career_runs=("batter_runs", "sum")
    ).reset_index().rename(columns={"striker_id": "player_id"})
    
    train_metrics = compute_career_pressure_metrics(
        train_matches, career_summary_df=train_summary,
        min_eval_balls=20, min_eval_matches=3, n_bootstrap=200
    )
    train_classified = classify_dataframe(train_metrics, is_emerging=False)
    train_ranked = compute_pressure_rankings(train_classified)
    
    # 2. Test split
    test_tagged = tag_high_pressure_deliveries(test_deliveries, threshold_variant, is_primary=True)
    test_contrib = compute_delivery_contributions(test_tagged)
    test_hp = test_contrib[test_contrib["is_high_pressure"]].copy()
    
    if test_hp.empty:
        return {"error": f"No test pressure deliveries for {test_season}"}
        
    test_matches = aggregate_player_matches(test_hp)
    
    future_player = test_matches.groupby(["player_id", "player_name"]).agg(
        future_hp_matches=("match_id", "count"),
        future_hp_balls=("hp_balls", "sum"),
        future_hp_runs=("hp_runs", "sum"),
        future_hp_exp_runs=("hp_exp_runs", "sum"),
        future_hp_rae=("hp_rae", "sum"),
        future_hp_pos_matches=("is_positive_impact", "sum"),
        future_hp_neg_matches=("is_negative_impact", "sum")
    ).reset_index()
    
    future_player["future_hp_raw_rae_per_100"] = (
        100.0 * future_player["future_hp_rae"] / np.maximum(future_player["future_hp_balls"], 1.0)
    )
    future_player["future_hp_strike_rate"] = (
        100.0 * future_player["future_hp_runs"] / np.maximum(future_player["future_hp_balls"], 1.0)
    )
    future_player["future_hp_pos_match_pct"] = (
        100.0 * future_player["future_hp_pos_matches"] / future_player["future_hp_matches"]
    )
    
    merged = train_ranked.merge(future_player, on="player_id", how="inner", suffixes=("_hist", "_future"))
    eval_cohort = merged[merged["future_hp_balls"] >= min_future_hp_balls].copy()
    
    n_eval = len(eval_cohort)
    if n_eval < 5:
        return {
            "fold": f"{train_end_season} -> {test_season}",
            "evaluated_players": n_eval,
            "error": "Insufficient sample for reliable validation metrics"
        }
        
    hist_risk_adj = eval_cohort["hp_risk_adjusted_impact"].values if "hp_risk_adjusted_impact" in eval_cohort.columns else eval_cohort["hp_lcb"].values
    hist_post = eval_cohort["hp_posterior_mean"].values
    future_rae_100 = eval_cohort["future_hp_raw_rae_per_100"].values
    
    # 1. Rank Correlations & CIs
    spearman_val, p_spearman = stats.spearmanr(hist_risk_adj, future_rae_100)
    sp_low, sp_high = compute_spearman_ci(spearman_val, n_eval)
    
    kendall_val, p_kendall = stats.kendalltau(hist_risk_adj, future_rae_100)
    kd_low, kd_high = compute_kendall_ci(kendall_val, n_eval)
    
    # 2. Baseline Prevalence: Fraction of cohort with future positive RAE
    cohort_positive_prevalence = float((future_rae_100 > 0).mean())
    
    # 3. Precision@K vs Baseline Prevalence
    ranked_cohort = eval_cohort.sort_values(by="hp_risk_adjusted_impact" if "hp_risk_adjusted_impact" in eval_cohort.columns else "hp_lcb", ascending=False)
    p_at_10 = float((ranked_cohort.head(10)["future_hp_raw_rae_per_100"] > 0).mean()) if n_eval >= 10 else None
    p_at_20 = float((ranked_cohort.head(20)["future_hp_raw_rae_per_100"] > 0).mean()) if n_eval >= 20 else None
    
    lift_at_10 = float(p_at_10 - cohort_positive_prevalence) if p_at_10 is not None else None
    lift_at_20 = float(p_at_20 - cohort_positive_prevalence) if p_at_20 is not None else None
    
    # 4. Future opportunity distribution
    opp_summary = {
        "mean_future_hp_balls": float(eval_cohort["future_hp_balls"].mean()),
        "median_future_hp_balls": float(eval_cohort["future_hp_balls"].median()),
        "min_future_hp_balls": float(eval_cohort["future_hp_balls"].min()),
        "max_future_hp_balls": float(eval_cohort["future_hp_balls"].max()),
        "mean_future_hp_matches": float(eval_cohort["future_hp_matches"].mean()),
        "total_future_hp_balls": float(eval_cohort["future_hp_balls"].sum()),
    }
    
    # 5. Future performance by historical classification
    class_perf = {}
    for cls_name, grp in eval_cohort.groupby("classification"):
        class_perf[cls_name] = {
            "player_count": len(grp),
            "mean_future_rae_per_100": float(grp["future_hp_raw_rae_per_100"].mean()),
            "median_future_rae_per_100": float(grp["future_hp_raw_rae_per_100"].median()),
            "mean_future_pos_match_pct": float(grp["future_hp_pos_match_pct"].mean()),
            "future_positive_rate": float((grp["future_hp_raw_rae_per_100"] > 0).mean()),
        }
        
    return {
        "fold": f"{train_end_season} -> {test_season}",
        "train_end_season": train_end_season,
        "test_season": test_season,
        "format_filter": format_filter or "COMBINED",
        "innings_filter": "CHASE" if innings_filter == 2 else ("FIRST_INNINGS" if innings_filter == 1 else "COMBINED"),
        "evaluated_players": n_eval,
        "spearman": {
            "rho": float(spearman_val),
            "p_value": float(p_spearman),
            "ci_95": [sp_low, sp_high]
        },
        "kendall": {
            "tau": float(kendall_val),
            "p_value": float(p_kendall),
            "ci_95": [kd_low, kd_high]
        },
        "baseline_positive_prevalence": cohort_positive_prevalence,
        "precision_at_10": p_at_10,
        "lift_at_10": lift_at_10,
        "precision_at_20": p_at_20,
        "lift_at_20": lift_at_20,
        "future_opportunity_distribution": opp_summary,
        "class_performance": class_perf,
    }


def run_comprehensive_validation(df_deliveries: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes full multi-fold, multi-format, multi-innings chronological validation.
    """
    print("Executing Fold 1 (Validation): Train <= 2024 -> Test 2025...")
    fold_2025_all = evaluate_future_fold_enhanced(df_deliveries, 2024, 2025)
    fold_2025_ipl = evaluate_future_fold_enhanced(df_deliveries, 2024, 2025, format_filter="IPL")
    fold_2025_t20i = evaluate_future_fold_enhanced(df_deliveries, 2024, 2025, format_filter="T20I")
    fold_2025_chase = evaluate_future_fold_enhanced(df_deliveries, 2024, 2025, innings_filter=2)
    fold_2025_inn1 = evaluate_future_fold_enhanced(df_deliveries, 2024, 2025, innings_filter=1)
    
    print("Executing Fold 2 (Holdout): Train <= 2025 -> Test 2026...")
    fold_2026_all = evaluate_future_fold_enhanced(df_deliveries, 2025, 2026)
    fold_2026_chase = evaluate_future_fold_enhanced(df_deliveries, 2025, 2026, innings_filter=2)
    fold_2026_inn1 = evaluate_future_fold_enhanced(df_deliveries, 2025, 2026, innings_filter=1)
    
    print("Executing Threshold Sensitivity on Validation Fold (2024 -> 2025)...")
    threshold_sensitivity = {}
    for var in ["p70", "p75", "p80", "p85"]:
        threshold_sensitivity[var] = evaluate_future_fold_enhanced(
            df_deliveries, 2024, 2025, threshold_variant=var
        )
        
    return {
        "validation_fold_2025": {
            "all_primary": fold_2025_all,
            "ipl_only": fold_2025_ipl,
            "t20i_only": fold_2025_t20i,
            "chase_only": fold_2025_chase,
            "first_innings_only": fold_2025_inn1,
        },
        "holdout_fold_2026": {
            "all_primary": fold_2026_all,
            "chase_only": fold_2026_chase,
            "first_innings_only": fold_2026_inn1,
        },
        "threshold_selection_tradeoff": threshold_sensitivity,
    }
