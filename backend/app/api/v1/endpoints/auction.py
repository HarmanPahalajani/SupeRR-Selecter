import sqlite3
from fastapi import APIRouter
from backend.app.schemas.models import AuctionSimRequest
from backend.optimisation.auction.simulator import simulate_auction

router = APIRouter(prefix="/auction", tags=["Auction Simulator"])

@router.post("/simulate")
def run_auction_simulation(req: AuctionSimRequest):
    return simulate_auction(
        target_player_id=req.target_player_id,
        bid_cap=req.bid_cap,
        user_budget=req.user_budget or 150000000,
        n_simulations=req.n_simulations or 1000,
        inflation_factor=req.inflation_factor or 1.0
    )

@router.get("/pool")
def get_auction_pool():
    conn = sqlite3.connect("data/app/user_store.db")
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT player_id, player_name, primary_role, overseas_status, is_available,
               estimated_price_low, estimated_price_mid, estimated_price_high, price_confidence, price_source
        FROM player_auction_pool
        LIMIT 100
    """).fetchall()
    conn.close()

    items = []
    for r in rows:
        items.append({
            "player_id": r[0],
            "player_name": r[1],
            "primary_role": r[2],
            "overseas_status": r[3],
            "is_available": bool(r[4]),
            "price_low": r[5],
            "price_mid": r[6],
            "price_high": r[7],
            "price_confidence": r[8],
            "price_source": r[9]
        })
    return {"pool": items}
