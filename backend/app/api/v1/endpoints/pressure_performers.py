"""
Pressure Performers API Endpoints
Part of SupeRR Intelligence — Pressure Performer Intelligence
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.app.services.pressure_performer_service import PressurePerformerService

router = APIRouter(prefix="/pressure-performers", tags=["Pressure Performers"])


@router.get("/leaderboard")
def get_leaderboard(
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING"),
    context: str = Query("ALL", description="Pressure context: ALL, CHASE, or FIRST_INNINGS"),
    classification: Optional[str] = Query(None, description="Optional filter"),
    search: Optional[str] = Query(None, description="Search player name"),
    sort_by: str = Query("pressure_rank", description="Sort field: pressure_rank, hp_risk_adjusted_impact, hp_raw_rae_per_100, hp_rae, hp_positive_match_pct, hp_strike_rate, hp_balls"),
    sort_dir: str = Query("asc", description="Sort direction: asc or desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    return PressurePerformerService.get_leaderboard(
        scope=scope,
        context=context,
        classification=classification,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset
    )


@router.get("/discovery")
def get_discovery_summary(
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING")
):
    return PressurePerformerService.get_discovery_summary(scope=scope)


@router.get("/summary")
def get_summary_highlight(
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING")
):
    return PressurePerformerService.get_discovery_summary(scope=scope)


@router.get("/player/{player_id}")
def get_player_pressure_profile(player_id: int):
    profile = PressurePerformerService.get_player_pressure_profile(player_id=player_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Player pressure profile not found")
    return profile


@router.get("/player/{player_id}/matches")
def get_player_matches(
    player_id: int,
    limit: int = Query(50, ge=1, le=100)
):
    return PressurePerformerService.get_player_matches(player_id=player_id, limit=limit)


@router.get("/compare")
def compare_players(
    player_ids: str = Query(..., description="Comma-separated player IDs (e.g. 5553,4847)"),
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING"),
    context: str = Query("ALL", description="Pressure context: ALL, CHASE, or FIRST_INNINGS")
):
    try:
        pids = [int(p.strip()) for p in player_ids.split(",") if p.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player_ids format. Expected comma-separated integers.")
    return PressurePerformerService.compare_players(player_ids=pids, scope=scope, context=context)


@router.get("/methodology")
def get_methodology_overview():
    return PressurePerformerService.get_methodology_overview()
