"""
Pressure Performer Intelligence — Regression & Integrity Tests
Part of SupeRR Intelligence — Unified Pressure Performer Intelligence

Validates:
1. Canonical dynamic pressure lineage and delivery tagging
2. First-innings and chase pressure definitions
3. Runs Above Expected (RAE) calculation
4. Unified evidence-aware ranking without artificial category tiers
5. Non-exclusion of lesser-known players (Akeal Hosein, Ijaz Ahmadzai, etc.)
6. Appropriate unranked handling for sparse samples and negative performers
7. Scope isolation between Primary (IPL, T20I, Combined) and Emerging
8. API endpoints and discovery metrics
"""

import pytest
import numpy as np
import pandas as pd
import duckdb
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.analytics.pressure_performers.pressure_opportunities import tag_high_pressure_deliveries
from backend.analytics.pressure_performers.contribution import compute_delivery_contributions
from backend.analytics.pressure_performers.ranking import compute_pressure_rankings
from backend.analytics.pressure_performers.classification import (
    classify_player_record,
    STATUS_RANKED,
    STATUS_LIMITED_EVIDENCE,
    STATUS_BELOW_BASELINE,
    STATUS_INSUFFICIENT
)

client = TestClient(app)
DB_PATH = "data/app/analytics.duckdb"


# ==========================================
# 1. SCOPE & POPULATION RECONCILIATION TESTS
# ==========================================

def test_master_player_population_complete():
    """Verify all 1,217 master player identities exist in dim_player_pressure_classification."""
    con = duckdb.connect(DB_PATH, read_only=True)
    total_dim = con.execute("SELECT count(*) FROM dim_player_pressure_classification").fetchone()[0]
    distinct_dim = con.execute("SELECT count(distinct player_id) FROM dim_player_pressure_classification").fetchone()[0]
    con.close()
    
    assert total_dim == 1217, f"Expected 1,217 master player records, found {total_dim}"
    assert distinct_dim == 1217, f"Expected 1,217 distinct player IDs, found {distinct_dim}"


def test_emerging_only_players_never_receive_primary_rank():
    """Verify Emerging-only players never receive an official primary competition rank."""
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT player_id, player_name, pressure_rank, classification
        FROM fact_player_pressure_metrics
        WHERE competition_scope = 'IPL_T20I' AND pressure_context = 'ALL'
          AND participation_status = 'EMERGING_ONLY'
    """).df()
    con.close()
    
    assert len(df) == 67, f"Expected 67 emerging-only players, found {len(df)}"
    for _, row in df.iterrows():
        assert row["pressure_rank"] is None or np.isnan(row["pressure_rank"]), f"Emerging-only player {row['player_name']} has primary rank"
        assert row["classification"] in (STATUS_INSUFFICIENT, "Emerging Scope Only — Not Evaluated in Primary")


def test_cross_scope_players_receive_separate_independent_records():
    """Verify dual-scope players have completely separate records for IPL_T20I and EMERGING."""
    con = duckdb.connect(DB_PATH, read_only=True)
    res = con.execute("""
        SELECT player_id, count(distinct competition_scope) as scope_count
        FROM fact_player_pressure_metrics
        WHERE pressure_context = 'ALL'
        GROUP BY player_id
        HAVING count(distinct competition_scope) > 1
    """).df()
    con.close()

    assert len(res) >= 100, f"Expected at least 100 dual-scope players, found {len(res)}"
    assert (res["scope_count"] >= 2).all()


# ==========================================
# 2. OPPORTUNITY & CONTRIBUTION LOGIC TESTS
# ==========================================

def test_high_pressure_threshold_frozen_at_75th_percentile():
    """Verify tagging applies p75 thresholds (Innings 1: 5.83, Chase: 8.60)."""
    df = pd.DataFrame({
        "match_id": [1, 2],
        "delivery_id": [101, 102],
        "innings": [1, 2],
        "pressure_index": [6.00, 8.50],
        "is_legal_ball": [1, 1],
        "batter_runs": [4, 1],
        "expected_batter_runs": [1.2, 1.1],
        "is_dismissal": [0, 0],
        "expected_wicket_prob": [0.05, 0.05]
    })
    tagged = tag_high_pressure_deliveries(df, threshold_variant="p75", is_primary=True)
    assert tagged.iloc[0]["is_high_pressure"] == True
    assert tagged.iloc[1]["is_high_pressure"] == False


def test_runs_above_expected_formula():
    """Verify RAE = actual_runs - expected_runs exactly."""
    df = pd.DataFrame({
        "match_id": [1],
        "delivery_id": [101],
        "innings": [1],
        "pressure_index": [7.0],
        "is_high_pressure": [True],
        "is_legal_ball": [1],
        "batter_runs": [6],
        "expected_batter_runs": [1.45],
        "is_dismissal": [0],
        "expected_wicket_prob": [0.04]
    })
    contrib = compute_delivery_contributions(df)
    assert pytest.approx(contrib.iloc[0]["rae"], abs=1e-5) == 6 - 1.45


def test_dismissal_attribution_to_striker():
    """Verify striker dismissals are accurately isolated from non-striker runouts."""
    df = pd.DataFrame({
        "match_id": [1, 2],
        "delivery_id": [101, 102],
        "innings": [1, 2],
        "pressure_index": [7.0, 7.0],
        "is_high_pressure": [True, True],
        "is_legal_ball": [1, 1],
        "batter_runs": [0, 1],
        "expected_batter_runs": [1.0, 1.0],
        "is_dismissal": [1, 1],
        "dismissal_kind": ["bowled", "run out"],
        "is_striker_dismissed": [1, 0],
        "expected_wicket_prob": [0.08, 0.08]
    })
    contrib = compute_delivery_contributions(df)
    assert contrib.iloc[0]["is_striker_dismissed"] == 1
    assert contrib.iloc[1]["is_striker_dismissed"] == 0


# ==========================================
# 3. UNIFIED RANKING & EVIDENCE EVALUATION TESTS
# ==========================================

def test_unified_ranking_assigns_sequential_order_to_qualified_positive_batters():
    """Verify all qualifying positive batters are ranked sequentially by CRAI."""
    df = pd.DataFrame({
        "player_id": [1, 2, 3],
        "player_name": ["Player A", "Player B", "Player C"],
        "hp_balls": [80.0, 60.0, 15.0],
        "hp_matches": [10, 8, 1],
        "hp_posterior_mean": [20.0, 16.0, 25.0],
        "hp_risk_adjusted_impact": [15.0, 11.0, 18.0],
        "hp_raw_rae_per_100": [35.0, 30.0, 60.0]
    })
    ranked = compute_pressure_rankings(df, min_balls=25, min_matches=3, is_emerging=False)
    
    # Player A and B qualify (>=25 balls, >=3 matches, post_mean > 0)
    assert ranked.loc[ranked["player_id"] == 1, "is_pressure_ranked"].values[0] == True
    assert ranked.loc[ranked["player_id"] == 1, "pressure_rank"].values[0] == 1
    
    assert ranked.loc[ranked["player_id"] == 2, "is_pressure_ranked"].values[0] == True
    assert ranked.loc[ranked["player_id"] == 2, "pressure_rank"].values[0] == 2
    
    # Player C has only 15 balls & 1 match -> unranked
    assert ranked.loc[ranked["player_id"] == 3, "is_pressure_ranked"].values[0] == False
    assert np.isnan(ranked.loc[ranked["player_id"] == 3, "pressure_rank"].values[0])


def test_sparse_evidence_remains_unranked():
    """Verify players with sparse opportunities are not given an official rank."""
    sparse_row = pd.Series({
        "hp_balls": 8.0,
        "hp_matches": 1,
        "hp_raw_rae_per_100": 30.0,
        "hp_posterior_mean": 6.0,
        "hp_risk_adjusted_impact": 2.0
    })
    cls = classify_player_record(sparse_row)
    assert cls == STATUS_LIMITED_EVIDENCE


def test_negative_performers_identified_without_artificial_tier():
    """Verify negative performers are flagged as below baseline without separate tier."""
    struggling_row = pd.Series({
        "hp_balls": 50.0,
        "hp_matches": 6,
        "hp_raw_rae_per_100": -40.0,
        "hp_posterior_mean": -20.0,
        "hp_risk_adjusted_impact": -28.0
    })
    cls = classify_player_record(struggling_row)
    assert cls == STATUS_BELOW_BASELINE


# ==========================================
# 4. TARGET AUDITED PLAYERS UNIFIED TEST
# ==========================================

def test_target_players_evaluated_consistently():
    """Verify Phil Salt, Finn Allen, Akeal Hosein, Jake McGurk, Josh Inglis, etc. on unified leaderboard."""
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT player_id, player_name, classification, hp_balls, hp_matches, hp_raw_rae_per_100, hp_posterior_mean, hp_risk_adjusted_impact, pressure_rank, is_pressure_ranked
        FROM fact_player_pressure_metrics
        WHERE competition_scope = 'IPL_T20I' AND pressure_context = 'ALL' 
          AND player_id IN (5553, 2367, 4847, 6281, 2379, 7341, 48504, 50284, 4736, 2417, 24779, 4821, 47050)
    """).df().set_index("player_name")
    con.close()
    
    # Phil Salt is #1 on Unified Leaderboard
    assert df.loc["Phil Salt", "pressure_rank"] == 1
    assert df.loc["Phil Salt", "is_pressure_ranked"] == True
    
    # Akeal Hosein has 139 pressure balls across 20 matches -> officially ranked on unified leaderboard!
    assert df.loc["Akeal Hosein", "is_pressure_ranked"] == True
    assert df.loc["Akeal Hosein", "pressure_rank"] > 0
    assert df.loc["Akeal Hosein", "hp_balls"] == 139.0
    assert df.loc["Akeal Hosein", "hp_matches"] == 20
    
    # Ijaz Ahmadzai, Travis Head, Finn Allen, Abhishek Sharma, Mahipal Lomror, Shamar Joseph are all officially ranked
    for name in ["Ijaz Ahmadzai", "Travis Head", "Finn Allen", "Abhishek Sharma", "Mahipal Lomror", "Shamar Joseph"]:
        assert df.loc[name, "is_pressure_ranked"] == True
        assert df.loc[name, "pressure_rank"] > 0
        
    # Jake McGurk (18b, 1m) has limited sample -> unranked
    assert df.loc["Jake McGurk", "is_pressure_ranked"] == False
    assert pd.isna(df.loc["Jake McGurk", "pressure_rank"])
    
    # Josh Inglis & Ben Duckett have negative situational impact -> unranked
    assert df.loc["Josh Inglis", "is_pressure_ranked"] == False
    assert df.loc["Ben Duckett", "is_pressure_ranked"] == False


# ==========================================
# 5. API ENDPOINTS INTEGRITY TESTS
# ==========================================

def test_api_leaderboard_endpoint():
    """Verify /api/v1/pressure-performers/leaderboard returns unified leaderboard."""
    response = client.get("/api/v1/pressure-performers/leaderboard?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "players" in data
    assert len(data["players"]) == 10
    first = data["players"][0]
    assert first["player_name"] == "Phil Salt"
    assert first["pressure_rank"] == 1
    assert first["is_pressure_ranked"] == True


def test_api_discovery_summary():
    """Verify /api/v1/pressure-performers/discovery returns objective leaderboard statistics."""
    response = client.get("/api/v1/pressure-performers/discovery")
    assert response.status_code == 200
    data = response.json()
    assert "total_batters_assessed" in data
    assert "positive_batters" in data
    assert "sufficient_evidence_batters" in data
    assert "total_pressure_matches" in data
    assert data["total_batters_assessed"] > 700
    assert data["positive_batters"] > 250
    assert data["sufficient_evidence_batters"] > 100
    assert data["total_pressure_matches"] > 400


def test_api_player_profile():
    """Verify /api/v1/pressure-performers/player/{player_id} returns unified pressure profile."""
    response = client.get("/api/v1/pressure-performers/player/5553")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 5553
    assert data["player_name"] == "Phil Salt"
    assert data["primary_rank"] == 1
    assert data["is_pressure_ranked"] == True
    assert "contexts" in data
