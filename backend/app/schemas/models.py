from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    backend_version: str
    duckdb_connected: bool
    sqlite_connected: bool
    data_scope: str

class CoverageResponse(BaseModel):
    total_deliveries: int
    primary_scope_deliveries: int
    ipl_deliveries: int
    t20i_deliveries: int
    total_matches: int
    primary_scope_matches: int
    unique_players: int
    date_range: str

class PlayerSummary(BaseModel):
    player_id: int
    player_name: str
    primary_role: str
    bat_style: str
    bowl_style: str
    total_matches: int
    overall_batting_rating: Optional[float] = None
    overall_bowling_rating: Optional[float] = None
    batting_rating: Optional[float] = None
    bowling_rating: Optional[float] = None
    batting_rating_status: Optional[str] = "UNRATED_INSUFFICIENT_DATA"
    bowling_rating_status: Optional[str] = "UNRATED_INSUFFICIENT_DATA"
    batting_confidence_tier: Optional[str] = "INSUFFICIENT_DATA"
    bowling_confidence_tier: Optional[str] = "INSUFFICIENT_DATA"
    batting_sample_size: Optional[int] = 0
    bowling_sample_size: Optional[int] = 0
    batting_uncertainty: Optional[float] = 0.5
    bowling_uncertainty: Optional[float] = 0.5
    batting_ranking_eligible: Optional[bool] = False
    bowling_ranking_eligible: Optional[bool] = False
    batting_official_rank: Optional[int] = None
    bowling_official_rank: Optional[int] = None
    overall_player_rating: Optional[float] = None
    eb_batting_impact: Optional[float] = None
    eb_bowling_impact: Optional[float] = None
    batting_sr: Optional[float] = None
    bowling_econ: Optional[float] = None
    balls_faced: Optional[int] = 0
    total_runs: Optional[int] = 0
    balls_bowled: Optional[int] = 0
    bowler_wickets: Optional[int] = 0
    confidence_tier: str
    is_undervalued: bool

class PlayerListResponse(BaseModel):
    items: List[PlayerSummary]
    total: int
    page: int
    page_size: int

class PlayerProfileResponse(BaseModel):
    summary: PlayerSummary
    career_stats: Dict[str, Any]
    pressure_stats: Dict[str, Any]
    phase_stats: Dict[str, Any]
    matchup_stats: Dict[str, Any]
    failure_signatures: List[str]
    recruitment_verdict: Dict[str, Any]

class CompareRequest(BaseModel):
    player_ids: List[int]
    format_filter: Optional[str] = "COMBINED"

class CompareResponse(BaseModel):
    players: List[Dict[str, Any]]
    head_to_head_matrix: Dict[str, Any]
    winner_by_scenario: Dict[str, Any]

class SquadOptimizeRequest(BaseModel):
    budget_remaining: int = 450000000
    players_to_acquire: int = 5
    locked_player_ids: Optional[List[int]] = []
    excluded_player_ids: Optional[List[int]] = []
    strategy: Optional[str] = "balanced"
    role_requirements: Optional[Dict[str, Dict[str, int]]] = None
    max_overseas: Optional[int] = 8
    current_overseas: Optional[int] = 4

class SquadWhatIfRequest(BaseModel):
    base_scenario: Dict[str, Any]
    exclude_player_id: Optional[int] = None
    lock_player_id: Optional[int] = None
    new_budget: Optional[int] = None
    new_strategy: Optional[str] = None

class AuctionSimRequest(BaseModel):
    target_player_id: int
    bid_cap: int
    user_budget: Optional[int] = 150000000
    n_simulations: Optional[int] = 1000
    inflation_factor: Optional[float] = 1.0

class WatchlistCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""

class WatchlistAddPlayerRequest(BaseModel):
    player_id: int
    priority: Optional[str] = "Medium"
    target_role: Optional[str] = ""

class NoteCreateRequest(BaseModel):
    content: str
    verdict: Optional[str] = "Shortlist"
    author: Optional[str] = "Analyst"
