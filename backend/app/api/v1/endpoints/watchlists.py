from fastapi import APIRouter
from backend.app.schemas.models import WatchlistCreateRequest, WatchlistAddPlayerRequest, NoteCreateRequest
from backend.app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["Watchlist & Notes"])

@router.get("")
def list_watchlists():
    return WatchlistService.get_watchlists()

@router.post("")
def create_watchlist(req: WatchlistCreateRequest):
    return WatchlistService.create_watchlist(req.name, req.description or "")

@router.post("/{watchlist_id}/players")
def add_player_to_watchlist(watchlist_id: int, req: WatchlistAddPlayerRequest):
    return WatchlistService.add_player(watchlist_id, req.player_id, req.priority or "Medium", req.target_role or "")

@router.delete("/{watchlist_id}/players/{player_id}")
def remove_player_from_watchlist(watchlist_id: int, player_id: int):
    return WatchlistService.remove_player(watchlist_id, player_id)

@router.get("/notes/{player_id}")
def get_player_notes(player_id: int):
    return WatchlistService.get_player_notes(player_id)

@router.post("/notes/{player_id}")
def add_player_note(player_id: int, req: NoteCreateRequest):
    return WatchlistService.add_player_note(player_id, req.content, req.verdict or "Shortlist", req.author or "Analyst")
