"""
Pressure Bowlers API Endpoints
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.app.services.pressure_bowler_service import PressureBowlerService

router = APIRouter(prefix="/pressure-bowlers", tags=["Pressure Bowlers"])


@router.get("/leaderboard")
def get_leaderboard(
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING"),
    bowling_style: Optional[str] = Query(None, description="Bowling style filter (e.g. Fast, Leg-Break)"),
    pace_or_spin: Optional[str] = Query(None, description="Bowling category filter: Pace, Spin, or ALL"),
    search: Optional[str] = Query(None, description="Search player name"),
    sort_by: str = Query("pressure_rank", description="Sort field: pressure_rank, pressure_wicket_rank, hp_risk_adjusted_impact, hp_raw_runs_saved_per_6, hp_runs_saved, hp_wae, hp_wickets, hp_overs, hp_matches, hp_economy_rate, hp_positive_match_pct"),
    sort_dir: str = Query("asc", description="Sort direction: asc or desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    return PressureBowlerService.get_leaderboard(
        scope=scope,
        bowling_style=bowling_style,
        pace_or_spin=pace_or_spin,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset
    )


@router.get("/summary")
def get_summary(
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING")
):
    return PressureBowlerService.get_discovery_summary(scope=scope)


@router.get("/player/{player_id}")
def get_player_pressure_profile(
    player_id: int,
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING")
):
    profile = PressureBowlerService.get_player_pressure_profile(player_id=player_id, scope=scope)
    if not profile:
        raise HTTPException(status_code=404, detail="Player pressure bowling profile not found")
    return profile


@router.get("/player/{player_id}/matches")
def get_player_matches(
    player_id: int,
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING"),
    limit: int = Query(50, ge=1, le=100)
):
    return PressureBowlerService.get_player_matches(player_id=player_id, scope=scope, limit=limit)


@router.get("/compare")
def compare_players(
    player_ids: str = Query(..., description="Comma-separated player IDs (e.g. 74,108)"),
    scope: str = Query("IPL_T20I", description="Competition scope: IPL_T20I, IPL, T20I, or EMERGING"),
    context: str = Query("ALL", description="Context filter: ALL, CHASE_DEFENCE, or FIRST_INNINGS_RESTRICTION")
):
    try:
        pids = [int(p.strip()) for p in player_ids.split(",") if p.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player_ids format. Expected comma-separated integers.")
    return PressureBowlerService.compare_players(player_ids=pids, scope=scope, context=context)


@router.get("/methodology")
def get_methodology():
    return PressureBowlerService.get_methodology_overview()
