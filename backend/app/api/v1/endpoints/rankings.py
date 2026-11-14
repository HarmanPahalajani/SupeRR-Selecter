from fastapi import APIRouter, Query
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Rankings & Discovery"])

@router.get("/rankings")
def get_rankings(category: str = Query("batters", pattern="^(batters|bowlers)$"), limit: int = Query(25, ge=5, le=100)):
    return AnalyticsService.get_rankings(category=category, limit=limit)

@router.get("/rankings/batters")
def get_batter_rankings(limit: int = Query(25, ge=5, le=100)):
    return AnalyticsService.get_rankings(category="batters", limit=limit)

@router.get("/rankings/bowlers")
def get_bowler_rankings(limit: int = Query(25, ge=5, le=100)):
    return AnalyticsService.get_rankings(category="bowlers", limit=limit)

@router.get("/discovery/undervalued")
def get_undervalued_talents():
    return AnalyticsService.get_undervalued_talents()
