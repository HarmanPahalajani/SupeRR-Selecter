import json
from pathlib import Path
from fastapi import APIRouter, Query
from backend.app.schemas.models import HealthResponse, CoverageResponse
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.win_prob_service import WinProbabilityService

router = APIRouter(prefix="/meta", tags=["Metadata"])

@router.get("/health", response_model=HealthResponse)
def get_health():
    return {
        "status": "healthy",
        "backend_version": "1.0.0",
        "duckdb_connected": Path("data/app/analytics.duckdb").exists(),
        "sqlite_connected": Path("data/app/user_store.db").exists(),
        "data_scope": "IPL (2022-2026) + T20I (2022-2026)"
    }

@router.get("/coverage", response_model=CoverageResponse)
def get_coverage():
    return AnalyticsService.get_coverage()

@router.get("/model-status")
def get_model_status():
    status = WinProbabilityService.get_status()
    eval_file = Path("artifacts/metrics/model_evaluation.json")
    if eval_file.exists():
        with open(eval_file) as f:
            status["eval_registry"] = json.load(f)
    return status

@router.get("/predict-win-prob")
def predict_win_prob(
    runs_needed: float = Query(..., description="Runs required by batting team to win"),
    legal_balls_remaining: float = Query(..., description="Legal deliveries remaining in chase"),
    wickets_in_hand: float = Query(..., description="Wickets in hand (1 to 10)"),
    required_run_rate: float = Query(..., description="Required run rate per 6 balls"),
    current_run_rate: float = Query(..., description="Current run rate per 6 balls"),
    model: str = Query("catboost", description="Model engine: 'catboost' (promoted primary) or 'logistic' (benchmark)")
):
    return WinProbabilityService.predict_chase_win_prob(
        runs_needed=runs_needed,
        legal_balls_remaining=legal_balls_remaining,
        wickets_in_hand=wickets_in_hand,
        required_run_rate=required_run_rate,
        current_run_rate=current_run_rate,
        model_type=model
    )

