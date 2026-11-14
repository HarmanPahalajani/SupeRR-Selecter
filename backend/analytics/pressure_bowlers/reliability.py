"""
Reliability and Empirical Bayes Estimation Module for Bowlers
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Estimates shrinkage-adjusted posterior pressure impact and match-clustered
bootstrap confidence intervals for every bowler.
"""

from typing import Dict, Tuple, List, Optional
import pandas as pd
import numpy as np


def compute_bowler_match_bootstrap_ci(
    match_runs_saved: np.ndarray,
    match_balls: np.ndarray,
    n_resamples: int = 1000,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Computes non-parametric 95% confidence interval via match-clustered bootstrap
    for runs saved per 6 legal balls.
    Resamples entire matches with replacement, preserving within-match correlation.
    """
    n = len(match_runs_saved)
    if n < 3:
        raw_per_6 = 6.0 * np.sum(match_runs_saved) / max(np.sum(match_balls), 1)
        return float(raw_per_6 - 2.5), float(raw_per_6 + 2.5)
        
    rng = np.random.RandomState(seed)
    indices = rng.randint(0, n, size=(n_resamples, n))
    resampled_rs = np.take(match_runs_saved, indices)
    resampled_balls = np.take(match_balls, indices)
    
    sum_rs = np.sum(resampled_rs, axis=1)
    sum_balls = np.maximum(np.sum(resampled_balls, axis=1), 1)
    estimates = 6.0 * sum_rs / sum_balls
    
    ci_low = float(np.percentile(estimates, 2.5))
    ci_high = float(np.percentile(estimates, 97.5))
    return ci_low, ci_high


def compute_career_bowler_pressure_metrics(
    match_df: pd.DataFrame,
    career_summary_df: Optional[pd.DataFrame] = None,
    min_eval_overs: float = 4.0,
    min_eval_matches: int = 3,
    n_bootstrap: int = 1000,
    seed: int = 42
) -> pd.DataFrame:
    """
    Computes career-level pressure metrics, Empirical Bayes shrinkage, and CIs for bowlers.
    """
    if match_df.empty:
        return pd.DataFrame()
        
    records = []
    for (pid, pname), group in match_df.groupby(["player_id", "player_name"]):
        m_count = len(group)
        balls = float(group["hp_balls"].sum())
        overs = balls / 6.0
        runs_conceded = float(group["hp_runs_conceded"].sum())
        exp_runs_conceded = float(group["hp_exp_runs_conceded"].sum())
        runs_saved = float(group["hp_runs_saved"].sum())
        
        wickets = float(group["hp_wickets"].sum())
        exp_wickets = float(group["hp_exp_wickets"].sum())
        wae = float(group["hp_wae"].sum())
        
        dots = float(group["hp_dots"].sum())
        boundaries = float(group["hp_boundaries_conceded"].sum())
        sixes = float(group["hp_sixes_conceded"].sum())
        pace_or_spin = group["pace_or_spin"].dropna().iloc[0] if "pace_or_spin" in group.columns and len(group["pace_or_spin"].dropna()) > 0 else "UNKNOWN"
        
        pos_m = int(group["is_positive_impact"].sum())
        neg_m = int(group["is_negative_impact"].sum())
        neutral_m = int(group["is_neutral_impact"].sum())
        
        raw_rs_per_6 = 6.0 * runs_saved / max(balls, 1.0)
        raw_rs_per_100 = 100.0 * runs_saved / max(balls, 1.0)
        economy_rate = 6.0 * runs_conceded / max(balls, 1.0) if balls > 0 else np.nan
        
        pos_match_pct = 100.0 * pos_m / m_count
        neg_match_pct = 100.0 * neg_m / m_count
        
        # Match distribution statistics
        match_rs = group["hp_runs_saved"].values
        match_balls = group["hp_balls"].values
        mean_match_rs = float(np.mean(match_rs))
        median_match_rs = float(np.median(match_rs))
        std_match_rs = float(np.std(match_rs, ddof=1)) if m_count > 1 else 0.0
        max_single_match_rs = float(np.max(match_rs))
        worst_single_match_rs = float(np.min(match_rs)) if len(match_rs) > 0 else 0.0
        
        # Single Match Concentration: Max Positive Match RS / Sum of Positive Match RS
        pos_rs = match_rs[match_rs > 0]
        if len(pos_rs) > 0:
            sum_pos_rs = float(np.sum(pos_rs))
            max_pos_rs = float(np.max(pos_rs))
            pos_match_share = float(max_pos_rs / sum_pos_rs) if sum_pos_rs > 0 else np.nan
        else:
            pos_match_share = np.nan
            
        neg_rs = match_rs[match_rs < 0]
        sum_neg_rs = float(np.sum(neg_rs)) if len(neg_rs) > 0 else 0.0

        # WAE per 6 and per 100 balls
        wae_per_6 = 6.0 * wae / max(balls, 1.0)
        wae_per_100 = 100.0 * wae / max(balls, 1.0)
            
        # Bootstrap CI on runs saved per 6 balls
        ci_low, ci_high = compute_bowler_match_bootstrap_ci(
            match_rs, match_balls, n_resamples=n_bootstrap, seed=seed + int(pid) % 1000
        )
        
        records.append({
            "player_id": pid,
            "player_name": pname,
            "pace_or_spin": pace_or_spin,
            "hp_matches": m_count,
            "hp_balls": balls,
            "hp_overs": overs,
            "hp_runs_conceded": runs_conceded,
            "hp_exp_runs_conceded": exp_runs_conceded,
            "hp_runs_saved": runs_saved,
            "hp_raw_runs_saved_per_6": raw_rs_per_6,
            "hp_raw_runs_saved_per_100": raw_rs_per_100,
            "hp_economy_rate": economy_rate,
            "hp_wickets": wickets,
            "hp_exp_wickets": exp_wickets,
            "hp_wae": wae,
            "hp_wae_per_6": wae_per_6,
            "hp_wae_per_100": wae_per_100,
            "hp_positive_matches": pos_m,
            "hp_negative_matches": neg_m,
            "hp_neutral_matches": neutral_m,
            "hp_positive_match_pct": pos_match_pct,
            "hp_negative_match_pct": neg_match_pct,
            "hp_mean_match_runs_saved": mean_match_rs,
            "hp_median_match_runs_saved": median_match_rs,
            "hp_std_match_runs_saved": std_match_rs,
            "hp_max_single_match_runs_saved": max_single_match_rs,
            "hp_positive_match_share": pos_match_share,
            "hp_single_match_share": pos_match_share if not np.isnan(pos_match_share) else 0.0,
            "hp_sum_negative_runs_saved": sum_neg_rs,
            "hp_worst_single_match_runs_saved": worst_single_match_rs,
            "hp_dots": dots,
            "hp_boundaries_conceded": boundaries,
            "hp_sixes_conceded": sixes,
            "hp_dot_pct": 100.0 * dots / max(balls, 1.0),
            "hp_boundary_pct": 100.0 * boundaries / max(balls, 1.0),
            "hp_six_pct": 100.0 * sixes / max(balls, 1.0),
            "hp_ci_low": ci_low,
            "hp_ci_high": ci_high,
            "hp_ci_width": ci_high - ci_low,
        })
        
    res_df = pd.DataFrame(records)
    
    # Empirical Bayes Normal-Normal Shrinkage for Runs Saved Per 6 Balls
    qual_mask = (res_df["hp_overs"] >= min_eval_overs) & (res_df["hp_matches"] >= min_eval_matches)
    if qual_mask.sum() >= 10:
        prior_mean = float(res_df.loc[qual_mask, "hp_raw_runs_saved_per_6"].mean())
        raw_var = float(res_df.loc[qual_mask, "hp_raw_runs_saved_per_6"].var(ddof=1))
    else:
        prior_mean = 0.0
        raw_var = 1.80
        
    # Between-bowler variance tau^2
    tau2 = max(0.20, raw_var * 0.45)
    
    # Within-bowler sampling variance sigma_i^2 based on effective overs bowled
    # In T20, per-over variance is approximately 3.2^2 / overs
    base_sigma2 = 8.50
    sigma2_i = base_sigma2 / np.maximum(res_df["hp_overs"], 0.20)
    
    shrinkage_factor = sigma2_i / (tau2 + sigma2_i)
    posterior_mean = (1.0 - shrinkage_factor) * res_df["hp_raw_runs_saved_per_6"] + shrinkage_factor * prior_mean
    posterior_se = np.sqrt(1.0 / (1.0 / tau2 + 1.0 / sigma2_i))
    
    res_df["hp_eb_prior_mean"] = prior_mean
    res_df["hp_eb_shrinkage"] = shrinkage_factor
    res_df["hp_posterior_mean"] = posterior_mean
    res_df["hp_posterior_se"] = posterior_se
    
    # Risk-Adjusted Impact (CRAI: Conservative half-sigma penalty, ~31st posterior percentile)
    res_df["hp_risk_adjusted_impact"] = posterior_mean - 0.5 * posterior_se
    res_df["hp_lcb"] = res_df["hp_risk_adjusted_impact"]
    res_df["hp_ucb"] = posterior_mean + 0.5 * posterior_se
    
    # Formal 95% One-Sided Bounds (Z = 1.645)
    res_df["hp_lcb_95"] = posterior_mean - 1.645 * posterior_se
    res_df["hp_ucb_95"] = posterior_mean + 1.645 * posterior_se
    
    # Empirical Bayes for Wickets Above Expected per 6 balls
    if qual_mask.sum() >= 10:
        wae_prior_mean = float(res_df.loc[qual_mask, "hp_wae_per_6"].mean())
        wae_raw_var = float(res_df.loc[qual_mask, "hp_wae_per_6"].var(ddof=1))
    else:
        wae_prior_mean = 0.0
        wae_raw_var = 0.08
        
    wae_tau2 = max(0.01, wae_raw_var * 0.40)
    wae_sigma2_i = 0.35 / np.maximum(res_df["hp_overs"], 0.20)
    wae_shrinkage = wae_sigma2_i / (wae_tau2 + wae_sigma2_i)
    wae_post_mean = (1.0 - wae_shrinkage) * res_df["hp_wae_per_6"] + wae_shrinkage * wae_prior_mean
    wae_post_se = np.sqrt(1.0 / (1.0 / wae_tau2 + 1.0 / wae_sigma2_i))
    
    res_df["hp_wae_posterior_mean"] = wae_post_mean
    res_df["hp_wae_posterior_se"] = wae_post_se
    res_df["hp_wae_crai"] = wae_post_mean - 0.5 * wae_post_se
    
    # Merge career summary if provided
    if career_summary_df is not None:
        res_df = res_df.merge(career_summary_df, on="player_id", how="left")
        
    return res_df
