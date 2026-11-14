"""
Authoritative Player Rating and Evidence-Based Ranking Engine for SupeRR Intelligence.

Implements:
1. Strict independence of batting and bowling evidence.
2. Discipline-specific sample size requirements and confidence tiers.
3. Rigorous Empirical Bayes shrinkage with per-discipline priors.
4. Conservative Lower Confidence Bound (LCB) ranking score.
5. Strict ranking eligibility (ineligible / uncertain players never receive an official rank).
6. Full population reconciliation across all 1,217 players.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

def compute_evidence_based_ratings(
    proc_path: Path = Path("data/processed"),
    p11_raw_path: Path = Path("data/raw/playing_eleven.csv")
) -> pd.DataFrame:
    print("Loading data for evidence-based rating calculation...")
    df_raw = pd.read_parquet(proc_path / "fact_delivery_scored.parquet")
    # Strict Scope Isolation: IPL & T20I only, Super Overs strictly excluded
    df = df_raw[(df_raw['is_primary_scope'] == True) & (df_raw['is_super_over'] == False)].copy()
    dim_player = pd.read_parquet(proc_path / "dim_player.parquet")
    dim_match = pd.read_parquet(proc_path / "dim_match.parquet")
    df_canonical = pd.read_parquet(proc_path / "fact_delivery_canonical.parquet")

    # High pressure delivery definition (>= 7.0 situational pressure index)
    df['is_high_pressure'] = df['pressure_index'] >= 7.0
    df['is_dot'] = (df['batter_runs'] == 0) & (df['extras_wide_runs'] == 0) & (df['extras_noball_runs'] == 0)
    df['is_boundary'] = df['batter_runs'].isin([4, 6])

    print("Aggregating match-level batting metrics...")
    match_bat = df.groupby(['striker_id', 'match_id', 'format_scope']).agg(
        balls_faced=('is_legal_ball', 'sum'),
        runs=('batter_runs', 'sum'),
        fours=('is_four', 'sum'),
        sixes=('is_six', 'sum'),
        dismissals=('is_wicket', 'sum'),
        rae=('rae', 'sum'),
        pressure_balls=('is_high_pressure', 'sum'),
        pressure_runs=('batter_runs', lambda s: s[df.loc[s.index, 'is_high_pressure']].sum()),
        pressure_weighted_rae=('pressure_weighted_rae', 'sum'),
        pressure_dots=('is_dot', lambda s: s[df.loc[s.index, 'is_high_pressure']].sum())
    ).reset_index().rename(columns={'striker_id': 'player_id'})

    bat_agg = match_bat.groupby('player_id').agg(
        matches_batted=('match_id', 'nunique'),
        balls_faced=('balls_faced', 'sum'),
        total_runs=('runs', 'sum'),
        fours=('fours', 'sum'),
        sixes=('sixes', 'sum'),
        dismissals=('dismissals', 'sum'),
        total_rae=('rae', 'sum'),
        pressure_balls_faced=('pressure_balls', 'sum'),
        pressure_runs=('pressure_runs', 'sum'),
        pressure_weighted_rae=('pressure_weighted_rae', 'sum'),
        pressure_dots=('pressure_dots', 'sum')
    ).reset_index()

    bat_agg['batting_sr'] = np.where(bat_agg['balls_faced'] > 0, (bat_agg['total_runs'] / bat_agg['balls_faced']) * 100.0, np.nan)
    bat_agg['batting_avg'] = np.where(bat_agg['dismissals'] > 0, bat_agg['total_runs'] / bat_agg['dismissals'], np.nan)
    bat_agg['rae_per_ball'] = np.where(bat_agg['balls_faced'] > 0, bat_agg['total_rae'] / bat_agg['balls_faced'], np.nan)
    bat_agg['pressure_rae_per_ball'] = np.where(bat_agg['pressure_balls_faced'] > 0, bat_agg['pressure_weighted_rae'] / bat_agg['pressure_balls_faced'], np.nan)
    bat_agg['pressure_dot_pct'] = np.where(bat_agg['pressure_balls_faced'] > 0, (bat_agg['pressure_dots'] / bat_agg['pressure_balls_faced']) * 100.0, np.nan)

    print("Aggregating match-level bowling metrics...")
    match_bowl = df.groupby(['bowler_id', 'match_id', 'format_scope']).agg(
        legal_balls=('is_legal_ball', 'sum'),
        runs_conceded=('bowler_conceded_runs', 'sum'),
        bowler_wickets=('is_bowler_wicket', 'sum'),
        runs_saved=('runs_saved', 'sum'),
        wae=('wae', 'sum'),
        pressure_balls=('is_high_pressure', 'sum'),
        pressure_runs_conceded=('bowler_conceded_runs', lambda s: s[df.loc[s.index, 'is_high_pressure']].sum()),
        pressure_weighted_runs_saved=('pressure_weighted_runs_saved', 'sum'),
        pressure_weighted_wae=('pressure_weighted_wae', 'sum'),
        dots_bowled=('is_dot', 'sum')
    ).reset_index().rename(columns={'bowler_id': 'player_id'})

    bowl_agg = match_bowl.groupby('player_id').agg(
        matches_bowled=('match_id', 'nunique'),
        legal_balls_bowled=('legal_balls', 'sum'),
        runs_conceded=('runs_conceded', 'sum'),
        bowler_wickets=('bowler_wickets', 'sum'),
        total_runs_saved=('runs_saved', 'sum'),
        total_wae=('wae', 'sum'),
        pressure_balls_bowled=('pressure_balls', 'sum'),
        pressure_runs_conceded=('pressure_runs_conceded', 'sum'),
        pressure_weighted_runs_saved=('pressure_weighted_runs_saved', 'sum'),
        pressure_weighted_wae=('pressure_weighted_wae', 'sum'),
        dots_bowled=('dots_bowled', 'sum')
    ).reset_index()

    bowl_agg['overs_bowled'] = bowl_agg['legal_balls_bowled'] / 6.0
    bowl_agg['bowling_econ'] = np.where(bowl_agg['legal_balls_bowled'] > 0, (bowl_agg['runs_conceded'] * 6.0) / bowl_agg['legal_balls_bowled'], np.nan)
    bowl_agg['bowling_sr'] = np.where(bowl_agg['bowler_wickets'] > 0, bowl_agg['legal_balls_bowled'] / bowl_agg['bowler_wickets'], np.nan)
    bowl_agg['bowling_avg'] = np.where(bowl_agg['bowler_wickets'] > 0, bowl_agg['runs_conceded'] / bowl_agg['bowler_wickets'], np.nan)
    bowl_agg['runs_saved_per_ball'] = np.where(bowl_agg['legal_balls_bowled'] > 0, bowl_agg['total_runs_saved'] / bowl_agg['legal_balls_bowled'], np.nan)
    bowl_agg['pressure_runs_saved_per_ball'] = np.where(bowl_agg['pressure_balls_bowled'] > 0, bowl_agg['pressure_weighted_runs_saved'] / bowl_agg['pressure_balls_bowled'], np.nan)

    print("Merging player dimensions...")
    metrics = dim_player.merge(bat_agg, on='player_id', how='left')
    metrics = metrics.merge(bowl_agg, on='player_id', how='left')

    # Strict volume vs rate missing-value semantics:
    # Volume counts fill with 0 for players without match activity in the discipline.
    bat_count_cols = [
        'matches_batted', 'balls_faced', 'total_runs', 'fours', 'sixes', 'dismissals',
        'total_rae', 'pressure_balls_faced', 'pressure_runs', 'pressure_weighted_rae', 'pressure_dots'
    ]
    for col in bat_count_cols:
        if col in metrics.columns:
            metrics[col] = metrics[col].fillna(0)

    bowl_count_cols = [
        'matches_bowled', 'legal_balls_bowled', 'runs_conceded', 'bowler_wickets',
        'total_runs_saved', 'total_wae', 'pressure_balls_bowled', 'pressure_runs_conceded',
        'pressure_weighted_runs_saved', 'pressure_weighted_wae', 'dots_bowled', 'overs_bowled'
    ]
    for col in bowl_count_cols:
        if col in metrics.columns:
            metrics[col] = metrics[col].fillna(0)

    # Note: Rates and averages (batting_sr, batting_avg, bowling_econ, bowling_sr, bowling_avg,
    # rae_per_ball, runs_saved_per_ball) remain NaN / None when sample or denominator is 0.

    # Classify Authoritative Roles
    from backend.analytics.ranking.roles import classify_player_roles
    p11_raw = pd.read_csv(p11_raw_path)
    metrics = classify_player_roles(metrics, p11_raw, dim_match, df_canonical)
    metrics['total_matches'] = metrics['effective_matches']

    # Phase allocations
    death_balls = df[df['phase'] == 'death'].groupby('bowler_id')['is_legal_ball'].sum()
    pp_balls = df[df['phase'] == 'powerplay'].groupby('bowler_id')['is_legal_ball'].sum()
    metrics['death_overs_bowled'] = (metrics['player_id'].map(death_balls).fillna(0) / 6.0).round(1)
    metrics['pp_overs_bowled'] = (metrics['player_id'].map(pp_balls).fillna(0) / 6.0).round(1)

    # =========================================================================
    # PHASE 4: INDEPENDENT EMPIRICAL BAYES & CONFIDENCE TIERS
    # =========================================================================
    print("Computing discipline-specific Empirical Bayes shrinkage and confidence tiers...")

    # A. BATTING DISCIPLINE
    # Evidence thresholds:
    # HIGH: balls_faced >= 180, matches_batted >= 12, pressure_balls_faced >= 40
    # MEDIUM: balls_faced >= 60, matches_batted >= 5, pressure_balls_faced >= 15
    # LIMITED: balls_faced >= 10, matches_batted >= 2
    # INSUFFICIENT: otherwise
    bat_high = (metrics['balls_faced'] >= 180) & (metrics['matches_batted'] >= 12) & (metrics['pressure_balls_faced'] >= 40)
    bat_med = ((metrics['balls_faced'] >= 60) & (metrics['matches_batted'] >= 5) & (metrics['pressure_balls_faced'] >= 15)) & ~bat_high
    bat_lim = ((metrics['balls_faced'] >= 10) & (metrics['matches_batted'] >= 2)) & ~(bat_high | bat_med)
    
    bat_qual = bat_high | bat_med
    
    metrics['batting_sample_size'] = metrics['balls_faced'].astype(int)
    metrics['batting_ranking_eligible'] = bat_qual
    metrics['batting_confidence_tier'] = np.select(
        [bat_high, bat_med, bat_lim],
        ['HIGH', 'MEDIUM', 'LIMITED_EVIDENCE'],
        default='INSUFFICIENT_DATA'
    )
    metrics['batting_rating_status'] = np.select(
        [bat_qual, bat_lim],
        ['RATED', 'LIMITED_EVIDENCE'],
        default='UNRATED_INSUFFICIENT_DATA'
    )

    # Batting Empirical Bayes Prior derived from qualified batters
    mu_bat = metrics.loc[bat_qual, 'pressure_rae_per_ball'].mean()
    tau2_bat = max(0.01, metrics.loc[bat_qual, 'pressure_rae_per_ball'].var())
    
    v_bat = 1.2
    n_bat = np.maximum(metrics['pressure_balls_faced'].values, 1)
    sigma2_bat = v_bat / n_bat
    b_bat = sigma2_bat / (tau2_bat + sigma2_bat)
    shrunk_bat = (1.0 - b_bat) * metrics['pressure_rae_per_ball'].values + b_bat * mu_bat
    unc_bat = np.sqrt(1.0 / (1.0/tau2_bat + 1.0/sigma2_bat))

    # Players with zero pressure balls faced have pure prior mean and maximum uncertainty
    no_bat_mask = metrics['pressure_balls_faced'] == 0
    shrunk_bat[no_bat_mask] = mu_bat
    unc_bat[no_bat_mask] = np.sqrt(tau2_bat)

    metrics['eb_batting_impact'] = shrunk_bat
    metrics['batting_uncertainty'] = unc_bat
    
    # Conservative Lower Confidence Bound ranking score
    metrics['batting_ranking_score'] = np.where(
        bat_qual,
        shrunk_bat - 0.5 * unc_bat,
        np.nan
    )
    
    # Batting Rating: 15.0 to 99.0 scale, ONLY for eligible players
    metrics['batting_rating'] = np.where(
        bat_qual,
        np.clip(50.0 + shrunk_bat * 35.0, 15.0, 99.0).round(1),
        np.nan
    )
    metrics['overall_batting_rating'] = metrics['batting_rating']

    # B. BOWLING DISCIPLINE
    # Evidence thresholds:
    # HIGH: legal_balls_bowled >= 180, matches_bowled >= 12, pressure_balls_bowled >= 40
    # MEDIUM: legal_balls_bowled >= 60, matches_bowled >= 5, pressure_balls_bowled >= 15
    # LIMITED: legal_balls_bowled >= 12, matches_bowled >= 2
    # INSUFFICIENT: otherwise
    bowl_high = (metrics['legal_balls_bowled'] >= 180) & (metrics['matches_bowled'] >= 12) & (metrics['pressure_balls_bowled'] >= 40)
    bowl_med = ((metrics['legal_balls_bowled'] >= 60) & (metrics['matches_bowled'] >= 5) & (metrics['pressure_balls_bowled'] >= 15)) & ~bowl_high
    bowl_lim = ((metrics['legal_balls_bowled'] >= 12) & (metrics['matches_bowled'] >= 2)) & ~(bowl_high | bowl_med)
    
    bowl_qual = bowl_high | bowl_med

    metrics['bowling_sample_size'] = metrics['legal_balls_bowled'].astype(int)
    metrics['bowling_ranking_eligible'] = bowl_qual
    metrics['bowling_confidence_tier'] = np.select(
        [bowl_high, bowl_med, bowl_lim],
        ['HIGH', 'MEDIUM', 'LIMITED_EVIDENCE'],
        default='INSUFFICIENT_DATA'
    )
    metrics['bowling_rating_status'] = np.select(
        [bowl_qual, bowl_lim],
        ['RATED', 'LIMITED_EVIDENCE'],
        default='UNRATED_INSUFFICIENT_DATA'
    )

    # Bowling Empirical Bayes Prior derived from qualified bowlers
    mu_bowl = metrics.loc[bowl_qual, 'pressure_runs_saved_per_ball'].mean()
    tau2_bowl = max(0.01, metrics.loc[bowl_qual, 'pressure_runs_saved_per_ball'].var())
    
    v_bowl = 1.0
    n_bowl = np.maximum(metrics['pressure_balls_bowled'].values, 1)
    sigma2_bowl = v_bowl / n_bowl
    b_bowl = sigma2_bowl / (tau2_bowl + sigma2_bowl)
    shrunk_bowl = (1.0 - b_bowl) * metrics['pressure_runs_saved_per_ball'].values + b_bowl * mu_bowl
    unc_bowl = np.sqrt(1.0 / (1.0/tau2_bowl + 1.0/sigma2_bowl))

    no_bowl_mask = metrics['pressure_balls_bowled'] == 0
    shrunk_bowl[no_bowl_mask] = mu_bowl
    unc_bowl[no_bowl_mask] = np.sqrt(tau2_bowl)

    metrics['eb_bowling_impact'] = shrunk_bowl
    metrics['bowling_uncertainty'] = unc_bowl

    wkts_per_match = metrics['bowler_wickets'].values / np.maximum(1, metrics['matches_bowled'].values)
    metrics['bowling_ranking_score'] = np.where(
        bowl_qual,
        shrunk_bowl - 0.5 * unc_bowl + 0.1 * np.minimum(2.0, wkts_per_match),
        np.nan
    )

    # Bowling Rating: 15.0 to 99.0 scale, ONLY for eligible players
    metrics['bowling_rating'] = np.where(
        bowl_qual,
        np.clip(50.0 + shrunk_bowl * 40.0 + 5.0 * np.minimum(2.0, wkts_per_match), 15.0, 99.0).round(1),
        np.nan
    )
    metrics['overall_bowling_rating'] = metrics['bowling_rating']

    # C. OFFICIAL DISCIPLINE RANKS (Eligible players only!)
    metrics['batting_official_rank'] = np.nan
    metrics['bowling_official_rank'] = np.nan

    eligible_bat_sorted = metrics[metrics['batting_ranking_eligible']].sort_values(by='batting_ranking_score', ascending=False)
    metrics.loc[eligible_bat_sorted.index, 'batting_official_rank'] = np.arange(1, len(eligible_bat_sorted) + 1)

    eligible_bowl_sorted = metrics[metrics['bowling_ranking_eligible']].sort_values(by='bowling_ranking_score', ascending=False)
    metrics.loc[eligible_bowl_sorted.index, 'bowling_official_rank'] = np.arange(1, len(eligible_bowl_sorted) + 1)

    # D. OVERALL PLAYER RATING & CONFIDENCE
    # Uses primary discipline + secondary demonstrated skill, never artificial defaults!
    conditions_overall = [
        (metrics['primary_role'].isin(['BATTER', 'WICKETKEEPER'])) & metrics['batting_ranking_eligible'],
        (metrics['primary_role'] == 'BOWLER') & metrics['bowling_ranking_eligible'],
        (metrics['primary_role'] == 'ALL_ROUNDER') & metrics['batting_ranking_eligible'] & metrics['bowling_ranking_eligible'],
        (metrics['primary_role'] == 'ALL_ROUNDER') & metrics['batting_ranking_eligible'] & ~metrics['bowling_ranking_eligible'],
        (metrics['primary_role'] == 'ALL_ROUNDER') & ~metrics['batting_ranking_eligible'] & metrics['bowling_ranking_eligible'],
    ]
    choices_overall = [
        np.where(metrics['bowling_ranking_eligible'], 0.85 * metrics['batting_rating'] + 0.15 * metrics['bowling_rating'], metrics['batting_rating']),
        np.where(metrics['batting_ranking_eligible'], 0.85 * metrics['bowling_rating'] + 0.15 * metrics['batting_rating'], metrics['bowling_rating']),
        0.50 * metrics['batting_rating'] + 0.50 * metrics['bowling_rating'],
        metrics['batting_rating'],
        metrics['bowling_rating']
    ]
    metrics['overall_player_rating'] = np.select(conditions_overall, choices_overall, default=np.nan).round(1)

    # Overall Confidence Tier (for high-level display)
    conditions_conf = [
        (metrics['batting_confidence_tier'] == 'HIGH') | (metrics['bowling_confidence_tier'] == 'HIGH'),
        (metrics['batting_confidence_tier'] == 'MEDIUM') | (metrics['bowling_confidence_tier'] == 'MEDIUM'),
        (metrics['batting_confidence_tier'] == 'LIMITED_EVIDENCE') | (metrics['bowling_confidence_tier'] == 'LIMITED_EVIDENCE')
    ]
    choices_conf = ['High Evidence', 'Moderate Evidence', 'Limited Evidence']
    metrics['confidence_tier'] = np.select(conditions_conf, choices_conf, default='Insufficient Data')

    # =========================================================================
    # REPRODUCIBLE BOOTSTRAP RESAMPLING & DISCOVERY GAP
    # =========================================================================
    print("Computing match-level bootstrap confidence intervals...")
    ci_low_dict = {}
    ci_high_dict = {}
    
    np.random.seed(42)
    qualified_pids = metrics[metrics['total_matches'] >= 5]['player_id'].values
    for pid in qualified_pids:
        p_matches = match_bat[match_bat['player_id'] == pid]['rae'].values
        if len(p_matches) >= 3:
            boot_means = [np.mean(np.random.choice(p_matches, size=len(p_matches), replace=True)) for _ in range(150)]
            ci_low_dict[pid] = float(np.percentile(boot_means, 2.5))
            ci_high_dict[pid] = float(np.percentile(boot_means, 97.5))
        else:
            ci_low_dict[pid] = -0.5
            ci_high_dict[pid] = 0.5

    metrics['boot_ci_low'] = metrics['player_id'].map(ci_low_dict).fillna(-0.5)
    metrics['boot_ci_high'] = metrics['player_id'].map(ci_high_dict).fillna(0.5)

    # Format portability
    print("Evaluating cross-format portability...")
    ipl_match_counts = match_bat[match_bat['format_scope'] == 'IPL'].groupby('player_id')['match_id'].nunique()
    t20i_match_counts = match_bat[match_bat['format_scope'] == 'T20I'].groupby('player_id')['match_id'].nunique()
    ipl_bat_rae = match_bat[match_bat['format_scope'] == 'IPL'].groupby('player_id')['rae'].mean()
    t20i_bat_rae = match_bat[match_bat['format_scope'] == 'T20I'].groupby('player_id')['rae'].mean()

    metrics['ipl_matches'] = metrics['player_id'].map(ipl_match_counts).fillna(0).astype(int)
    metrics['t20i_matches'] = metrics['player_id'].map(t20i_match_counts).fillna(0).astype(int)
    metrics['ipl_batting_rae'] = metrics['player_id'].map(ipl_bat_rae).fillna(0.0)
    metrics['t20i_batting_rae'] = metrics['player_id'].map(t20i_bat_rae).fillna(0.0)

    has_sufficient_evidence = (metrics['ipl_matches'] >= 5) & (metrics['t20i_matches'] >= 5) & metrics['batting_ranking_eligible']
    metrics['has_both_formats'] = has_sufficient_evidence
    metrics['format_portability_score'] = np.where(
        has_sufficient_evidence,
        np.clip(100.0 - np.abs(metrics['ipl_batting_rae'] - metrics['t20i_batting_rae']) * 35.0, 20.0, 100.0),
        np.nan
    )

    # Statistical Under-Recognition Detector ("Discovery Gap")
    print("Computing Statistical Under-Recognition (Discovery Gap)...")
    qual_bat = metrics['batting_ranking_eligible']
    metrics['conv_bat_score'] = np.nan
    metrics['conv_bat_percentile'] = np.nan
    metrics['adjusted_bat_percentile'] = np.nan

    conv_scores = (metrics.loc[qual_bat, 'batting_avg'] * metrics.loc[qual_bat, 'batting_sr']) / 100.0
    metrics.loc[qual_bat, 'conv_bat_score'] = conv_scores
    metrics.loc[qual_bat, 'conv_bat_percentile'] = (stats.rankdata(conv_scores) / qual_bat.sum()) * 100.0

    adj_scores = metrics.loc[qual_bat, 'eb_batting_impact']
    metrics.loc[qual_bat, 'adjusted_bat_percentile'] = (stats.rankdata(adj_scores) / qual_bat.sum()) * 100.0

    metrics['discovery_gap'] = metrics['adjusted_bat_percentile'] - metrics['conv_bat_percentile']
    metrics['is_undervalued_talent'] = (metrics['discovery_gap'] >= 18.0) & (metrics['eb_batting_impact'] > 0.05) & qual_bat

    # Preserve supplementary emerging candidate discovery fields
    # Strict Scope Isolation: Emerging competitions only, Super Overs excluded
    df_emg = df_raw[(df_raw['is_primary_scope'] == False) & (df_raw['is_super_over'] == False)].copy()
    if len(df_emg) > 0:
        df_emg['is_high_p'] = df_emg['pressure_index'] >= 6.5
        emg_bat = df_emg[df_emg['is_high_p']].groupby('striker_id').agg(
            emerging_pressure_balls=('innings_ball_num', 'count'),
            emerging_pressure_runs=('batter_runs', 'sum')
        ).reset_index().rename(columns={'striker_id': 'player_id'})

        emg_bowl = df_emg[df_emg['is_high_p']].groupby('bowler_id').agg(
            emerging_pressure_balls_bowled=('innings_ball_num', 'count'),
            emerging_pressure_runs_conceded=('bowler_conceded_runs', 'sum'),
            emerging_pressure_wickets=('is_bowler_wicket', 'sum')
        ).reset_index().rename(columns={'bowler_id': 'player_id'})

        metrics = metrics.merge(emg_bat, on='player_id', how='left').merge(emg_bowl, on='player_id', how='left')
        metrics['emerging_pressure_balls'] = metrics['emerging_pressure_balls'].fillna(0).astype(int)
        metrics['emerging_pressure_runs'] = metrics['emerging_pressure_runs'].fillna(0).astype(int)
        metrics['emerging_pressure_sr'] = np.where(metrics['emerging_pressure_balls'] > 0, (metrics['emerging_pressure_runs'] / metrics['emerging_pressure_balls']) * 100.0, np.nan)
        metrics['emerging_pressure_balls_bowled'] = metrics['emerging_pressure_balls_bowled'].fillna(0).astype(int)
        metrics['emerging_pressure_runs_conceded'] = metrics['emerging_pressure_runs_conceded'].fillna(0).astype(int)
        metrics['emerging_pressure_wickets'] = metrics['emerging_pressure_wickets'].fillna(0).astype(int)
        metrics['emerging_pressure_economy'] = np.where(metrics['emerging_pressure_balls_bowled'] > 0, metrics['emerging_pressure_runs_conceded'] / (metrics['emerging_pressure_balls_bowled'] / 6.0), np.nan)
        metrics['is_emerging_candidate'] = (metrics['emerging_pressure_balls'] > 0) | (metrics['emerging_pressure_balls_bowled'] > 0)
    else:
        metrics['emerging_pressure_balls'] = 0
        metrics['emerging_pressure_runs'] = 0
        metrics['emerging_pressure_sr'] = np.nan
        metrics['emerging_pressure_balls_bowled'] = 0
        metrics['emerging_pressure_runs_conceded'] = 0
        metrics['emerging_pressure_wickets'] = 0
        metrics['emerging_pressure_economy'] = np.nan
        metrics['is_emerging_candidate'] = False

    metrics['competition_scope'] = "IPL_T20I"

    print("Evidence-based ratings calculation complete.")
    return metrics
