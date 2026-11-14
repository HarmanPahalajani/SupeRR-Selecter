import pytest
import pandas as pd
from backend.analytics.ranking.roles import classify_player_roles
from backend.optimisation.squad.optimizer import optimize_squad
from backend.app.services.analytics_service import AnalyticsService

@pytest.fixture(scope="module")
def classified_data():
    return pd.read_parquet("data/processed/fact_player_metrics.parquet")

def test_single_mutually_exclusive_role(classified_data):
    """1. Every player has exactly one primary role from the valid set."""
    valid_roles = {"BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER", "UNKNOWN"}
    assigned_roles = set(classified_data["primary_role"].unique())
    assert assigned_roles.issubset(valid_roles)
    assert not classified_data["primary_role"].isnull().any()

def test_total_player_count_invariance(classified_data):
    """2. The sum across mutually exclusive primary categories equals the unique player count (1217)."""
    role_counts = classified_data["primary_role"].value_counts()
    assert role_counts.sum() == 1217
    assert len(classified_data["player_id"].unique()) == 1217

def test_no_duplicate_players_across_categories(classified_data):
    """3. No player appears twice in primary role categories."""
    assert classified_data["player_id"].is_unique

def test_verified_wicketkeepers_identified(classified_data):
    """4. Verified playing XI wicketkeepers are accurately classified."""
    # Sanju Samson, MS Dhoni, Rishabh Pant, Jos Buttler, Heinrich Klaasen
    known_wks = [2258, 2, 4703, 813, 4260] # check by ID or name
    wk_names = ["Sanju Samson", "Mahendra Singh Dhoni", "Rishabh Pant", "Jos Buttler", "Heinrich Klaasen", "Nicholas Pooran"]
    sub = classified_data[classified_data["player_name"].isin(wk_names)]
    for _, r in sub.iterrows():
        assert r["primary_role"] == "WICKETKEEPER", f"Failed for {r['player_name']}: got {r['primary_role']}"

def test_occasional_bowlers_not_allrounders(classified_data):
    """5. Occasional/part-time bowlers are NOT classified as all-rounders."""
    part_timers = ["Virat Kohli", "Suryakumar Yadav", "Shreyas Iyer", "Rohit Sharma"]
    sub = classified_data[classified_data["player_name"].isin(part_timers)]
    for _, r in sub.iterrows():
        assert r["primary_role"] == "BATTER", f"Part-timer {r['player_name']} incorrectly classified as {r['primary_role']}"

def test_genuine_allrounders_identified(classified_data):
    """6. Players with genuine batting and bowling responsibilities are correctly identified."""
    stars = ["Hardik Pandya", "Andre Russell", "Ravindra Jadeja", "Axar Patel", "Sam Curran", "Marcus Stoinis"]
    sub = classified_data[classified_data["player_name"].isin(stars)]
    for _, r in sub.iterrows():
        assert r["primary_role"] == "ALL_ROUNDER", f"All-rounder {r['player_name']} incorrectly classified as {r['primary_role']}"

def test_pure_bowlers_identified(classified_data):
    """Verified specialist bowlers with batting exposure remain bowlers."""
    bowlers = ["Jasprit Bumrah", "Yuzvendra Chahal", "Arshdeep Singh", "Mohammed Siraj", "Ravi Bishnoi"]
    sub = classified_data[classified_data["player_name"].isin(bowlers)]
    for _, r in sub.iterrows():
        assert r["primary_role"] == "BOWLER", f"Bowler {r['player_name']} incorrectly classified as {r['primary_role']}"

def test_format_specific_roles(classified_data):
    """7. Format-specific roles exist and correctly capture competition activity."""
    assert "ipl_primary_role" in classified_data.columns
    assert "t20i_primary_role" in classified_data.columns
    # Check that players with no IPL appearances get UNKNOWN for ipl_primary_role
    no_ipl = classified_data[classified_data["p11_ipl_matches"] == 0]
    assert (no_ipl["ipl_primary_role"] == "UNKNOWN").all()

def test_player_discovery_filtering():
    """8. Player Discovery service returns exact category subsets."""
    batters = AnalyticsService.list_players(role="BATTER", page_size=100)
    assert len(batters["items"]) > 0
    for p in batters["items"]:
        assert p["primary_role"] == "BATTER"

    bowlers = AnalyticsService.list_players(role="BOWLER", page_size=100)
    assert len(bowlers["items"]) > 0
    for p in bowlers["items"]:
        assert p["primary_role"] == "BOWLER"

    wks = AnalyticsService.list_players(role="WICKETKEEPER", page_size=100)
    assert len(wks["items"]) > 0
    for p in wks["items"]:
        assert p["primary_role"] == "WICKETKEEPER"

def test_squad_architect_receives_correct_roles():
    """9. Squad Architect CP-SAT optimizer receives and balances corrected roles."""
    sol = optimize_squad(budget_remaining=400000000, players_to_acquire=5, strategy="balanced")
    assert sol["status"] in ["OPTIMAL", "FEASIBLE"]
    assert len(sol["players"]) == 5
    for p in sol["players"]:
        assert p["primary_role"] in ["BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER"]
