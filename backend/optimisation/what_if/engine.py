from backend.optimisation.squad.optimizer import optimize_squad

def run_what_if_analysis(
    base_scenario: dict,
    exclude_player_id: int = None,
    lock_player_id: int = None,
    new_budget: int = None,
    new_strategy: str = None
):
    """
    Reruns true CP-SAT optimization with modified constraints.
    Returns previous vs updated squad, replacements, and utility delta.
    """
    # Run base
    base_sol = optimize_squad(
        budget_remaining=base_scenario.get("budget_remaining", 450000000),
        players_to_acquire=base_scenario.get("players_to_acquire", 5),
        locked_player_ids=base_scenario.get("locked_player_ids", []),
        excluded_player_ids=base_scenario.get("excluded_player_ids", []),
        strategy=base_scenario.get("strategy", "balanced"),
        role_requirements=base_scenario.get("role_requirements", None)
    )

    # Update inputs for what-if
    updated_locked = list(base_scenario.get("locked_player_ids", []))
    updated_excluded = list(base_scenario.get("excluded_player_ids", []))
    
    if exclude_player_id:
        updated_excluded.append(exclude_player_id)
        if exclude_player_id in updated_locked:
            updated_locked.remove(exclude_player_id)
    if lock_player_id:
        updated_locked.append(lock_player_id)
        if lock_player_id in updated_excluded:
            updated_excluded.remove(lock_player_id)

    updated_budget = new_budget if new_budget is not None else base_scenario.get("budget_remaining", 450000000)
    updated_strat = new_strategy if new_strategy is not None else base_scenario.get("strategy", "balanced")

    # Run what-if re-optimization
    updated_sol = optimize_squad(
        budget_remaining=updated_budget,
        players_to_acquire=base_scenario.get("players_to_acquire", 5),
        locked_player_ids=updated_locked,
        excluded_player_ids=updated_excluded,
        strategy=updated_strat,
        role_requirements=base_scenario.get("role_requirements", None)
    )

    # Compare squads
    base_ids = set(p['player_id'] for p in base_sol.get('players', []))
    new_ids = set(p['player_id'] for p in updated_sol.get('players', []))

    removed_players = [p for p in base_sol.get('players', []) if p['player_id'] not in new_ids]
    added_replacements = [p for p in updated_sol.get('players', []) if p['player_id'] not in base_ids]

    base_util = sum(p['utility_score'] for p in base_sol.get('players', []))
    new_util = sum(p['utility_score'] for p in updated_sol.get('players', []))

    return {
        "status": updated_sol.get('status'),
        "base_solution": base_sol,
        "updated_solution": updated_sol,
        "delta": {
            "utility_delta": new_util - base_util,
            "spend_delta": updated_sol.get('total_spend', 0) - base_sol.get('total_spend', 0),
            "removed_players": removed_players,
            "recommended_replacements": added_replacements
        }
    }
