from fastapi import APIRouter
from backend.app.api.v1.endpoints import meta, players, rankings, squads, auction, watchlists, methodology, staging, pressure_performers, pressure_bowlers

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(meta.router)
api_v1_router.include_router(players.router)
api_v1_router.include_router(rankings.router)
api_v1_router.include_router(squads.router)
api_v1_router.include_router(auction.router)
api_v1_router.include_router(watchlists.router)
api_v1_router.include_router(methodology.router)
api_v1_router.include_router(staging.router)
api_v1_router.include_router(pressure_performers.router)
api_v1_router.include_router(pressure_bowlers.router)
