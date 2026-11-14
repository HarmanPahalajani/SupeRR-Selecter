"""
Reliability and Empirical Bayes Estimation Module
Part of SupeRR Intelligence — Pressure Performer Intelligence

Estimates shrinkage-adjusted posterior pressure impact and match-clustered
bootstrap confidence intervals for every batter.
"""

from typing import Dict, Tuple, List, Optional
import pandas as pd
import numpy as np


def compute_match_bootstrap_ci(
    match_raes: np.ndarray,
    match_balls: np.ndarray,
    n_resamples: int = 1000,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Computes non-parametric 95% confidence interval via match-clustered bootstrap.
    Resamples entire matches with replacement, preserving within-match correlation.
    """
    n = len(match_raes)
    if n < 3:
        raw = 100.0 * np.sum(match_raes) / max(np.sum(match_balls), 1)
        return float(raw - 25.0), float(raw + 25.0)
        
    rng = np.random.RandomState(seed)
    indices = rng.randint(0, n, size=(n_resamples, n))
    resampled_raes = np.take(match_raes, indices)
    resampled_balls = np.take(match_balls, indices)
    
    sum_raes = np.sum(resampled_raes, axis=1)
    sum_balls = np.maximum(np.sum(resampled_balls, axis=1), 1)
    estimates = 100.0 * sum_raes / sum_balls
    
    ci_low = float(np.percentile(estimates, 2.5))
    ci_high = float(np.percentile(estimates, 97.5))
    return ci_low, ci_high


def compute_career_pressure_metrics(
    match_df: pd.DataFrame,
    career_summary_df: Optional[pd.DataFrame] = None,
    min_eval_balls: int = 20,
    min_eval_matches: int = 3,
    n_bootstrap: int = 1000,
    seed: int = 42
) -> pd.DataFrame:
    """
    Computes career-level pressure metrics, Empirical Bayes shrinkage, and CIs.
    """
    if match_df.empty:
        return pd.DataFrame()
        
    # Group by player
    records = []
    for (pid, pname), group in match_df.groupby(["player_id", "player_name"]):
        m_count = len(group)
        balls = float(group["hp_balls"].sum())
        runs = float(group["hp_runs"].sum())
        exp_runs = float(group["hp_exp_runs"].sum())
        rae = float(group["hp_rae"].sum())
        dismissals = float(group["hp_striker_dismissals"].sum())
        exp_wickets = float(group["hp_exp_wickets"].sum())
        boundaries = float(group["hp_boundaries"].sum())
        sixes = float(group["hp_sixes"].sum())
        dots = float(group["hp_dots"].sum())
        
        pos_m = int(group["is_positive_impact"].sum())
        neg_m = int(group["is_negative_impact"].sum())
        neutral_m = int(group["is_neutral_impact"].sum())
        
        raw_rae_per_100 = 100.0 * rae / max(balls, 1.0)
        pos_match_pct = 100.0 * pos_m / m_count
        neg_match_pct = 100.0 * neg_m / m_count
        
        # Match distribution statistics
        match_raes = group["hp_rae"].values
        match_balls = group["hp_balls"].values
        mean_match_rae = float(np.mean(match_raes))
        median_match_rae = float(np.median(match_raes))
        std_match_rae = float(np.std(match_raes, ddof=1)) if m_count > 1 else 0.0
        max_single_match_rae = float(np.max(match_raes))
        
        # Corrected Single Match Concentration: Max Positive Match RAE / Sum of Positive Match RAE
        pos_raes = match_raes[match_raes > 0]
        if len(pos_raes) > 0:
            sum_pos_rae = float(np.sum(pos_raes))
            max_pos_rae = float(np.max(pos_raes))
            pos_match_share = float(max_pos_rae / sum_pos_rae) if sum_pos_rae > 0 else np.nan
        else:
            pos_match_share = np.nan
            
        neg_raes = match_raes[match_raes < 0]
        sum_neg_rae = float(np.sum(neg_raes)) if len(neg_raes) > 0 else 0.0
        worst_single_match_rae = float(np.min(match_raes)) if len(match_raes) > 0 else 0.0
            
        # Bootstrap CI
        ci_low, ci_high = compute_match_bootstrap_ci(
            match_raes, match_balls, n_resamples=n_bootstrap, seed=seed + int(pid) % 1000
        )
        
        records.append({
            "player_id": pid,
            "player_name": pname,
            "hp_matches": m_count,
            "hp_balls": balls,
            "hp_runs": runs,
            "hp_exp_runs": exp_runs,
            "hp_rae": rae,
            "hp_raw_rae_per_100": raw_rae_per_100,
            "hp_positive_matches": pos_m,
            "hp_negative_matches": neg_m,
            "hp_neutral_matches": neutral_m,
            "hp_positive_match_pct": pos_match_pct,
            "hp_negative_match_pct": neg_match_pct,
            "hp_mean_match_rae": mean_match_rae,
            "hp_median_match_rae": median_match_rae,
            "hp_std_match_rae": std_match_rae,
            "hp_max_single_match_rae": max_single_match_rae,
            "hp_positive_match_share": pos_match_share,
            "hp_single_match_share": pos_match_share if not np.isnan(pos_match_share) else 0.0,
            "hp_sum_negative_rae": sum_neg_rae,
            "hp_worst_single_match_rae": worst_single_match_rae,
            "hp_dismissals": dismissals,
            "hp_exp_wickets": exp_wickets,
            "hp_dismissal_rate": dismissals / max(balls, 1.0),
            "hp_boundary_pct": 100.0 * boundaries / max(balls, 1.0),
            "hp_six_pct": 100.0 * sixes / max(balls, 1.0),
            "hp_dot_pct": 100.0 * dots / max(balls, 1.0),
            "hp_strike_rate": 100.0 * runs / max(balls, 1.0),
            "hp_ci_low": ci_low,
            "hp_ci_high": ci_high,
            "hp_ci_width": ci_high - ci_low,
        })
        
    res_df = pd.DataFrame(records)
    
    # Empirical Bayes Normal-Normal Shrinkage
    # Baseline prior from qualified players (>= min_eval_balls and >= min_eval_matches)
    qual_mask = (res_df["hp_balls"] >= min_eval_balls) & (res_df["hp_matches"] >= min_eval_matches)
    if qual_mask.sum() >= 10:
        prior_mean = float(res_df.loc[qual_mask, "hp_raw_rae_per_100"].mean())
        raw_var = float(res_df.loc[qual_mask, "hp_raw_rae_per_100"].var(ddof=1))
    else:
        prior_mean = 0.0
        raw_var = 150.0
        
    # Between-player variance tau^2
    tau2 = max(10.0, raw_var * 0.40)
    
    # Within-player sampling variance sigma_i^2 based on effective balls faced
    # Base delivery variance roughly 1.3^2 * 100^2 / balls
    base_sigma2 = 18000.0
    sigma2_i = base_sigma2 / np.maximum(res_df["hp_balls"], 1.0)
    
    shrinkage_factor = sigma2_i / (tau2 + sigma2_i)
    posterior_mean = (1.0 - shrinkage_factor) * res_df["hp_raw_rae_per_100"] + shrinkage_factor * prior_mean
    posterior_se = np.sqrt(1.0 / (1.0 / tau2 + 1.0 / sigma2_i))
    
    res_df["hp_eb_prior_mean"] = prior_mean
    res_df["hp_eb_shrinkage"] = shrinkage_factor
    res_df["hp_posterior_mean"] = posterior_mean
    res_df["hp_posterior_se"] = posterior_se
    
    # Risk-Adjusted Impact (CRAI: Conservative half-sigma penalty, ~31st posterior percentile)
    res_df["hp_risk_adjusted_impact"] = posterior_mean - 0.5 * posterior_se
    res_df["hp_lcb"] = res_df["hp_risk_adjusted_impact"]  # backward-compatible alias
    res_df["hp_ucb"] = posterior_mean + 0.5 * posterior_se
    
    # Formal 95% One-Sided Bounds (Z = 1.645)
    res_df["hp_lcb_95"] = posterior_mean - 1.645 * posterior_se
    res_df["hp_ucb_95"] = posterior_mean + 1.645 * posterior_se
    
    # Merge career exposure information if provided
    if career_summary_df is not None:
        res_df = res_df.merge(career_summary_df, on="player_id", how="left")
        
    return res_df
