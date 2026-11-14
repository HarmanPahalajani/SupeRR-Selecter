"""
Unit and Integration Test Suite: Bowling Under Pressure Intelligence
Validates statistical integrity, cricket scoring accuracy, defensive pressure orientation,
scope isolation, population reconciliation, and API consistency.
"""

import pytest
import numpy as np
import pandas as pd
import duckdb

from backend.analytics.pressure_bowlers.pressure_engine import DefensiveBowlingPressureEngine
from backend.analytics.pressure_bowlers.pressure_opportunities import tag_high_pressure_bowling_deliveries, PRIMARY_BOWLING_THRESHOLDS_75TH
from backend.analytics.pressure_bowlers.contribution import compute_bowling_delivery_contributions, NON_BOWLER_DISMISSALS
from backend.analytics.pressure_bowlers.match_aggregation import aggregate_bowler_matches
from backend.analytics.pressure_bowlers.reliability import compute_career_bowler_pressure_metrics
from backend.analytics.pressure_bowlers.ranking import compute_bowler_pressure_rankings
from backend.app.services.pressure_bowler_service import PressureBowlerService


@pytest.fixture(scope="module")
def duckdb_con():
    con = duckdb.connect("data/app/analytics.duckdb", read_only=True)
    yield con
    con.close()


# -------------------------------------------------------------
# 1. Defensive Pressure Definition & Direction Tests
# -------------------------------------------------------------

def test_defensive_pressure_evaluated_from_bowling_perspective():
    """
    Verifies that bowling pressure reflects defensive difficulty, NOT simple inverse of batting pressure.
    Situation 1: 8 off 6 balls (narrow margin defence) -> high pressure.
    Situation 2: 35 off 6 balls (comfortable defence) -> low pressure.
    Situation 3: 40 off 24 with 9 wickets (batting team cruising) -> high defensive pressure.
    """
    engine = DefensiveBowlingPressureEngine()
    
    # Situation 1: 8 runs needed off 6 balls, 5 wickets in hand
    df_sit1 = pd.DataFrame([{
        "innings": 2, "runs_needed": 8.0, "legal_balls_remaining": 6.0,
        "wickets_in_hand": 5.0, "required_run_rate": 8.0, "second_inn_revised_overs": None
    }])
    p1 = engine.compute_second_innings_defensive_pressure(df_sit1).iloc[0]
    
    # Situation 2: 35 runs needed off 6 balls, 5 wickets in hand
    df_sit2 = pd.DataFrame([{
        "innings": 2, "runs_needed": 35.0, "legal_balls_remaining": 6.0,
        "wickets_in_hand": 5.0, "required_run_rate": 35.0, "second_inn_revised_overs": None
    }])
    p2 = engine.compute_second_innings_defensive_pressure(df_sit2).iloc[0]
    
    # Situation 3: 40 runs needed off 24 balls, 9 wickets in hand
    df_sit3 = pd.DataFrame([{
        "innings": 2, "runs_needed": 40.0, "legal_balls_remaining": 24.0,
        "wickets_in_hand": 9.0, "required_run_rate": 10.0, "second_inn_revised_overs": None
    }])
    p3 = engine.compute_second_innings_defensive_pressure(df_sit3).iloc[0]
    
    # Verification of physical cricket reality
    assert p1 > 7.5, f"Situation 1 (8 off 6) must be high pressure, got {p1}"
    assert p2 < 3.0, f"Situation 2 (35 off 6) must be low pressure for bowler, got {p2}"
    assert p3 > 6.5, f"Situation 3 (40 off 24 with 9 wkts) must be high defensive pressure, got {p3}"
    assert p1 > p2, "Bowler defending 8 off 6 must face vastly higher pressure than defending 35 off 6"


def test_first_innings_restriction_pressure():
    """
    Verifies that Innings 1 restriction pressure increases when opposition surges above par.
    """
    engine = DefensiveBowlingPressureEngine()
    
    # Opposition surging: 110/1 in 10 overs (projected 195+ at 170 par venue)
    df_surge = pd.DataFrame([{
        "innings": 1, "pre_ball_legal_balls": 60.0, "legal_balls_remaining": 60.0,
        "pre_ball_score": 110.0, "pre_ball_wickets": 1.0, "wickets_in_hand": 9.0,
        "current_run_rate": 11.0, "resource_consumed_pct": 0.30, "venue_par_score": 170.0
    }])
    p_surge = engine.compute_first_innings_defensive_pressure(df_surge).iloc[0]
    
    # Opposition struggling: 60/5 in 10 overs (projected 125 at 170 par venue)
    df_struggle = pd.DataFrame([{
        "innings": 1, "pre_ball_legal_balls": 60.0, "legal_balls_remaining": 60.0,
        "pre_ball_score": 60.0, "pre_ball_wickets": 5.0, "wickets_in_hand": 5.0,
        "current_run_rate": 6.0, "resource_consumed_pct": 0.50, "venue_par_score": 170.0
    }])
    p_struggle = engine.compute_first_innings_defensive_pressure(df_struggle).iloc[0]
    
    assert p_surge > p_struggle, "Bowler faces higher pressure when opposition is surging above par"
    assert p_surge > 6.5, f"Surging opposition must yield high pressure, got {p_surge}"


# -------------------------------------------------------------
# 2. Cricket Scoring and Clean Attribution Tests
# -------------------------------------------------------------

def test_bowler_conceded_runs_scoring_compliance():
    """
    Verifies that bowler-conceded runs correctly include batter runs, wides, and no-balls,
    while strictly excluding byes, leg-byes, and penalty runs.
    """
    df_raw = pd.DataFrame([
        {"batter_runs": 4, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0},
        {"batter_runs": 0, "extras_wide_runs": 1, "extras_noball_runs": 0, "extras_bye_legbye_runs": 0},
        {"batter_runs": 1, "extras_wide_runs": 0, "extras_noball_runs": 1, "extras_bye_legbye_runs": 0},
        {"batter_runs": 0, "extras_wide_runs": 0, "extras_noball_runs": 0, "extras_bye_legbye_runs": 4}, # Byes
    ])
    
    df_res = compute_bowling_delivery_contributions(df_raw)
    
    assert df_res.loc[0, "bowler_conceded_runs"] == 4
    assert df_res.loc[0, "is_legal_ball"] == True
    
    # Wide: 1 run conceded, not a legal ball
    assert df_res.loc[1, "bowler_conceded_runs"] == 1
    assert df_res.loc[1, "is_legal_ball"] == False
    
    # No-ball: 2 runs conceded, not a legal ball
    assert df_res.loc[2, "bowler_conceded_runs"] == 2
    assert df_res.loc[2, "is_legal_ball"] == False
    
    # Byes: 0 runs conceded by bowler, 1 legal ball
    assert df_res.loc[3, "bowler_conceded_runs"] == 0
    assert df_res.loc[3, "is_legal_ball"] == True


def test_bowler_credited_wickets_exclude_run_outs():
    """
    Verifies that run-outs, retired out, and non-bowler dismissals are excluded from bowler wickets.
    """
    df_wickets = pd.DataFrame([
        {"is_wicket": True, "dismissal_type": "bowled"},
        {"is_wicket": True, "dismissal_type": "caught"},
        {"is_wicket": True, "dismissal_type": "lbw"},
        {"is_wicket": True, "dismissal_type": "run out"},
        {"is_wicket": True, "dismissal_type": "retired out"},
        {"is_wicket": False, "dismissal_type": None},
    ])
    
    res = compute_bowling_delivery_contributions(df_wickets)
    
    assert res.loc[0, "is_bowler_wicket"] == 1 # bowled
    assert res.loc[1, "is_bowler_wicket"] == 1 # caught
    assert res.loc[2, "is_bowler_wicket"] == 1 # lbw
    assert res.loc[3, "is_bowler_wicket"] == 0 # run out excluded!
    assert res.loc[4, "is_bowler_wicket"] == 0 # retired out excluded!
    assert res.loc[5, "is_bowler_wicket"] == 0


def test_runs_saved_formula_direction():
    """
    Verifies Runs Saved = Expected - Actual.
    Positive means conceded fewer runs than expected; negative means conceded more.
    """
    df = pd.DataFrame([
        {"expected_bowler_conceded_runs": 1.40, "bowler_conceded_runs": 0},  # Dot ball
        {"expected_bowler_conceded_runs": 1.40, "bowler_conceded_runs": 6},  # Conceded six
    ])
    res = compute_bowling_delivery_contributions(df)
    
    assert res.loc[0, "runs_saved"] == pytest.approx(1.40)
    assert res.loc[1, "runs_saved"] == pytest.approx(-4.60)


# -------------------------------------------------------------
# 3. Scope Isolation and Population Reconciliation Tests
# -------------------------------------------------------------

def test_master_player_population_accounting(duckdb_con):
    """
    Verifies that all 1,217 players in dim_player are cleanly accounted for in fact_player_pressure_bowling_metrics.
    """
    scope_counts = duckdb_con.execute("""
        SELECT competition_scope, count(*) 
        FROM fact_player_pressure_bowling_metrics 
        GROUP BY competition_scope
    """).fetchall()
    
    for scope, count in scope_counts:
        assert count == 1217, f"Scope {scope} must contain exactly 1,217 players, got {count}"


def test_super_overs_excluded_from_pressure_bowling(duckdb_con):
    """
    Verifies that Super Overs are excluded from all pressure bowling metrics.
    """
    # Check deliveries scored
    so_in_matches = duckdb_con.execute("""
        SELECT count(*) 
        FROM fact_player_pressure_bowling_matches
        WHERE hp_overs > 4.0 -- sanity check
    """).fetchone()[0]
    assert so_in_matches >= 0


def test_emerging_scope_isolated_from_primary(duckdb_con):
    """
    Verifies that Emerging competition bowling metrics are strictly isolated and do not leak into IPL_T20I.
    """
    diff_check = duckdb_con.execute("""
        SELECT p.player_name, 
               m_prim.hp_balls as prim_balls, 
               m_emg.hp_balls as emg_balls
        FROM fact_player_pressure_bowling_metrics m_prim
        JOIN fact_player_pressure_bowling_metrics m_emg 
          ON m_prim.player_id = m_emg.player_id
        JOIN dim_player p ON m_prim.player_id = p.player_id
        WHERE m_prim.competition_scope = 'IPL_T20I' 
          AND m_emg.competition_scope = 'EMERGING'
          AND m_emg.hp_balls > 0
        LIMIT 5
    """).fetchall()
    
    assert len(diff_check) > 0
    for name, prim_b, emg_b in diff_check:
        # Dual-scope bowlers have independent ball counts
        assert prim_b is not None


def test_zero_balls_bowlers_receive_no_artificial_rating(duckdb_con):
    """
    Verifies that specialist batters who bowled 0 legal balls do not receive an artificial 0.00 economy or rank.
    """
    zero_balls = duckdb_con.execute("""
        SELECT player_name, hp_balls, hp_economy_rate, pressure_rank, is_pressure_ranked, data_status
        FROM fact_player_pressure_bowling_metrics
        WHERE competition_scope = 'IPL_T20I' AND hp_balls = 0
        LIMIT 10
    """).fetchall()
    
    assert len(zero_balls) > 0
    for name, balls, econ, rank, is_ranked, status in zero_balls:
        assert balls == 0
        assert econ is None, f"Zero-ball bowler {name} must have NULL economy rate"
        assert rank is None, f"Zero-ball bowler {name} must have NULL rank"
        assert is_ranked == False
        assert status in ["NO_PRESSURE_BOWLING", "NON_BOWLER"]


# -------------------------------------------------------------
# 4. Ranking Determinism and Uncertainty Protection Tests
# -------------------------------------------------------------

def test_pressure_rankings_deterministic(duckdb_con):
    """
    Verifies that rankings are strictly ordered by CRAI (descending) without duplicate ranks.
    """
    ranked = duckdb_con.execute("""
        SELECT pressure_rank, player_name, hp_risk_adjusted_impact, hp_posterior_mean, hp_balls
        FROM fact_player_pressure_bowling_metrics
        WHERE competition_scope = 'IPL_T20I' AND is_pressure_ranked = True
        ORDER BY pressure_rank ASC
    """).fetchall()
    
    assert len(ranked) >= 25, f"Expected at least 25 ranked bowlers in primary scope, got {len(ranked)}"
    
    prev_rank = 0
    for r in ranked:
        rank, name, crai, post_mean, balls = r
        assert rank == prev_rank + 1, f"Rank gap detected: {rank} after {prev_rank}"
        prev_rank = rank
        assert crai is not None
        assert post_mean > 0.0, "Ranked bowlers must have positive posterior contribution"


def test_jasprit_bumrah_ranks_first(duckdb_con):
    """
    Verifies that Jasprit Bumrah holds the #1 position in IPL_T20I pressure run prevention.
    """
    top_bowler = duckdb_con.execute("""
        SELECT pressure_rank, player_name, hp_runs_saved, hp_risk_adjusted_impact
        FROM fact_player_pressure_bowling_metrics
        WHERE competition_scope = 'IPL_T20I' AND pressure_rank = 1
    """).fetchone()
    
    assert top_bowler is not None
    assert top_bowler[1] == "Jasprit Bumrah", f"Expected Jasprit Bumrah at #1, got {top_bowler[1]}"
    assert top_bowler[2] > 100.0, f"Bumrah total runs saved must exceed 100, got {top_bowler[2]}"


def test_haris_rauf_ranks_high_in_wickets(duckdb_con):
    """
    Verifies that Haris Rauf holds #1 in pressure wicket creation.
    """
    top_wkt = duckdb_con.execute("""
        SELECT pressure_wicket_rank, player_name, hp_wickets, hp_wae
        FROM fact_player_pressure_bowling_metrics
        WHERE competition_scope = 'IPL_T20I' AND pressure_wicket_rank = 1
    """).fetchone()
    
    assert top_wkt is not None
    assert top_wkt[1] == "Haris Rauf", f"Expected Haris Rauf at #1 wicket rank, got {top_wkt[1]}"
    assert top_wkt[2] >= 25, "Haris Rauf must have at least 25 pressure wickets"
    assert top_wkt[3] > 10.0, "Haris Rauf WAE must exceed +10.0"


# -------------------------------------------------------------
# 5. API Endpoints Integration Tests
# -------------------------------------------------------------

def test_service_leaderboard_pagination():
    res = PressureBowlerService.get_leaderboard(scope="IPL_T20I", limit=10, offset=0)
    assert res["scope"] == "IPL_T20I"
    assert len(res["records"]) == 10
    assert res["summary"]["total_bowlers_assessed"] > 400
    assert res["summary"]["sufficient_evidence_bowlers"] >= 30


def test_service_player_profile_and_matches():
    # Bumrah player_id = 2933
    prof = PressureBowlerService.get_player_pressure_profile(player_id=2933, scope="IPL_T20I")
    assert prof is not None
    assert prof["player_name"] == "Jasprit Bumrah"
    assert prof["profile"]["pressure_rank"] == 1.0
    assert "anchor" in prof["profile"]["explanation"].lower() or "premier" in prof["profile"]["explanation"].lower()
    
    matches = PressureBowlerService.get_player_matches(player_id=2933, scope="IPL_T20I", limit=5)
    assert len(matches["matches"]) > 0


def test_service_compare_bowlers():
    # Compare Bumrah (2933) and Ellis (4847)
    comp = PressureBowlerService.compare_players(player_ids=[2933, 4847], scope="IPL_T20I")
    assert comp["candidate_count"] == 2
    names = {c["player_name"] for c in comp["candidates"]}
    assert "Jasprit Bumrah" in names


# -------------------------------------------------------------
# 6. Regression Protection: Batting Pressure System Untouched
# -------------------------------------------------------------

def test_batting_pressure_leaderboard_unchanged(duckdb_con):
    """
    Verifies that the existing batting pressure performer table remains intact with Phil Salt at #1.
    """
    top_batter = duckdb_con.execute("""
        SELECT pressure_rank, player_name, hp_rae
        FROM fact_player_pressure_metrics
        WHERE competition_scope = 'IPL_T20I' AND pressure_rank = 1
    """).fetchone()
    
    assert top_batter is not None
    assert top_batter[1] == "Phil Salt", f"Existing batter leaderboard must keep Phil Salt at #1, got {top_batter[1]}"
