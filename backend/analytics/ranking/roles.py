"""
Authoritative Player Role Classification Engine for SupeRR Intelligence.

Mutually Exclusive Primary Roles:
- BATTER
- BOWLER
- ALL_ROUNDER
- WICKETKEEPER
- UNKNOWN (insufficient participation/evidence)

Secondary Skills:
- Wicketkeeper-Batter
- Wicketkeeper-All-rounder
- Batting All-rounder
- Bowling All-rounder
- Part-time Bowler
- Pure Batter
- Specialist Bowler
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def classify_player_roles(
    df_metrics: pd.DataFrame,
    df_p11: pd.DataFrame,
    df_matches: pd.DataFrame,
    df_deliveries: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes deterministic, mutually exclusive primary roles, secondary skill tags,
    evidence metrics, confidence tiers, and format-specific roles (IPL & T20I).
    """
    metrics = df_metrics.copy()
    
    # 1. Compute robust match participation from playing_eleven (filtered to is_played==1)
    p11_played = df_p11[df_p11['is_played'] == 1].merge(df_matches[['match_id', 'format_scope']], on='match_id', how='left')
    
    # Total matches in XI
    p11_tot = p11_played.groupby('player_id')['match_id'].nunique().rename('p11_matches_played')
    
    # Wicketkeeping matches
    p11_wk = p11_played[p11_played['is_wk'] == True].groupby('player_id')['match_id'].nunique().rename('p11_wk_matches')
    
    # Format-specific playing XI matches
    p11_ipl_tot = p11_played[p11_played['format_scope'] == 'IPL'].groupby('player_id')['match_id'].nunique().rename('p11_ipl_matches')
    p11_ipl_wk = p11_played[(p11_played['format_scope'] == 'IPL') & (p11_played['is_wk'] == True)].groupby('player_id')['match_id'].nunique().rename('p11_ipl_wk_matches')
    p11_t20i_tot = p11_played[p11_played['format_scope'] == 'T20I'].groupby('player_id')['match_id'].nunique().rename('p11_t20i_matches')
    p11_t20i_wk = p11_played[(p11_played['format_scope'] == 'T20I') & (p11_played['is_wk'] == True)].groupby('player_id')['match_id'].nunique().rename('p11_t20i_wk_matches')

    # Merge participation signals
    metrics = metrics.merge(p11_tot, on='player_id', how='left')
    metrics = metrics.merge(p11_wk, on='player_id', how='left')
    metrics = metrics.merge(p11_ipl_tot, on='player_id', how='left')
    metrics = metrics.merge(p11_ipl_wk, on='player_id', how='left')
    metrics = metrics.merge(p11_t20i_tot, on='player_id', how='left')
    metrics = metrics.merge(p11_t20i_wk, on='player_id', how='left')

    metrics['p11_matches_played'] = metrics['p11_matches_played'].fillna(0).astype(int)
    metrics['p11_wk_matches'] = metrics['p11_wk_matches'].fillna(0).astype(int)
    metrics['p11_ipl_matches'] = metrics['p11_ipl_matches'].fillna(0).astype(int)
    metrics['p11_ipl_wk_matches'] = metrics['p11_ipl_wk_matches'].fillna(0).astype(int)
    metrics['p11_t20i_matches'] = metrics['p11_t20i_matches'].fillna(0).astype(int)
    metrics['p11_t20i_wk_matches'] = metrics['p11_t20i_wk_matches'].fillna(0).astype(int)

    # Effective matches is the maximum of playing XI appearances, batting appearances, or bowling appearances
    metrics['effective_matches'] = np.maximum(
        metrics['p11_matches_played'],
        np.maximum(metrics['matches_batted'], metrics['matches_bowled'])
    ).astype(int)

    # Derived rates
    eff_m = np.maximum(metrics['effective_matches'], 1)
    metrics['wk_match_ratio'] = np.where(metrics['effective_matches'] > 0, metrics['p11_wk_matches'] / eff_m, 0.0)
    metrics['balls_faced_per_match'] = metrics['balls_faced'] / eff_m
    metrics['balls_bowled_per_match'] = metrics['legal_balls_bowled'] / eff_m
    metrics['bowling_match_rate'] = metrics['matches_bowled'] / eff_m
    metrics['batting_match_rate'] = metrics['matches_batted'] / eff_m

    # =========================================================================
    # PRIMARY ROLE CLASSIFICATION (MUTUALLY EXCLUSIVE)
    # =========================================================================

    # Condition 1: UNKNOWN (Insufficient participation evidence)
    # Zero appearances in playing XI, zero deliveries faced, zero deliveries bowled
    cond_unknown = (
        (metrics['effective_matches'] == 0) & 
        (metrics['balls_faced'] == 0) & 
        (metrics['legal_balls_bowled'] == 0)
    )

    # Condition 2: WICKETKEEPER
    # Verified playing XI designation with consistency threshold
    cond_wk = (~cond_unknown) & (
        ((metrics['p11_wk_matches'] >= 3) & (metrics['wk_match_ratio'] >= 0.25)) |
        (metrics['p11_wk_matches'] >= 8) |
        ((metrics['p11_wk_matches'] >= 1) & (metrics['effective_matches'] <= 3) & (metrics['wk_match_ratio'] >= 0.50))
    )

    # Condition 3: ALL_ROUNDER
    # Meaningful and repeated batting AND bowling responsibility
    cond_ar = (~cond_unknown) & (~cond_wk) & (
        (metrics['balls_faced'] >= 60) &
        (metrics['legal_balls_bowled'] >= 90) &
        (metrics['balls_faced_per_match'] >= 5.0) &
        (metrics['balls_bowled_per_match'] >= 6.0) &
        (metrics['bowling_match_rate'] >= 0.25)
    )

    # Condition 4: BOWLER
    # Substantial bowling responsibility without qualifying as all-rounder
    cond_bowler = (~cond_unknown) & (~cond_wk) & (~cond_ar) & (
        (metrics['legal_balls_bowled'] >= metrics['balls_faced'] * 1.5) |
        ((metrics['legal_balls_bowled'] >= 30) & (metrics['balls_faced'] < 30)) |
        ((metrics['bowling_match_rate'] >= 0.60) & (metrics['balls_faced_per_match'] < 5.0))
    )

    # Condition 5: BATTER
    # Primary batting responsibility without regular bowling involvement
    cond_batter = (~cond_unknown) & (~cond_wk) & (~cond_ar) & (~cond_bowler)

    conditions = [cond_unknown, cond_wk, cond_ar, cond_bowler, cond_batter]
    choices = ['UNKNOWN', 'WICKETKEEPER', 'ALL_ROUNDER', 'BOWLER', 'BATTER']

    metrics['primary_role'] = np.select(conditions, choices, default='UNKNOWN')

    # Ensure mutual exclusivity
    assert not metrics['primary_role'].isnull().any(), "Found null primary roles!"
    assert set(metrics['primary_role'].unique()).issubset(set(choices)), "Invalid role values assigned!"

    # =========================================================================
    # SECONDARY SKILLS (OVERLAPPING / MULTI-TAG)
    # =========================================================================
    secondary_skills = []
    role_confidences = []
    role_evidences = []

    for _, r in metrics.iterrows():
        p_role = r['primary_role']
        skills = []
        conf = "Low Evidence"
        evid_parts = []

        if p_role == 'UNKNOWN':
            skills.append('Unclassified Squad Member')
            conf = 'No Match Evidence'
            evid_parts.append('No recorded match participation in 2022-2026 scope')

        elif p_role == 'WICKETKEEPER':
            evid_parts.append(f"{r['p11_wk_matches']} WK matches ({r['wk_match_ratio']*100:.1f}% ratio)")
            if r['legal_balls_bowled'] >= 60:
                skills.append('Wicketkeeper-All-rounder')
            else:
                skills.append('Wicketkeeper-Batter')
            
            if r['p11_wk_matches'] >= 10:
                conf = 'High Evidence'
            elif r['p11_wk_matches'] >= 3:
                conf = 'Moderate Evidence'
            else:
                conf = 'Low Evidence'

        elif p_role == 'ALL_ROUNDER':
            evid_parts.append(f"{int(r['balls_faced'])} balls faced, {int(r['legal_balls_bowled'])} balls bowled across {int(r['effective_matches'])} matches")
            # Distinguish Batting All-rounder vs Bowling All-rounder
            if r['balls_faced'] >= r['legal_balls_bowled'] * 1.2:
                skills.append('Batting All-rounder')
            elif r['legal_balls_bowled'] >= r['balls_faced'] * 1.2:
                skills.append('Bowling All-rounder')
            else:
                skills.append('Balanced All-rounder')

            if r['balls_faced'] >= 150 and r['legal_balls_bowled'] >= 150:
                conf = 'High Evidence'
            else:
                conf = 'Moderate Evidence'

        elif p_role == 'BOWLER':
            evid_parts.append(f"{int(r['legal_balls_bowled'])} balls bowled ({r['balls_bowled_per_match']:.1f}/match)")
            if r['balls_faced'] >= 60 and r['balls_faced_per_match'] >= 4.0:
                skills.append('Bowling All-rounder')
            else:
                skills.append('Specialist Bowler')
            
            if r['legal_balls_bowled'] >= 240:
                conf = 'High Evidence'
            elif r['legal_balls_bowled'] >= 60:
                conf = 'Moderate Evidence'
            else:
                conf = 'Low Evidence'

        elif p_role == 'BATTER':
            evid_parts.append(f"{int(r['balls_faced'])} balls faced ({r['balls_faced_per_match']:.1f}/match)")
            if r['legal_balls_bowled'] >= 12:
                skills.append('Part-time Bowler')
            else:
                skills.append('Pure Batter')
            
            # Check occasional wicketkeeper tag
            if r['p11_wk_matches'] >= 1:
                skills.append('Occasional Wicketkeeper')

            if r['balls_faced'] >= 200:
                conf = 'High Evidence'
            elif r['balls_faced'] >= 50:
                conf = 'Moderate Evidence'
            else:
                conf = 'Low Evidence'

        secondary_skills.append(", ".join(skills))
        role_confidences.append(conf)
        role_evidences.append("; ".join(evid_parts))

    metrics['secondary_skills'] = secondary_skills
    metrics['role_confidence'] = role_confidences
    metrics['role_evidence'] = role_evidences

    # =========================================================================
    # FORMAT-SPECIFIC ROLES (IPL & T20I)
    # =========================================================================
    # df_deliveries already has format_scope
    sub_bbb = df_deliveries

    # IPL
    ipl_bat = sub_bbb[sub_bbb['format_scope'] == 'IPL'].groupby('striker_id')['runs'].count().rename('ipl_bf')
    ipl_bowl = sub_bbb[sub_bbb['format_scope'] == 'IPL'].groupby('bowler_id')['is_legal_ball'].sum().rename('ipl_bb')
    metrics = metrics.merge(ipl_bat, left_on='player_id', right_index=True, how='left')
    metrics = metrics.merge(ipl_bowl, left_on='player_id', right_index=True, how='left')
    metrics['ipl_bf'] = metrics['ipl_bf'].fillna(0).astype(int)
    metrics['ipl_bb'] = metrics['ipl_bb'].fillna(0).astype(int)

    # T20I
    t20i_bat = sub_bbb[sub_bbb['format_scope'] == 'T20I'].groupby('striker_id')['runs'].count().rename('t20i_bf')
    t20i_bowl = sub_bbb[sub_bbb['format_scope'] == 'T20I'].groupby('bowler_id')['is_legal_ball'].sum().rename('t20i_bb')
    metrics = metrics.merge(t20i_bat, left_on='player_id', right_index=True, how='left')
    metrics = metrics.merge(t20i_bowl, left_on='player_id', right_index=True, how='left')
    metrics['t20i_bf'] = metrics['t20i_bf'].fillna(0).astype(int)
    metrics['t20i_bb'] = metrics['t20i_bb'].fillna(0).astype(int)

    def format_role(bf_col, bb_col, wk_col, tot_m_col):
        eff = np.maximum(metrics[tot_m_col], 1)
        wk_r = np.where(metrics[tot_m_col] > 0, metrics[wk_col] / eff, 0.0)
        c_unk = (metrics[tot_m_col] == 0) & (metrics[bf_col] == 0) & (metrics[bb_col] == 0)
        c_wk = (~c_unk) & (((metrics[wk_col] >= 2) & (wk_r >= 0.25)) | (metrics[wk_col] >= 5) | ((metrics[wk_col] >= 1) & (metrics[tot_m_col] <= 2) & (wk_r >= 0.5)))
        c_ar = (~c_unk) & (~c_wk) & (
            (metrics[bf_col] >= 30) & (metrics[bb_col] >= 40) & 
            (metrics[bf_col] / eff >= 4.0) & (metrics[bb_col] / eff >= 5.0)
        )
        c_bowl = (~c_unk) & (~c_wk) & (~c_ar) & (
            (metrics[bb_col] >= metrics[bf_col] * 1.5) |
            ((metrics[bb_col] >= 18) & (metrics[bf_col] < 18))
        )
        c_bat = (~c_unk) & (~c_wk) & (~c_ar) & (~c_bowl)
        return np.select([c_unk, c_wk, c_ar, c_bowl, c_bat], ['UNKNOWN', 'WICKETKEEPER', 'ALL_ROUNDER', 'BOWLER', 'BATTER'], default='UNKNOWN')

    metrics['ipl_primary_role'] = format_role('ipl_bf', 'ipl_bb', 'p11_ipl_wk_matches', 'p11_ipl_matches')
    metrics['t20i_primary_role'] = format_role('t20i_bf', 't20i_bb', 'p11_t20i_wk_matches', 'p11_t20i_matches')

    return metrics
