from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.models import PlayerListResponse, PlayerProfileResponse, CompareRequest, CompareResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("", response_model=PlayerListResponse)
def list_players(
    role: Optional[str] = None,
    format_scope: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "overall_player_rating",
    discipline: Optional[str] = None,
    eligible_only: bool = False,
    confidence_tier: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    return AnalyticsService.list_players(
        role=role, format_scope=format_scope, search=search,
        sort_by=sort_by, discipline=discipline, eligible_only=eligible_only,
        confidence_tier=confidence_tier, page=page, page_size=page_size
    )

@router.get("/{player_id}/profile", response_model=PlayerProfileResponse)
def get_player_profile(player_id: int):
    profile = AnalyticsService.get_player_profile(player_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found.")
    return profile

@router.post("/compare", response_model=CompareResponse)
def compare_players(req: CompareRequest):
    if len(req.player_ids) < 2 or len(req.player_ids) > 4:
        raise HTTPException(status_code=400, detail="Comparison requires between 2 and 4 player IDs.")
    return AnalyticsService.compare_players(req.player_ids)
