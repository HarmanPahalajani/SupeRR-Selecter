"""
Staging API Router for Dynamic Pressure Engine vNext
Allows audit and inspection of vNext pressure metrics and ranking comparisons
without modifying or disrupting public production endpoints.
Strictly enforces competition scope separation:
- Primary Senior Scope: IPL + T20I (193,988 deliveries)
- Supplementary Emerging Scope: OTHER_T20 (6,973 deliveries)
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
import pandas as pd
import numpy as np

router = APIRouter(prefix="/staging", tags=["Staging - Pressure Engine vNext"])

STAGING_META_PATH = Path("data/staging/staging_metadata_vNext.json")
STAGING_PLAYER_METRICS_PATH = Path("data/staging/fact_player_metrics_pressure_vNext.parquet")
PROD_PLAYER_METRICS_PATH = Path("data/processed/fact_player_metrics.parquet")
STAGING_DELIVERY_STATES_PATH = Path("data/staging/fact_delivery_states_pressure_vNext.parquet")
PROD_DELIVERY_STATES_PATH = Path("data/processed/fact_delivery_states.parquet")

@router.get("/meta")
def get_staging_metadata() -> Dict[str, Any]:
    """Returns metadata and scope configuration for the vNext staging pressure engine."""
    if not STAGING_META_PATH.exists():
        raise HTTPException(status_code=404, detail="Staging metadata not found. Run generate_staging.py first.")
    with open(STAGING_META_PATH, "r") as f:
        return json.load(f)

@router.get("/pressure-comparison")
def compare_player_pressure_metrics(
    category: str = Query("batters", pattern="^(batters|bowlers)$", description="'batters' or 'bowlers'"),
    scope: str = Query("primary", pattern="^(primary|emerging)$", description="'primary' (IPL/T20I) or 'emerging' (OTHER_T20 discovery candidates)"),
    player_name: Optional[str] = Query(None, description="Optional player name substring search"),
    limit: int = Query(25, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Compares production vs staging pressure metrics and rankings with strict competition scope enforcement.
    """
    if not STAGING_PLAYER_METRICS_PATH.exists() or not PROD_PLAYER_METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Staging or production player metrics not found.")

    df_stage = pd.read_parquet(STAGING_PLAYER_METRICS_PATH)
    df_prod = pd.read_parquet(PROD_PLAYER_METRICS_PATH)

    if scope == "emerging":
        # Supplementary emerging candidates
        if category == "batters":
            emg_active = df_stage[df_stage['emerging_pressure_balls'] >= 10].copy()
            if emg_active.empty:
                return {"scope": "emerging", "category": "batters", "count": 0, "results": []}
            emg_active['emerging_rank'] = emg_active['emerging_pressure_sr'].rank(ascending=False, method='min')
            if player_name:
                emg_active = emg_active[emg_active['player_name'].str.contains(player_name, case=False, na=False)]
            emg_active = emg_active.sort_values('emerging_rank').head(limit)
            results = []
            for _, r in emg_active.iterrows():
                results.append({
                    "player_id": int(r['player_id']),
                    "player_name": r['player_name'],
                    "scope": "emerging (OTHER_T20)",
                    "emerging_rank": int(r['emerging_rank']),
                    "emerging_balls": int(r['emerging_pressure_balls']),
                    "emerging_runs": int(r['emerging_pressure_runs']),
                    "emerging_sr": round(float(r['emerging_pressure_sr']), 2),
                    "primary_matches": int(r.get('total_matches', 0))
                })
            return {"scope": "emerging", "competition_scope": "OTHER_T20", "category": "batters", "count": len(results), "results": results}
        else:
            emg_active = df_stage[df_stage['emerging_pressure_balls_bowled'] >= 12].copy()
            if emg_active.empty:
                return {"scope": "emerging", "category": "bowlers", "count": 0, "results": []}
            emg_active['emerging_rank'] = emg_active['emerging_pressure_economy'].rank(ascending=True, method='min')
            if player_name:
                emg_active = emg_active[emg_active['player_name'].str.contains(player_name, case=False, na=False)]
            emg_active = emg_active.sort_values('emerging_rank').head(limit)
            results = []
            for _, r in emg_active.iterrows():
                results.append({
                    "player_id": int(r['player_id']),
                    "player_name": r['player_name'],
                    "scope": "emerging (OTHER_T20)",
                    "emerging_rank": int(r['emerging_rank']),
                    "emerging_balls_bowled": int(r['emerging_pressure_balls_bowled']),
                    "emerging_runs_conceded": int(r['emerging_pressure_runs_conceded']),
                    "emerging_econ": round(float(r['emerging_pressure_economy']), 2),
                    "primary_matches": int(r.get('total_matches', 0))
                })
            return {"scope": "emerging", "competition_scope": "OTHER_T20", "category": "bowlers", "count": len(results), "results": results}

    # Primary scope comparison (IPL + T20I)
    if category == "batters":
        prod_active = df_prod[df_prod['pressure_balls_faced'] >= 20].copy()
        prod_active['prod_pressure_sr'] = (prod_active['pressure_runs'] / prod_active['pressure_balls_faced']) * 100.0
        prod_active['prod_rank'] = prod_active['prod_pressure_sr'].rank(ascending=False, method='min')

        stage_active = df_stage[df_stage['staging_pressure_balls'] >= 20].copy()
        stage_active['stage_pressure_sr'] = (stage_active['staging_pressure_runs'] / stage_active['staging_pressure_balls']) * 100.0
        stage_active['stage_rank'] = stage_active['stage_pressure_sr'].rank(ascending=False, method='min')

        merged = pd.merge(
            stage_active[['player_id', 'player_name', 'total_matches', 'confidence_tier', 'staging_pressure_balls', 'staging_pressure_runs', 'stage_pressure_sr', 'stage_rank']],
            prod_active[['player_id', 'pressure_balls_faced', 'pressure_runs', 'prod_pressure_sr', 'prod_rank']],
            on='player_id',
            how='inner'
        )
        merged['rank_delta'] = merged['prod_rank'] - merged['stage_rank'] # positive = improved in staging

        if player_name:
            merged = merged[merged['player_name'].str.contains(player_name, case=False, na=False)]

        merged = merged.sort_values('stage_rank').head(limit)

        records = []
        for _, row in merged.iterrows():
            records.append({
                "player_id": int(row['player_id']),
                "player_name": row['player_name'],
                "competition_scope": "IPL_T20I",
                "primary_matches": int(row['total_matches']),
                "confidence_tier": row['confidence_tier'],
                "staging": {
                    "rank": int(row['stage_rank']),
                    "balls": int(row['staging_pressure_balls']),
                    "runs": int(row['staging_pressure_runs']),
                    "strike_rate": round(float(row['stage_pressure_sr']), 2)
                },
                "production": {
                    "rank": int(row['prod_rank']),
                    "balls": int(row['pressure_balls_faced']),
                    "runs": int(row['pressure_runs']),
                    "strike_rate": round(float(row['prod_pressure_sr']), 2)
                },
                "rank_delta": int(row['rank_delta'])
            })

        return {
            "category": "batters",
            "competition_scope": "IPL_T20I",
            "count": len(records),
            "qualifier": "min 20 primary-scope pressure balls faced",
            "results": records
        }

    else: # bowlers
        prod_active = df_prod[df_prod['pressure_balls_bowled'] >= 24].copy()
        prod_active['prod_pressure_econ'] = (prod_active['pressure_runs_conceded'] / (prod_active['pressure_balls_bowled'] / 6.0))
        prod_active['prod_rank'] = prod_active['prod_pressure_econ'].rank(ascending=True, method='min')

        stage_active = df_stage[df_stage['staging_pressure_balls_bowled'] >= 24].copy()
        stage_active['stage_pressure_econ'] = (stage_active['staging_pressure_runs_conceded'] / (stage_active['staging_pressure_balls_bowled'] / 6.0))
        stage_active['stage_rank'] = stage_active['stage_pressure_econ'].rank(ascending=True, method='min')

        merged = pd.merge(
            stage_active[['player_id', 'player_name', 'total_matches', 'confidence_tier', 'staging_pressure_balls_bowled', 'staging_pressure_runs_conceded', 'stage_pressure_econ', 'stage_rank']],
            prod_active[['player_id', 'pressure_balls_bowled', 'pressure_runs_conceded', 'prod_pressure_econ', 'prod_rank']],
            on='player_id',
            how='inner'
        )
        merged['rank_delta'] = merged['prod_rank'] - merged['stage_rank']

        if player_name:
            merged = merged[merged['player_name'].str.contains(player_name, case=False, na=False)]

        merged = merged.sort_values('stage_rank').head(limit)

        records = []
        for _, row in merged.iterrows():
            records.append({
                "player_id": int(row['player_id']),
                "player_name": row['player_name'],
                "competition_scope": "IPL_T20I",
                "primary_matches": int(row['total_matches']),
                "confidence_tier": row['confidence_tier'],
                "staging": {
                    "rank": int(row['stage_rank']),
                    "balls_bowled": int(row['staging_pressure_balls_bowled']),
                    "runs_conceded": int(row['staging_pressure_runs_conceded']),
                    "economy": round(float(row['stage_pressure_econ']), 2)
                },
                "production": {
                    "rank": int(row['prod_rank']),
                    "balls_bowled": int(row['pressure_balls_bowled']),
                    "runs_conceded": int(row['pressure_runs_conceded']),
                    "economy": round(float(row['prod_pressure_econ']), 2)
                },
                "rank_delta": int(row['rank_delta'])
            })

        return {
            "category": "bowlers",
            "competition_scope": "IPL_T20I",
            "count": len(records),
            "qualifier": "min 24 primary-scope pressure balls bowled",
            "results": records
        }

@router.get("/delivery-comparison")
def compare_delivery_pressure(
    match_id: int = Query(..., description="Match ID to inspect"),
    innings: int = Query(..., ge=1, le=2, description="Innings (1 or 2)"),
    limit: int = Query(50, ge=1, le=120)
) -> Dict[str, Any]:
    """
    Compares ball-by-ball situational pressure between production and staging vNext.
    Exposes competition scope of the match.
    """
    if not STAGING_DELIVERY_STATES_PATH.exists() or not PROD_DELIVERY_STATES_PATH.exists():
        raise HTTPException(status_code=404, detail="Delivery states parquet not found.")

    df_stage = pd.read_parquet(STAGING_DELIVERY_STATES_PATH)
    df_prod = pd.read_parquet(PROD_DELIVERY_STATES_PATH)

    mask_stage = (df_stage['match_id'] == match_id) & (df_stage['innings'] == innings)
    mask_prod = (df_prod['match_id'] == match_id) & (df_prod['innings'] == innings)

    sub_stage = df_stage[mask_stage].sort_values(['overid', 'ball_num']).head(limit)
    sub_prod = df_prod[mask_prod].sort_values(['overid', 'ball_num']).head(limit)

    if sub_stage.empty:
        raise HTTPException(status_code=404, detail=f"No delivery states found for match_id={match_id}, innings={innings}")

    comp_format = sub_stage['format_scope'].iloc[0] if 'format_scope' in sub_stage.columns else 'Unknown'
    is_primary = bool(sub_stage['is_primary_scope'].iloc[0]) if 'is_primary_scope' in sub_stage.columns else True

    merged = pd.merge(
        sub_stage[['overid', 'ball_num', 'batter_id', 'bowler_id', 'situational_pressure', 'inn1_pressure_index', 'chase_pressure_index', 'pressure_tier']],
        sub_prod[['overid', 'ball_num', 'situational_pressure', 'pressure_tier']],
        on=['overid', 'ball_num'],
        suffixes=('_staging', '_prod')
    )

    deliveries = []
    for _, row in merged.iterrows():
        deliveries.append({
            "over": int(row['overid']),
            "ball": int(row['ball_num']),
            "prod_pressure": round(float(row['situational_pressure_prod']), 2),
            "stage_pressure": round(float(row['situational_pressure_staging']), 2),
            "prod_tier": row['pressure_tier_prod'],
            "stage_tier": row['pressure_tier_staging'],
            "pressure_diff": round(float(row['situational_pressure_staging'] - row['situational_pressure_prod']), 2)
        })

    return {
        "match_id": match_id,
        "innings": innings,
        "format_scope": comp_format,
        "is_primary_scope": is_primary,
        "deliveries_compared": len(deliveries),
        "deliveries": deliveries
    }
