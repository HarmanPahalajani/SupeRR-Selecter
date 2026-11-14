"""
Independent Regression & Integrity Tests — Batting Pressure RAE & Wide Ball Attribution
Part of SupeRR Intelligence — Pressure Performer Intelligence

Verifies:
1. A wide delivery with positive expected_batter_runs contributes zero batting RAE (rae == 0.0).
2. A wide delivery contributes zero batter-faced balls (hp_balls == 0, hp_exp_runs == 0.0).
3. Wide runs remain included in bowler-conceded runs in the bowling pipeline.
4. A legal bye or leg-bye delivery remains a batting opportunity with zero batter runs and valid negative RAE.
5. Ordinary legal deliveries retain the standard RAE formula (batter_runs - expected_batter_runs).
6. Reaggregated player-level RAE strictly agrees with eligible delivery-level contributions.
"""

import pytest
import numpy as np
import pandas as pd

from backend.analytics.pressure_performers.contribution import compute_delivery_contributions
from backend.analytics.pressure_performers.match_aggregation import aggregate_player_matches
from backend.analytics.pressure_bowlers.contribution import compute_bowling_delivery_contributions


def test_wide_ball_contributes_zero_batting_rae_and_zero_balls():
    """
    Ensure wide deliveries never penalize a batter:
    expected_batter_runs must be 0.0, rae must be 0.0, and hp_balls must be 0.
    """
    df = pd.DataFrame([{
        "striker_id": 101,
        "striker_name": "Test Batter",
        "match_id": 99901,
        "comp_id": 1,
        "comp_name": "Test League",
        "season": 2024,
        "match_date": "2024-05-01",
        "format_scope": "IPL",
        "innings": 2,
        "batter_runs": 0,
        "extras_wide_runs": 1,
        "extras_noball_runs": 0,
        "extras_bye_legbye_runs": 0,
        "is_legal_ball": False,
        "expected_batter_runs": 1.45,  # Upstream model expectation before zeroing
        "pressure_index": 9.2,
        "pre_ball_score": 150,
        "pre_ball_wickets": 4,
        "required_run_rate": 10.5,
        "legal_balls_remaining": 12,
        "is_wicket": False,
        "is_four": False,
        "is_six": False
    }])
    
    # 1. Delivery contribution check
    df_contrib = compute_delivery_contributions(df)
    assert df_contrib.loc[0, "expected_batter_runs"] == 0.0, "Expected batter runs on wide must be 0.0"
    assert df_contrib.loc[0, "rae"] == 0.0, "Batting RAE on wide must be exactly 0.0"
    assert df_contrib.loc[0, "is_legal_ball"] == False, "Wide delivery must not be a legal ball"
    
    # 2. Match aggregation check
    m_df = aggregate_player_matches(df_contrib)
    assert len(m_df) == 1
    row = m_df.iloc[0]
    assert row["hp_balls"] == 0, f"hp_balls on wide must be 0, got {row['hp_balls']}"
    assert row["hp_runs"] == 0, f"hp_runs on wide must be 0, got {row['hp_runs']}"
    assert row["hp_exp_runs"] == 0.0, f"hp_exp_runs on wide must be 0.0, got {row['hp_exp_runs']}"
    assert row["hp_rae"] == 0.0, f"hp_rae on wide must be 0.0, got {row['hp_rae']}"


def test_wide_runs_remain_included_in_bowler_conceded_runs():
    """
    Ensure wide deliveries continue to be counted as runs conceded by the bowler in the bowling pipeline.
    """
    df_bowling = pd.DataFrame([{
        "bowler_id": 202,
        "bowler_name": "Test Bowler",
        "match_id": 99901,
        "batter_runs": 0,
        "extras_wide_runs": 1,
        "extras_noball_runs": 0,
        "extras_bye_legbye_runs": 0,
        "expected_bowler_conceded_runs": 1.20,
        "is_wicket": False
    }])
    
    res = compute_bowling_delivery_contributions(df_bowling)
    assert res.loc[0, "bowler_conceded_runs"] == 1, "Bowler must concede 1 run on wide"
    assert res.loc[0, "is_legal_ball"] == False, "Wide must not be a legal ball for bowler"
    # Runs saved = expected - conceded = 1.20 - 1 = 0.20
    assert np.isclose(res.loc[0, "runs_saved"], 0.20), "Runs saved must equal expected - conceded"


def test_legal_bye_or_legbye_remains_batting_opportunity_with_valid_negative_rae():
    """
    Ensure legal deliveries resulting in byes or leg-byes count as a ball faced,
    with 0 batter runs and a valid negative RAE penalty (0 - expected_batter_runs).
    """
    df = pd.DataFrame([{
        "striker_id": 101,
        "striker_name": "Test Batter",
        "match_id": 99901,
        "comp_id": 1,
        "comp_name": "Test League",
        "season": 2024,
        "match_date": "2024-05-01",
        "format_scope": "IPL",
        "innings": 2,
        "batter_runs": 0,
        "extras_wide_runs": 0,
        "extras_noball_runs": 0,
        "extras_bye_legbye_runs": 1,
        "is_legal_ball": True,
        "expected_batter_runs": 1.25,
        "pressure_index": 9.0,
        "pre_ball_score": 150,
        "pre_ball_wickets": 4,
        "required_run_rate": 10.5,
        "legal_balls_remaining": 11,
        "is_wicket": False,
        "is_four": False,
        "is_six": False
    }])
    
    df_contrib = compute_delivery_contributions(df)
    assert df_contrib.loc[0, "expected_batter_runs"] == 1.25
    assert np.isclose(df_contrib.loc[0, "rae"], -1.25), "Batter faced legal delivery and scored 0 off bat -> RAE is -1.25"
    assert df_contrib.loc[0, "is_legal_ball"] == True
    
    m_df = aggregate_player_matches(df_contrib)
    assert len(m_df) == 1
    row = m_df.iloc[0]
    assert row["hp_balls"] == 1, "Legal bye delivery must increment balls faced"
    assert row["hp_runs"] == 0, "Batter runs must remain 0"
    assert np.isclose(row["hp_exp_runs"], 1.25), "Expected runs must be 1.25"
    assert np.isclose(row["hp_rae"], -1.25), "RAE must be -1.25"


def test_ordinary_legal_deliveries_retain_existing_rae_formula():
    """
    Ensure ordinary boundary, scoring, and dot deliveries retain standard RAE = batter_runs - expected_batter_runs.
    """
    deliveries = [
        # Boundary 4
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 4, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": True, "expected_batter_runs": 1.30, "pressure_index": 8.8,
         "pre_ball_score": 150, "pre_ball_wickets": 4, "required_run_rate": 10.0, "legal_balls_remaining": 10,
         "is_wicket": False, "is_four": True, "is_six": False},
        # Dot ball
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 0, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": True, "expected_batter_runs": 1.15, "pressure_index": 8.9,
         "pre_ball_score": 154, "pre_ball_wickets": 4, "required_run_rate": 9.8, "legal_balls_remaining": 9,
         "is_wicket": False, "is_four": False, "is_six": False},
        # Six
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 6, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": True, "expected_batter_runs": 1.40, "pressure_index": 9.1,
         "pre_ball_score": 154, "pre_ball_wickets": 4, "required_run_rate": 10.2, "legal_balls_remaining": 8,
         "is_wicket": False, "is_four": False, "is_six": True},
    ]
    df = pd.DataFrame(deliveries)
    df_contrib = compute_delivery_contributions(df)
    
    assert np.isclose(df_contrib.loc[0, "rae"], 4.0 - 1.30)
    assert np.isclose(df_contrib.loc[1, "rae"], 0.0 - 1.15)
    assert np.isclose(df_contrib.loc[2, "rae"], 6.0 - 1.40)


def test_reaggregated_player_level_rae_agrees_with_eligible_deliveries():
    """
    Ensure that in a realistic match with legal balls, wides, and leg-byes,
    the aggregated hp_rae exactly matches the sum of eligible delivery contributions.
    """
    records = [
        # Legal single
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 1, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": True, "expected_batter_runs": 1.20, "pressure_index": 8.7,
         "pre_ball_score": 100, "pre_ball_wickets": 2, "required_run_rate": 8.5, "legal_balls_remaining": 30,
         "is_wicket": False, "is_four": False, "is_six": False},
        # Wide ball (bowler bowls wide outside off stump)
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 0, "extras_wide_runs": 1, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": False, "expected_batter_runs": 1.50, "pressure_index": 8.7,
         "pre_ball_score": 101, "pre_ball_wickets": 2, "required_run_rate": 8.4, "legal_balls_remaining": 30,
         "is_wicket": False, "is_four": False, "is_six": False},
        # Boundary four
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 4, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": True, "expected_batter_runs": 1.30, "pressure_index": 8.8,
         "pre_ball_score": 102, "pre_ball_wickets": 2, "required_run_rate": 8.2, "legal_balls_remaining": 29,
         "is_wicket": False, "is_four": True, "is_six": False},
        # Leg-bye
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 0, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 1,
         "is_legal_ball": True, "expected_batter_runs": 1.10, "pressure_index": 8.9,
         "pre_ball_score": 106, "pre_ball_wickets": 2, "required_run_rate": 8.0, "legal_balls_remaining": 28,
         "is_wicket": False, "is_four": False, "is_six": False},
        # Another wide ball
        {"striker_id": 101, "striker_name": "Test Batter", "match_id": 99901, "comp_id": 1, "comp_name": "L",
         "season": 2024, "match_date": "2024-05-01", "format_scope": "IPL", "innings": 2,
         "batter_runs": 0, "extras_wide_runs": 1, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0,
         "is_legal_ball": False, "expected_batter_runs": 1.60, "pressure_index": 8.9,
         "pre_ball_score": 107, "pre_ball_wickets": 2, "required_run_rate": 7.9, "legal_balls_remaining": 28,
         "is_wicket": False, "is_four": False, "is_six": False},
    ]
    df = pd.DataFrame(records)
    df_contrib = compute_delivery_contributions(df)
    
    # Check individual RAE values
    # Delivery 0: 1 - 1.20 = -0.20
    # Delivery 1 (Wide): 0.00
    # Delivery 2: 4 - 1.30 = +2.70
    # Delivery 3 (Leg-bye): 0 - 1.10 = -1.10
    # Delivery 4 (Wide): 0.00
    expected_individual_raes = [-0.20, 0.00, 2.70, -1.10, 0.00]
    np.testing.assert_allclose(df_contrib["rae"].values, expected_individual_raes, atol=1e-6)
    
    # Total delivery RAE sum
    total_delivery_rae = df_contrib["rae"].sum()
    assert np.isclose(total_delivery_rae, 1.40), f"Expected 1.40 total delivery RAE, got {total_delivery_rae}"
    
    m_df = aggregate_player_matches(df_contrib)
    assert len(m_df) == 1
    row = m_df.iloc[0]
    
    # Verification of player match aggregates:
    # hp_balls = 3 (1 single + 1 four + 1 legbye; 2 wides excluded)
    # hp_runs = 5 (1 single + 4 from boundary; 0 from wides and legbyes)
    # hp_exp_runs = 1.20 + 1.30 + 1.10 = 3.60 (wides excluded)
    # hp_rae = 1.40 (agrees exactly with sum of individual delivery rae)
    assert row["hp_balls"] == 3
    assert row["hp_runs"] == 5
    assert np.isclose(row["hp_exp_runs"], 3.60)
    assert np.isclose(row["hp_rae"], total_delivery_rae)
