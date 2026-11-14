import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api():
    print("=== EXECUTING COMPLETE END-TO-END WORKFLOW AUDIT ===\n")

    # Workflow 1: Search for a player
    print("Workflow 1: Searching for player 'Samson' via /players?search=Samson...")
    url = f"{BASE_URL}/players?search=Samson&page=1&page_size=10"
    req = urllib.request.urlopen(url)
    res = json.loads(req.read().decode())
    print(f"  Found {res['total']} results. First: {res['items'][0]['player_name']} (ID: {res['items'][0]['player_id']})")
    assert len(res['items']) > 0
    target_player_id = res['items'][0]['player_id']

    # Workflow 2: Open complete intelligence profile
    print(f"\nWorkflow 2: Fetching complete intelligence profile for Player ID {target_player_id}...")
    url = f"{BASE_URL}/players/{target_player_id}/profile"
    req = urllib.request.urlopen(url)
    profile = json.loads(req.read().decode())
    summary = profile['summary']
    print(f"  Name: {summary['player_name']} | Role: {summary['primary_role']}")
    print(f"  Career Stats -> Runs: {profile['career_stats']['runs']}, SR: {profile['career_stats']['strike_rate']:.2f}")
    print(f"  Recruitment Verdict: {profile['recruitment_verdict']['recommendation']} (Evidence: {profile['recruitment_verdict']['evidence_strength']})")
    print(f"  Pressure Stats -> Pressure RAE/ball: {profile['pressure_stats']['pressure_rae_per_ball']:.3f}")
    assert summary['player_id'] == target_player_id

    # Workflow 3: Compare multiple players
    print("\nWorkflow 3: Comparing multiple players (Sanju Samson vs Heinrich Klaasen)...")
    url = f"{BASE_URL}/players?search=Klaasen&page=1&page_size=5"
    req = urllib.request.urlopen(url)
    klaasen_id = json.loads(req.read().decode())['items'][0]['player_id']
    comp_url = f"{BASE_URL}/players/compare"
    payload = json.dumps({"player_ids": [target_player_id, klaasen_id]}).encode('utf-8')
    req = urllib.request.Request(comp_url, data=payload, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    comp_res = json.loads(resp.read().decode())
    print(f"  Compared {len(comp_res['players'])} players: {[p['player_name'] for p in comp_res['players']]}")
    print(f"  Winner by scenario: {comp_res['winner_by_scenario']}")
    assert len(comp_res['players']) == 2

    # Workflow 4: Find undervalued statistical opportunities
    print("\nWorkflow 4: Finding undervalued statistical opportunities (Discovery Gap)...")
    disc_url = f"{BASE_URL}/discovery/undervalued"
    req = urllib.request.urlopen(disc_url)
    undervalued = json.loads(req.read().decode())
    print(f"  Total qualified undervalued talents returned: {len(undervalued)}")
    for t in undervalued[:3]:
        print(f"  - {t['player_name']} ({t['primary_role']}): Avg {t['batting_avg']:.1f}, SR {t['batting_sr']:.1f} -> EB Impact {t['eb_batting_impact']:.3f} (Discovery Gap: +{t['discovery_gap']:.1f})")
    assert len(undervalued) > 0

    # Workflow 5: Generate all three squad strategies
    print("\nWorkflow 5: Generating all three squad strategies via /squads/optimise...")
    post_data = json.dumps({"budget_remaining": 400000000, "players_to_acquire": 5}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/squads/optimise", data=post_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    squad_res = json.loads(resp.read().decode())
    print(f"  Overall Optimiser Status: {squad_res['status']}")
    for strat in ["balanced", "upside", "risk_controlled"]:
        s = squad_res['strategies'][strat]
        print(f"  Strategy: '{strat}' -> Status: {s['status']} | Squad Size: {len(s['players'])} | Spend: ₹{s['total_spend']/10000000:.2f} Cr")
        assert s['status'] in ["OPTIMAL", "FEASIBLE"]
        assert len(s['players']) == 5

    # Workflow 6: Remove selected player and verify genuine re-optimisation
    print("\nWorkflow 6: What-if Re-optimisation (Excluding top pick)...")
    balanced_players = squad_res['strategies']['balanced']['players']
    first_pick_id = balanced_players[0]['player_id']
    first_pick_name = balanced_players[0]['player_name']
    post_data = json.dumps({"budget_remaining": 400000000, "players_to_acquire": 5, "excluded_player_ids": [first_pick_id]}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/squads/optimise", data=post_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    reopt_res = json.loads(resp.read().decode())
    reopt_player_ids = [p['player_id'] for p in reopt_res['strategies']['balanced']['players']]
    print(f"  Excluded: {first_pick_name} (ID: {first_pick_id})")
    print(f"  Re-optimized squad contains excluded player? {first_pick_id in reopt_player_ids}")
    assert first_pick_id not in reopt_player_ids, "Excluded player was not removed during re-optimization!"

    # Workflow 7: Run Monte Carlo auction simulation
    print("\nWorkflow 7: Running Monte Carlo auction simulation...")
    post_data = json.dumps({
        "target_player_id": target_player_id,
        "bid_cap": 30000000,
        "user_budget": 100000000,
        "n_simulations": 100
    }).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/auction/simulate", data=post_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    auc_res = json.loads(resp.read().decode())
    print(f"  Simulation completed: Win probability = {auc_res['win_probability']*100:.1f}%, Expected Spend If Won = ₹{auc_res['expected_expenditure_if_won']/10000000:.2f} Cr, Risk of Overspend = {auc_res['risk_of_exceeding_budget']*100:.1f}%")
    print(f"  Replacement targets suggested: {[r['player_name'] for r in auc_res['replacement_tree']]}")
    assert 0.0 <= auc_res['win_probability'] <= 1.0
    assert len(auc_res['bid_curve']) > 0

    # Workflow 8: Save and retrieve a watchlist entry
    print("\nWorkflow 8: Testing Watchlist persistence workflow...")
    # Create watchlist
    wl_post = json.dumps({"name": "Audit Verification Watchlist", "description": "Release readiness verification list"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/watchlists", data=wl_post, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    wid = json.loads(resp.read().decode())["watchlist_id"]

    # Add player to watchlist
    add_post = json.dumps({"player_id": target_player_id, "priority": "High", "target_role": "top_order"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/watchlists/{wid}/players", data=add_post, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200

    # Add scouting note
    note_post = json.dumps({"content": "High pressure chase anchor and elite pace hitter.", "verdict": "Shortlist"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/watchlists/notes/{target_player_id}", data=note_post, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200

    # Retrieve notes
    req = urllib.request.urlopen(f"{BASE_URL}/watchlists/notes/{target_player_id}")
    notes_get = json.loads(req.read().decode())
    print(f"  Retrieved {len(notes_get)} notes for Player {target_player_id}. Latest: '{notes_get[-1]['content']}' (Verdict: {notes_get[-1]['verdict']})")
    assert len(notes_get) > 0

    # Workflow 9: Inspect the methodology and validation centre
    print("\nWorkflow 9: Inspecting Methodology & Validation Centre data...")
    req = urllib.request.urlopen(f"{BASE_URL}/meta/coverage")
    cov = json.loads(req.read().decode())
    print(f"  Coverage meta loaded: {cov['total_deliveries']} total deliveries, {cov['unique_players']} players.")

    print("\n>>> ALL 9 END-TO-END WORKFLOWS VERIFIED 100% FUNCTIONAL AND PASSING! <<<")

if __name__ == "__main__":
    test_api()
