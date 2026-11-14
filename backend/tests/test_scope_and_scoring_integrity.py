"""
Comprehensive Automated Test Suite for Data Integrity, Scope Isolation,
Cricket Statistics Accuracy, and Population Invariants.

Enforces:
1. Strict Scope Isolation (IPL/T20I vs Emerging vs Super Overs).
2. Cricket Scoring Semantics (wides, no-balls, byes, bowler wickets).
3. Missing-Value vs Zero-Value Semantics (Fin Allen & population-wide).
4. Full Master Population Reconciliation (1,217 players).
5. API Serialization Integrity (no artificial defaults or leaked stats).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.analytics_service import AnalyticsService

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def canonical_deliveries():
    return pd.read_parquet("data/processed/fact_delivery_canonical.parquet")

@pytest.fixture(scope="module")
def player_metrics():
    return pd.read_parquet("data/processed/fact_player_metrics.parquet")

@pytest.fixture(scope="module")
def dim_players():
    return pd.read_parquet("data/processed/dim_player.parquet")

@pytest.fixture(scope="module")
def dim_matches():
    return pd.read_parquet("data/processed/dim_match.parquet")

# =========================================================================
# A. SCOPE ISOLATION TESTS
# =========================================================================

def test_scope_delivery_partitioning(canonical_deliveries):
    """Verify exact delivery count accounting across all competition scopes."""
    df = canonical_deliveries
    assert len(df) == 200999, f"Expected 200,999 canonical deliveries, got {len(df)}"
    
    primary_reg = df[(df['is_primary_scope'] == True) & (df['is_super_over'] == False)]
    primary_so = df[(df['is_primary_scope'] == True) & (df['is_super_over'] == True)]
    emerging_reg = df[(df['is_primary_scope'] == False) & (df['is_super_over'] == False)]
    emerging_so = df[(df['is_primary_scope'] == False) & (df['is_super_over'] == True)]
    
    assert len(primary_reg) == 193988, f"Expected 193,988 primary regular deliveries, got {len(primary_reg)}"
    assert len(primary_so) == 26, f"Expected 26 primary super over deliveries, got {len(primary_so)}"
    assert len(emerging_reg) == 6973, f"Expected 6,973 emerging regular deliveries, got {len(emerging_reg)}"
    assert len(emerging_so) == 12, f"Expected 12 emerging super over deliveries, got {len(emerging_so)}"
    assert len(primary_reg) + len(primary_so) + len(emerging_reg) + len(emerging_so) == 200999

def test_super_overs_excluded_from_official_metrics(player_metrics, canonical_deliveries):
    """Verify that Super Over deliveries never enter regulation balls or runs."""
    # Find all deliveries in super overs
    so_deliv = canonical_deliveries[canonical_deliveries['is_super_over'] == True]
    assert len(so_deliv) == 38
    
    # Check that total primary legal balls across all players exactly matches primary regular legal balls
    primary_reg = canonical_deliveries[(canonical_deliveries['is_primary_scope'] == True) & (canonical_deliveries['is_super_over'] == False)]
    expected_legal_balls = int(primary_reg['is_legal_ball'].sum())
    actual_legal_balls = int(player_metrics['legal_balls_bowled'].sum())
    assert actual_legal_balls == expected_legal_balls, f"Mismatch in total legal balls: {actual_legal_balls} vs {expected_legal_balls}"

def test_emerging_only_players_cannot_receive_official_ranks(player_metrics, canonical_deliveries):
    """Emerging-only players must never receive an official IPL/T20I rank."""
    df_prim = canonical_deliveries[(canonical_deliveries['is_primary_scope'] == True) & (canonical_deliveries['is_super_over'] == False)]
    prim_players = set(df_prim['striker_id'].unique()).union(set(df_prim['bowler_id'].unique()))
    
    df_emg = canonical_deliveries[(canonical_deliveries['is_primary_scope'] == False) & (canonical_deliveries['is_super_over'] == False)]
    emg_players = set(df_emg['striker_id'].unique()).union(set(df_emg['bowler_id'].unique()))
    
    emerging_only_ids = emg_players - prim_players
    assert len(emerging_only_ids) == 67, f"Expected 67 emerging-only players, got {len(emerging_only_ids)}"
    
    emg_only_metrics = player_metrics[player_metrics['player_id'].isin(emerging_only_ids)]
    assert (emg_only_metrics['batting_ranking_eligible'] == False).all()
    assert (emg_only_metrics['bowling_ranking_eligible'] == False).all()
    assert emg_only_metrics['batting_official_rank'].isna().all()
    assert emg_only_metrics['bowling_official_rank'].isna().all()
    assert emg_only_metrics['batting_rating'].isna().all()
    assert emg_only_metrics['bowling_rating'].isna().all()

# =========================================================================
# B. CRICKET SCORING CALCULATION TESTS
# =========================================================================

def test_fin_allen_integrity(player_metrics, client):
    """Diagnostic Test: Fin Allen (4847) must have 0 balls bowled and null economy."""
    fin = player_metrics[player_metrics['player_id'] == 4847].iloc[0]
    
    assert fin['player_name'] == 'Finn Allen'
    assert fin['legal_balls_bowled'] == 0
    assert fin['bowler_wickets'] == 0
    assert pd.isna(fin['bowling_econ']), f"Finn Allen bowling_econ must be NaN, got {fin['bowling_econ']}"
    assert pd.isna(fin['bowling_sr']), f"Finn Allen bowling_sr must be NaN, got {fin['bowling_sr']}"
    assert pd.isna(fin['bowling_avg']), f"Finn Allen bowling_avg must be NaN, got {fin['bowling_avg']}"
    assert pd.isna(fin['bowling_rating']), "Finn Allen bowling_rating must be NaN"
    assert pd.isna(fin['bowling_official_rank']), "Finn Allen bowling_official_rank must be NaN"
    assert fin['bowling_ranking_eligible'] == False
    
    # Batting remains intact
    assert fin['balls_faced'] == 829
    assert fin['batting_ranking_eligible'] == True
    assert fin['batting_official_rank'] == 1.0

    # API test for Fin Allen
    res = client.get("/api/v1/players/4847/profile")
    assert res.status_code == 200
    data = res.json()
    assert data['summary']['bowling_econ'] is None, f"API bowling_econ should be null, got {data['summary']['bowling_econ']}"
    assert data['career_stats']['economy'] is None, f"API career economy should be null, got {data['career_stats']['economy']}"
    assert data['career_stats']['balls_bowled'] == 0
    assert data['career_stats']['wickets'] == 0

def test_bowling_economy_formula_positive_balls(player_metrics):
    """Positive legal balls must match exact cricket economy formula: (runs * 6) / balls."""
    bowlers = player_metrics[player_metrics['legal_balls_bowled'] > 0]
    assert len(bowlers) == 596
    
    expected_econ = (bowlers['runs_conceded'] * 6.0) / bowlers['legal_balls_bowled']
    diff = np.abs(bowlers['bowling_econ'] - expected_econ).max()
    assert diff < 1e-9, f"Max difference in economy rate: {diff}"

def test_wides_and_noballs_not_in_legal_balls(canonical_deliveries):
    """Wides and no-balls must not increment legal balls bowled."""
    primary_reg = canonical_deliveries[(canonical_deliveries['is_primary_scope'] == True) & (canonical_deliveries['is_super_over'] == False)]
    
    # Wides have is_legal_ball == False
    wides = primary_reg[primary_reg['extras_wide_runs'] > 0]
    assert (wides['is_legal_ball'] == False).all()
    
    # No-balls have is_legal_ball == False
    noballs = primary_reg[primary_reg['extras_noball_runs'] > 0]
    assert (noballs['is_legal_ball'] == False).all()

def test_byes_and_legbyes_excluded_from_bowler_runs(canonical_deliveries):
    """Byes and leg-byes must not be charged against the bowler."""
    primary_reg = canonical_deliveries[(canonical_deliveries['is_primary_scope'] == True) & (canonical_deliveries['is_super_over'] == False)]
    expected_conceded = primary_reg['batter_runs'] + primary_reg['extras_wide_runs'] + primary_reg['extras_noball_runs']
    assert (expected_conceded == primary_reg['bowler_conceded_runs']).all()

def test_non_bowler_wickets_excluded(canonical_deliveries):
    """Run outs and non-bowler wickets must not be credited as bowler wickets."""
    primary_reg = canonical_deliveries[(canonical_deliveries['is_primary_scope'] == True) & (canonical_deliveries['is_super_over'] == False)]
    bowler_wkts = primary_reg[primary_reg['is_bowler_wicket'] == True]
    assert set(bowler_wkts['dismissal_type'].unique()).issubset({'Caught', 'Bowled', 'LBW', 'Stump', 'Hit Wicket'})

# =========================================================================
# C. POPULATION-WIDE INVARIANTS
# =========================================================================

def test_population_reconciliation(player_metrics, dim_players):
    """All 1,217 players in dim_player must reconcile with fact_player_metrics."""
    assert len(dim_players) == 1217
    assert len(player_metrics) == 1217
    assert set(dim_players['player_id']) == set(player_metrics['player_id'])

def test_all_zero_ball_bowlers_have_null_economy(player_metrics):
    """Every player with 0 legal balls must have NaN bowling economy."""
    zero_balls = player_metrics[player_metrics['legal_balls_bowled'] == 0]
    assert len(zero_balls) == 621
    assert zero_balls['bowling_econ'].isna().all()
    assert zero_balls['bowling_sr'].isna().all()
    assert zero_balls['bowling_avg'].isna().all()

def test_all_zero_ball_batters_have_null_sr(player_metrics):
    """Every player with 0 balls faced must have NaN batting strike rate."""
    zero_bat = player_metrics[player_metrics['balls_faced'] == 0]
    assert len(zero_bat) == 393
    assert zero_bat['batting_sr'].isna().all()
    assert zero_bat['batting_avg'].isna().all()

def test_leaderboard_contains_only_eligible_players(client):
    """Official leaderboards must only return eligible players with valid ranks."""
    # Batting
    res_bat = client.get("/api/v1/rankings?category=batters&limit=20")
    assert res_bat.status_code == 200
    bat_items = res_bat.json()
    assert len(bat_items) == 20
    for item in bat_items:
        assert item['batting_official_rank'] is not None
        assert item['batting_rating'] is not None
        assert item['balls_faced'] >= 60

    # Bowling
    res_bowl = client.get("/api/v1/rankings?category=bowlers&limit=20")
    assert res_bowl.status_code == 200
    bowl_items = res_bowl.json()
    assert len(bowl_items) == 20
    for item in bowl_items:
        assert item['bowling_official_rank'] is not None
        assert item['bowling_rating'] is not None
        assert item['legal_balls_bowled'] >= 30
        assert item['bowling_econ'] is not None

def test_comparison_endpoint_handles_zero_balls_cleanly(client):
    """Comparing a pure batter (Fin Allen) and pure bowler (Bumrah) returns clean nulls."""
    # Finn Allen: 4847, Jasprit Bumrah: 2933
    res = client.post("/api/v1/players/compare", json={"player_ids": [4847, 2933]})
    assert res.status_code == 200
    data = res.json()
    players = {p['player_id']: p for p in data['players']}
    
    # Finn Allen: pure batter
    fa = players[4847]
    assert fa['bowling_econ'] is None
    assert fa['overall_bowling_rating'] is None
    assert fa['bowling_ranking_eligible'] == False
    assert fa['batting_ranking_eligible'] == True
    
    # Jasprit Bumrah: bowler
    jb = players[2933]
    assert jb['bowling_econ'] is not None
    assert jb['bowling_ranking_eligible'] == True
