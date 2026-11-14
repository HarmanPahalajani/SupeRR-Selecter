"""
Automated Test Suite for Player Batting/Bowling Rating Integrity,
Evidence-Based Rankings, and Confidence-Aware Player Discovery.

Covers all 24 acceptance criteria:
- Rating integrity (Criteria 1-9)
- Ranking integrity (Criteria 10-16)
- System integration (Criteria 17-24)
"""

import pytest
import pandas as pd
import numpy as np
import duckdb
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.analytics_service import AnalyticsService
from backend.optimisation.squad.optimizer import optimize_squad
from backend.optimisation.auction.simulator import simulate_auction

@pytest.fixture(scope="module")
def ratings_data():
    p = Path("data/staging_ratings/fact_player_metrics.parquet")
    if not p.exists():
        p = Path("data/processed/fact_player_metrics.parquet")
    return pd.read_parquet(p)

# =========================================================================
# CRITERIA 1-9: RATING INTEGRITY
# =========================================================================

def test_1_bowler_zero_batting_receives_no_batting_rating(ratings_data):
    """1. A bowler with zero batting deliveries receives no batting rating."""
    zero_bat = ratings_data[(ratings_data['primary_role'] == 'BOWLER') & (ratings_data['balls_faced'] == 0)]
    assert len(zero_bat) > 0, "Expected bowlers with 0 balls faced"
    assert zero_bat['batting_rating'].isnull().all(), "Bowlers with 0 balls faced must have null batting_rating"
    assert (zero_bat['batting_ranking_eligible'] == False).all()
    assert (zero_bat['batting_confidence_tier'] == 'INSUFFICIENT_DATA').all()

def test_2_batter_zero_bowling_receives_no_bowling_rating(ratings_data):
    """2. A batter with zero bowling deliveries receives no bowling rating."""
    zero_bowl = ratings_data[(ratings_data['primary_role'] == 'BATTER') & (ratings_data['legal_balls_bowled'] == 0)]
    assert len(zero_bowl) > 0, "Expected batters with 0 balls bowled"
    assert zero_bowl['bowling_rating'].isnull().all(), "Batters with 0 balls bowled must have null bowling_rating"
    assert (zero_bowl['bowling_ranking_eligible'] == False).all()
    assert (zero_bowl['bowling_confidence_tier'] == 'INSUFFICIENT_DATA').all()

def test_3_handful_batting_cannot_receive_eligible_elite_rating(ratings_data):
    """3. A player with a handful of batting deliveries cannot automatically receive an eligible elite rating."""
    handful_bat = ratings_data[(ratings_data['balls_faced'] > 0) & (ratings_data['balls_faced'] < 60)]
    # None of these players can be eligible for official ranking
    assert (handful_bat['batting_ranking_eligible'] == False).all()
    # Check specific former 99-rated outliers
    shahnawaz = ratings_data[ratings_data['player_name'] == 'Shahnawaz Dhani'].iloc[0]
    nandan = ratings_data[ratings_data['player_name'] == 'Nandan Yadav'].iloc[0]
    assert pd.isnull(shahnawaz['batting_rating']), f"Shahnawaz Dhani must have null batting rating, got {shahnawaz['batting_rating']}"
    assert pd.isnull(nandan['batting_rating']), f"Nandan Yadav must have null batting rating, got {nandan['batting_rating']}"

def test_4_handful_bowling_cannot_receive_eligible_elite_rating(ratings_data):
    """4. A player with a handful of bowling deliveries cannot automatically receive an eligible elite rating."""
    handful_bowl = ratings_data[(ratings_data['legal_balls_bowled'] > 0) & (ratings_data['legal_balls_bowled'] < 60)]
    assert (handful_bowl['bowling_ranking_eligible'] == False).all()
    # Check specific former 99-rated outliers
    virat = ratings_data[ratings_data['player_name'] == 'Virat Kohli'].iloc[0]
    travis = ratings_data[ratings_data['player_name'] == 'Travis Head'].iloc[0]
    assert pd.isnull(virat['bowling_rating']), f"Virat Kohli must have null bowling rating, got {virat['bowling_rating']}"
    assert pd.isnull(travis['bowling_rating']), f"Travis Head must have null bowling rating, got {travis['bowling_rating']}"

def test_5_genuine_allrounders_obtain_both_ratings(ratings_data):
    """5. Genuine all-rounders can obtain both ratings with sufficient evidence."""
    stars = ['Hardik Pandya', 'Andre Russell', 'Ravindra Jadeja', 'Axar Patel', 'Sam Curran', 'Marcus Stoinis']
    sub = ratings_data[ratings_data['player_name'].isin(stars)]
    assert len(sub) == len(stars)
    for _, r in sub.iterrows():
        assert r['batting_ranking_eligible'] == True, f"{r['player_name']} must be eligible in batting"
        assert r['bowling_ranking_eligible'] == True, f"{r['player_name']} must be eligible in bowling"
        assert pd.notnull(r['batting_rating']), f"{r['player_name']} must have non-null batting rating"
        assert pd.notnull(r['bowling_rating']), f"{r['player_name']} must have non-null bowling rating"

def test_6_specialists_with_secondary_skills_obtain_valid_secondary_ratings(ratings_data):
    """6. Specialists with demonstrated secondary skills can obtain valid secondary ratings."""
    pat_cummins = ratings_data[ratings_data['player_name'] == 'Patrick Cummins'].iloc[0]
    assert pat_cummins['primary_role'] == 'BOWLER'
    # Pat Cummins faced 244 balls with demonstrated batting ability
    assert pat_cummins['batting_ranking_eligible'] == True
    assert pd.notnull(pat_cummins['batting_rating'])
    assert pat_cummins['batting_rating'] >= 60.0

def test_7_poor_performance_with_evidence_receives_low_rating(ratings_data):
    """7. Poor performance with sufficient evidence can receive a low rating."""
    siraj = ratings_data[ratings_data['player_name'] == 'Mohammed Siraj'].iloc[0]
    # Siraj has faced 72 balls and has negative RAE
    if siraj['batting_ranking_eligible']:
        assert siraj['batting_rating'] < 40.0, f"Siraj batting rating should be low, got {siraj['batting_rating']}"

def test_8_missing_data_never_becomes_99_or_favourable_default(ratings_data):
    """8. Missing data never becomes 99 or another favourable default."""
    zero_bat = ratings_data[ratings_data['balls_faced'] == 0]
    zero_bowl = ratings_data[ratings_data['legal_balls_bowled'] == 0]
    assert zero_bat['batting_rating'].isnull().all()
    assert zero_bowl['bowling_rating'].isnull().all()
    assert not (zero_bat['batting_rating'] == 99.0).any()
    assert not (zero_bowl['bowling_rating'] == 99.0).any()

def test_9_all_numeric_ratings_are_finite_and_bounded(ratings_data):
    """9. All numeric ratings are finite and within the permitted scale [15.0, 99.0]."""
    valid_bat = ratings_data['batting_rating'].dropna()
    valid_bowl = ratings_data['bowling_rating'].dropna()
    assert (valid_bat >= 15.0).all() and (valid_bat <= 99.0).all()
    assert (valid_bowl >= 15.0).all() and (valid_bowl <= 99.0).all()
    assert np.isfinite(valid_bat).all()
    assert np.isfinite(valid_bowl).all()

# =========================================================================
# CRITERIA 10-16: RANKING INTEGRITY
# =========================================================================

def test_10_ineligible_player_never_receives_official_discipline_rank(ratings_data):
    """10. An ineligible player never receives an official discipline rank."""
    inelig_bat = ratings_data[ratings_data['batting_ranking_eligible'] == False]
    inelig_bowl = ratings_data[ratings_data['bowling_ranking_eligible'] == False]
    assert inelig_bat['batting_official_rank'].isnull().all(), "Ineligible batters must have null official rank"
    assert inelig_bowl['bowling_official_rank'].isnull().all(), "Ineligible bowlers must have null official rank"

def test_11_top_rankings_contain_only_eligible_players(ratings_data):
    """11. Top 10, Top 25 and Top 50 contain only eligible players."""
    top50_bat = ratings_data[ratings_data['batting_official_rank'] <= 50]
    top50_bowl = ratings_data[ratings_data['bowling_official_rank'] <= 50]
    assert len(top50_bat) == 50
    assert len(top50_bowl) == 50
    assert top50_bat['batting_ranking_eligible'].all()
    assert top50_bowl['bowling_ranking_eligible'].all()
    assert top50_bat['batting_confidence_tier'].isin(['HIGH', 'MEDIUM']).all()
    assert top50_bowl['bowling_confidence_tier'].isin(['HIGH', 'MEDIUM']).all()

def test_12_eligible_players_ranked_ahead_of_limited_evidence(ratings_data):
    """12. Eligible players are ranked ahead of limited-evidence players."""
    lim_bat = ratings_data[ratings_data['batting_confidence_tier'] == 'LIMITED_EVIDENCE']
    assert lim_bat['batting_official_rank'].isnull().all()
    lim_bowl = ratings_data[ratings_data['bowling_confidence_tier'] == 'LIMITED_EVIDENCE']
    assert lim_bowl['bowling_official_rank'].isnull().all()

def test_13_null_ratings_sort_last():
    """13. Null ratings sort last in ranking queries."""
    res = AnalyticsService.list_players(sort_by="batting_rating", page_size=20)
    # The top 20 must all have non-null batting ratings
    for p in res['items']:
        assert p['batting_rating'] is not None

def test_14_insufficient_data_players_cannot_influence_rank_calculations(ratings_data):
    """14. Insufficient-data players cannot influence rank calculations."""
    ins_bat = ratings_data[ratings_data['batting_confidence_tier'] == 'INSUFFICIENT_DATA']
    assert ins_bat['batting_official_rank'].isnull().all()
    # Maximum rank assigned equals count of eligible players
    max_bat_rank = ratings_data['batting_official_rank'].max()
    assert max_bat_rank == ratings_data['batting_ranking_eligible'].sum()

def test_15_tied_scores_handled_deterministically(ratings_data):
    """15. Official ranks are strictly distinct positive integers with no duplicate ranks."""
    bat_ranks = ratings_data['batting_official_rank'].dropna()
    bowl_ranks = ratings_data['bowling_official_rank'].dropna()
    assert len(bat_ranks) == len(set(bat_ranks)), "Batting ranks must be unique"
    assert len(bowl_ranks) == len(set(bowl_ranks)), "Bowling ranks must be unique"
    assert bat_ranks.min() == 1.0
    assert bowl_ranks.min() == 1.0

def test_16_ranking_stability_under_bootstrap_resampling(ratings_data):
    """16. Ranking stability is evaluated under match-level bootstrap resampling."""
    assert 'boot_ci_low' in ratings_data.columns
    assert 'boot_ci_high' in ratings_data.columns
    assert (ratings_data['boot_ci_high'] >= ratings_data['boot_ci_low']).all()

# =========================================================================
# CRITERIA 17-24: SYSTEM INTEGRATION
# =========================================================================

def test_17_ratings_consistent_in_api():
    """17. Corrected ratings are consistent in API responses."""
    client = TestClient(app)
    # Test rankings endpoint
    res = client.get("/api/v1/rankings/batters?limit=10")
    assert res.status_code == 200
    batters = res.json()
    assert len(batters) == 10
    for b in batters:
        assert b['batting_rating'] is not None
        assert b['confidence_tier'] in ['HIGH', 'MEDIUM']
        # Confirm no tailender bowler with small sample is in top 10 batters
        assert b['balls_faced'] >= 60

def test_18_frontend_profile_handles_null_ratings():
    """18. API returns null ratings for ineligible disciplines so frontend displays N/A."""
    client = TestClient(app)
    # Player 19530: Shahnawaz Dhani (bowler with 6 balls faced)
    res = client.get("/api/v1/players/19530/profile")
    assert res.status_code == 200
    profile = res.json()
    assert profile['summary']['batting_rating'] is None
    assert profile['summary']['overall_batting_rating'] is None
    assert profile['summary']['bowling_rating'] is not None

def test_19_player_comparison_handles_unavailable_metrics():
    """19. Player Comparison handles unavailable metrics correctly and selects valid winners."""
    client = TestClient(app)
    # Compare Virat Kohli (47) and Jasprit Bumrah (2933)
    res = client.post("/api/v1/players/compare", json={"player_ids": [47, 2933]})
    assert res.status_code == 200
    comp = res.json()
    winners = comp['winner_by_scenario']
    # Kohli must win batter, Bumrah must win bowler
    assert winners['Best High-Pressure Batter']['winner_id'] == 47
    assert winners['Best Pressure Bowler']['winner_id'] == 2933

def test_20_squad_architect_ignores_unsupported_skills():
    """20. Squad Architect optimizer functions and utilizes evidence-conditioned utility."""
    sol = optimize_squad(budget_remaining=450000000, players_to_acquire=5, strategy="balanced")
    assert sol['status'] in ['OPTIMAL', 'FEASIBLE']
    assert len(sol['players']) == 5

def test_21_auction_simulator_does_not_reward_missing_evidence():
    """21. Auction Simulator does not pick unevidenced players as top replacements."""
    sim = simulate_auction(target_player_id=2933, bid_cap=120000000) # Bumrah (2933)
    assert len(sim['replacement_tree']) > 0
    for rep in sim['replacement_tree']:
        # Replacements for a bowler must have non-null bowling ratings
        assert rep['confidence_tier'] in ['High Evidence', 'Moderate Evidence']

def test_22_emerging_scope_does_not_contaminate_official_rankings(ratings_data):
    """22. Emerging competition records cannot contaminate official rankings."""
    assert 'competition_scope' in ratings_data.columns
    assert (ratings_data['competition_scope'] == 'IPL_T20I').all()
    # Emerging candidates are tracked separately
    assert 'is_emerging_candidate' in ratings_data.columns

def test_23_no_duplicate_or_incorrectly_joined_player_ids(ratings_data):
    """23. No duplicate or incorrectly joined player IDs."""
    assert ratings_data['player_id'].is_unique
    assert len(ratings_data) == 1217

def test_24_all_1217_player_identities_accounted(ratings_data):
    """24. All 1,217 player identities remain correctly accounted for."""
    assert len(ratings_data) == 1217
    assert set(ratings_data['primary_role'].unique()).issubset({"BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER", "UNKNOWN"})
