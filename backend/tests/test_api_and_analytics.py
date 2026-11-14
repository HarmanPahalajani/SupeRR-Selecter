import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.optimisation.squad.optimizer import optimize_squad
from backend.optimisation.auction.simulator import simulate_auction

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/v1/meta/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["duckdb_connected"] is True
    assert data["sqlite_connected"] is True

def test_coverage_endpoint():
    res = client.get("/api/v1/meta/coverage")
    assert res.status_code == 200
    data = res.json()
    assert data["total_deliveries"] == 200961
    assert data["primary_scope_deliveries"] == 193988
    assert data["primary_scope_matches"] == 853

def test_players_endpoint():
    res = client.get("/api/v1/players?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 10
    assert data["total"] > 500

    # Test profile of the top player
    top_pid = data["items"][0]["player_id"]
    prof_res = client.get(f"/api/v1/players/{top_pid}/profile")
    assert prof_res.status_code == 200
    prof = prof_res.json()
    assert "career_stats" in prof
    assert "pressure_stats" in prof
    assert "recruitment_verdict" in prof

def test_comparison_endpoint():
    # Pick two players
    res = client.get("/api/v1/players?page=1&page_size=2")
    p1 = res.json()["items"][0]["player_id"]
    p2 = res.json()["items"][1]["player_id"]

    comp_res = client.post("/api/v1/players/compare", json={"player_ids": [p1, p2]})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["players"]) == 2
    assert "winner_by_scenario" in comp_data

def test_rankings_endpoints():
    res_bat = client.get("/api/v1/rankings/batters?limit=10")
    assert res_bat.status_code == 200
    assert len(res_bat.json()) == 10

    res_bowl = client.get("/api/v1/rankings/bowlers?limit=10")
    assert res_bowl.status_code == 200
    assert len(res_bowl.json()) == 10

    res_undervalued = client.get("/api/v1/discovery/undervalued")
    assert res_undervalued.status_code == 200
    assert len(res_undervalued.json()) > 0

def test_squad_optimizer():
    sol = optimize_squad(
        budget_remaining=400000000,
        players_to_acquire=5,
        strategy="balanced"
    )
    assert sol["status"] in ["OPTIMAL", "FEASIBLE"]
    assert len(sol["players"]) == 5
    assert sol["total_spend"] <= 400000000

def test_auction_simulator():
    # Fetch a sample player
    res = client.get("/api/v1/players?page=1&page_size=1")
    pid = res.json()["items"][0]["player_id"]

    sim = simulate_auction(
        target_player_id=pid,
        bid_cap=30000000,
        user_budget=100000000,
        n_simulations=100
    )
    assert "win_probability" in sim
    assert 0.0 <= sim["win_probability"] <= 1.0
    assert len(sim["bid_curve"]) > 0

def test_watchlist_workflow():
    # Create watchlist
    wl_res = client.post("/api/v1/watchlists", json={"name": "Test Scout List", "description": "Automated test list"})
    assert wl_res.status_code == 200
    wid = wl_res.json()["watchlist_id"]

    # Add player
    add_res = client.post(f"/api/v1/watchlists/{wid}/players", json={"player_id": 1234, "priority": "High", "target_role": "finisher"})
    assert add_res.status_code == 200

    # Add note
    note_res = client.post("/api/v1/watchlists/notes/1234", json={"content": "Strong finisher technique.", "verdict": "Shortlist"})
    assert note_res.status_code == 200

    # Retrieve notes
    notes_get = client.get("/api/v1/watchlists/notes/1234")
    assert notes_get.status_code == 200
    assert len(notes_get.json()) > 0
