from fastapi import APIRouter
from backend.app.schemas.models import SquadOptimizeRequest, SquadWhatIfRequest
from backend.optimisation.squad.optimizer import optimize_squad
from backend.optimisation.what_if.engine import run_what_if_analysis

router = APIRouter(prefix="/squads", tags=["Squad Architect"])

@router.post("/optimise")
def run_squad_optimization(req: SquadOptimizeRequest):
    # Return 3 strategy alternatives: balanced, upside, risk_controlled
    balanced_sol = optimize_squad(
        budget_remaining=req.budget_remaining,
        players_to_acquire=req.players_to_acquire,
        locked_player_ids=req.locked_player_ids,
        excluded_player_ids=req.excluded_player_ids,
        strategy="balanced",
        role_requirements=req.role_requirements,
        max_overseas=req.max_overseas,
        current_overseas=req.current_overseas
    )

    upside_sol = optimize_squad(
        budget_remaining=req.budget_remaining,
        players_to_acquire=req.players_to_acquire,
        locked_player_ids=req.locked_player_ids,
        excluded_player_ids=req.excluded_player_ids,
        strategy="upside",
        role_requirements=req.role_requirements,
        max_overseas=req.max_overseas,
        current_overseas=req.current_overseas
    )

    risk_controlled_sol = optimize_squad(
        budget_remaining=req.budget_remaining,
        players_to_acquire=req.players_to_acquire,
        locked_player_ids=req.locked_player_ids,
        excluded_player_ids=req.excluded_player_ids,
        strategy="risk_controlled",
        role_requirements=req.role_requirements,
        max_overseas=req.max_overseas,
        current_overseas=req.current_overseas
    )

    return {
        "status": balanced_sol.get("status"),
        "strategies": {
            "balanced": balanced_sol,
            "upside": upside_sol,
            "risk_controlled": risk_controlled_sol
        }
    }

@router.post("/what-if")
def run_what_if(req: SquadWhatIfRequest):
    return run_what_if_analysis(
        base_scenario=req.base_scenario,
        exclude_player_id=req.exclude_player_id,
        lock_player_id=req.lock_player_id,
        new_budget=req.new_budget,
        new_strategy=req.new_strategy
    )
