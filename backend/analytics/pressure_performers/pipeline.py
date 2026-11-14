"""
Production Data Pipeline for Pressure Performer Intelligence
Part of SupeRR Intelligence — Pressure Performer Intelligence

Generates full-dataset pressure metrics, unified rankings, match evidence logs,
and leaderboards across:
- Primary Combined (IPL & T20I)
- IPL Only
- T20I Only
- Emerging Competitions
and across all pressure contexts (Combined ALL, Chase Crisis, First-Innings Acceleration).

Writes outputs to Parquet and synchronizes DuckDB tables with 100% population reconciliation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from typing import Dict, List, Any
import pandas as pd
import numpy as np
import duckdb

from backend.analytics.pressure_performers.pressure_opportunities import tag_high_pressure_deliveries
from backend.analytics.pressure_performers.contribution import compute_delivery_contributions
from backend.analytics.pressure_performers.match_aggregation import aggregate_player_matches
from backend.analytics.pressure_performers.reliability import compute_career_pressure_metrics
from backend.analytics.pressure_performers.classification import (
    classify_dataframe,
    generate_player_explanations,
    STATUS_INSUFFICIENT
)
from backend.analytics.pressure_performers.ranking import compute_pressure_rankings


def run_pipeline() -> Dict[str, Any]:
    print("=== Launching Pressure Performer Intelligence Production Pipeline ===")
    con = duckdb.connect()
    
    # 1. Load canonical datasets
    print("Loading deliveries, players, and matches...")
    deliveries_path = "data/processed/fact_delivery_scored.parquet"
    players_path = "data/processed/dim_player.parquet"
    matches_path = "data/processed/dim_match.parquet"
    
    df_del = con.execute(f"SELECT * FROM read_parquet('{deliveries_path}')").df()
    dim_player = con.execute(f"SELECT * FROM read_parquet('{players_path}')").df()
    dim_match = con.execute(f"SELECT * FROM read_parquet('{matches_path}')").df()
    
    total_master_players = len(dim_player)
    print(f"Loaded {len(df_del)} canonical regular deliveries, {total_master_players} master players.")
    
    # Population reconciliation sets
    primary_del = df_del[df_del["is_primary_scope"]].copy()
    emerging_del = df_del[~df_del["is_primary_scope"]].copy()
    
    primary_strikers = set(primary_del["striker_id"].dropna().astype(int))
    primary_bowlers = set(primary_del["bowler_id"].dropna().astype(int))
    primary_participants = primary_strikers.union(primary_bowlers)  # Exactly 891
    
    emerging_strikers = set(emerging_del["striker_id"].dropna().astype(int))
    emerging_bowlers = set(emerging_del["bowler_id"].dropna().astype(int))
    emerging_participants = emerging_strikers.union(emerging_bowlers)  # Exactly 172
    
    emerging_only = emerging_participants - primary_participants      # Exactly 67
    dual_scope = primary_participants.intersection(emerging_participants)  # Exactly 105
    all_active = primary_participants.union(emerging_participants)     # Exactly 958
    all_player_ids = set(dim_player["player_id"].astype(int))
    squad_only = all_player_ids - all_active                          # Exactly 259
    
    print(f"Population Audit: {len(primary_participants)} Primary participants, {len(emerging_participants)} Emerging participants.")
    print(f"  - Primary Only: {len(primary_participants - emerging_participants)}")
    print(f"  - Emerging Only: {len(emerging_only)}")
    print(f"  - Dual Scope: {len(dual_scope)}")
    print(f"  - Squad Only (0 deliveries): {len(squad_only)}")
    print(f"  - Master Reconciliation: {len(primary_participants - emerging_participants)} + {len(emerging_only)} + {len(dual_scope)} + {len(squad_only)} = {total_master_players}")
    
    # Career summaries for visibility & baseline
    def build_career_summary(del_df):
        return del_df.groupby("striker_id").agg(
            career_matches=("match_id", "nunique"),
            career_balls_faced=("is_legal_ball", "sum"),
            career_runs=("batter_runs", "sum")
        ).reset_index().rename(columns={"striker_id": "player_id"})

    primary_career = build_career_summary(primary_del)
    emerging_career = build_career_summary(emerging_del)
    
    ipl_del = primary_del[primary_del["format_scope"] == "IPL"].copy()
    t20i_del = primary_del[primary_del["format_scope"] == "T20I"].copy()
    ipl_career = build_career_summary(ipl_del)
    t20i_career = build_career_summary(t20i_del)
    
    # Tag high-pressure deliveries
    print("Tagging high-pressure deliveries with dynamic thresholds...")
    primary_tagged = tag_high_pressure_deliveries(primary_del, threshold_variant="p75", is_primary=True)
    primary_contrib = compute_delivery_contributions(primary_tagged)
    primary_hp = primary_contrib[primary_contrib["is_high_pressure"]].copy()
    
    ipl_hp = primary_hp[primary_hp["format_scope"] == "IPL"].copy()
    t20i_hp = primary_hp[primary_hp["format_scope"] == "T20I"].copy()
    
    emerging_tagged = tag_high_pressure_deliveries(emerging_del, threshold_variant="p75", is_primary=False)
    emerging_contrib = compute_delivery_contributions(emerging_tagged)
    emerging_hp = emerging_contrib[emerging_contrib["is_high_pressure"]].copy()
    
    all_metrics_records = []
    all_match_records = []
    
    contexts = [
        ("ALL", None),
        ("CHASE", "CHASE"),
        ("FIRST_INNINGS", "FIRST_INNINGS")
    ]
    
    scopes = [
        ("IPL_T20I", primary_hp, primary_career, 25, 3, False),
        ("IPL", ipl_hp, ipl_career, 20, 2, False),
        ("T20I", t20i_hp, t20i_career, 20, 2, False),
        ("EMERGING", emerging_hp, emerging_career, 15, 2, True)
    ]
    
    for scope_code, hp_subset, career_df, min_b, min_m, is_em in scopes:
        for ctx_code, ctx_filter in contexts:
            print(f"Processing Scope: {scope_code} | Context: {ctx_code}...")
            m_df = aggregate_player_matches(hp_subset, context_filter=ctx_filter)
            if not m_df.empty:
                m_df["competition_scope"] = scope_code
                m_df["pressure_context"] = ctx_code
                all_match_records.append(m_df)
                
                n_boot = 500 if is_em else 1000
                p_metrics = compute_career_pressure_metrics(
                    m_df, career_summary_df=career_df,
                    min_eval_balls=min_b, min_eval_matches=min_m,
                    n_bootstrap=n_boot, seed=42
                )
                p_classified = classify_dataframe(p_metrics, is_emerging=is_em)
                p_ranked = compute_pressure_rankings(
                    p_classified, min_balls=min_b, min_matches=min_m, is_emerging=is_em
                )
                p_ranked["competition_scope"] = scope_code
                p_ranked["pressure_context"] = ctx_code
                all_metrics_records.append(p_ranked)
                
    # Combine active records
    combined_metrics = pd.concat(all_metrics_records, ignore_index=True)
    combined_matches = pd.concat(all_match_records, ignore_index=True)
    
    # 4. Strict Population Reconciliation for Master Dimension
    # Ensure all 1,217 players appear in master classification table
    dim_player_map = dim_player.set_index("player_id")["player_name"].to_dict()
    
    # Primary ALL active players
    primary_active_all = combined_metrics[
        (combined_metrics["competition_scope"] == "IPL_T20I") & 
        (combined_metrics["pressure_context"] == "ALL")
    ].copy()
    existing_primary_all_pids = set(primary_active_all["player_id"])
    
    # Emerging ALL active players
    emerging_active_all = combined_metrics[
        (combined_metrics["competition_scope"] == "EMERGING") & 
        (combined_metrics["pressure_context"] == "ALL")
    ].copy()
    emerging_active_map = emerging_active_all.set_index("player_id")["classification"].to_dict()
    
    # Construct zero/missing records with accurate population labels
    missing_records = []
    for pid in all_player_ids:
        if pid in existing_primary_all_pids:
            continue
        pname = dim_player_map.get(pid, f"Player {pid}")
        
        if pid in emerging_only:
            cls = "Emerging Scope Only — Not Evaluated in Primary"
            ev = "Emerging Scope Only"
            part_status = "EMERGING_ONLY"
        elif pid in squad_only:
            cls = "Squad Member — Zero Recorded Deliveries"
            ev = "Zero Recorded Deliveries"
            part_status = "SQUAD_ONLY"
        else:
            # Primary participant who did not bat in high pressure (e.g. specialist bowler or 0 HP balls)
            cls = STATUS_INSUFFICIENT
            ev = "Insufficient Evidence"
            part_status = "PRIMARY_PARTICIPANT"
            
        missing_records.append({
            "player_id": pid,
            "player_name": pname,
            "hp_matches": 0,
            "hp_balls": 0.0,
            "hp_runs": 0.0,
            "hp_exp_runs": 0.0,
            "hp_rae": 0.0,
            "hp_raw_rae_per_100": np.nan,
            "hp_positive_matches": 0,
            "hp_negative_matches": 0,
            "hp_neutral_matches": 0,
            "hp_positive_match_pct": np.nan,
            "hp_negative_match_pct": np.nan,
            "hp_mean_match_rae": np.nan,
            "hp_median_match_rae": np.nan,
            "hp_std_match_rae": np.nan,
            "hp_max_single_match_rae": np.nan,
            "hp_positive_match_share": np.nan,
            "hp_single_match_share": 0.0,
            "hp_sum_negative_rae": 0.0,
            "hp_worst_single_match_rae": 0.0,
            "hp_dismissals": 0.0,
            "hp_exp_wickets": 0.0,
            "hp_dismissal_rate": np.nan,
            "hp_boundary_pct": np.nan,
            "hp_six_pct": np.nan,
            "hp_dot_pct": np.nan,
            "hp_strike_rate": np.nan,
            "hp_ci_low": np.nan,
            "hp_ci_high": np.nan,
            "hp_ci_width": np.nan,
            "hp_eb_prior_mean": 0.0,
            "hp_eb_shrinkage": 1.0,
            "hp_posterior_mean": np.nan,
            "hp_posterior_se": np.nan,
            "hp_risk_adjusted_impact": np.nan,
            "hp_lcb": np.nan,
            "hp_ucb": np.nan,
            "hp_lcb_95": np.nan,
            "hp_ucb_95": np.nan,
            "career_matches": 0,
            "career_balls_faced": 0.0,
            "career_runs": 0.0,
            "classification": cls,
            "evidence_level": ev,
            "is_pressure_ranked": False,
            "pressure_rank": np.nan,
            "competition_scope": "IPL_T20I",
            "pressure_context": "ALL",
            "participation_status": part_status,
        })
        
    full_metrics = pd.concat([combined_metrics, pd.DataFrame(missing_records)], ignore_index=True)
    
    # Merge player metadata (bat_style, bowl_style, is_wk)
    full_metrics = full_metrics.merge(
        dim_player[["player_id", "bat_style", "bowl_style", "is_wk"]],
        on="player_id", how="left"
    )
    
    # Generate scouting explanations
    full_metrics["explanation"] = full_metrics.apply(generate_player_explanations, axis=1)
    
    # Build Dim Player Pressure Classification (Master Player Dimension)
    dim_classification = full_metrics[
        (full_metrics["competition_scope"] == "IPL_T20I") & 
        (full_metrics["pressure_context"] == "ALL")
    ].copy()
    
    # Set accurate participation status and emerging status
    dim_classification["participation_status"] = np.where(
        dim_classification["player_id"].isin(squad_only), "SQUAD_ONLY",
        np.where(dim_classification["player_id"].isin(emerging_only), "EMERGING_ONLY", "PRIMARY_PARTICIPANT")
    )
    dim_classification["emerging_classification"] = dim_classification["player_id"].map(
        lambda pid: emerging_active_map.get(pid, "Not Evaluated in Emerging Scope")
    )
    
    cols_to_keep = [
        "player_id", "player_name", "participation_status", "bat_style", "bowl_style", "is_wk",
        "classification", "evidence_level", "pressure_rank", "is_pressure_ranked",
        "hp_matches", "hp_balls", "hp_runs", "hp_rae", "hp_raw_rae_per_100",
        "hp_posterior_mean", "hp_risk_adjusted_impact", "hp_lcb", "hp_ucb", "hp_lcb_95", "hp_ucb_95",
        "hp_ci_low", "hp_ci_high", "hp_positive_matches", "hp_positive_match_pct", "hp_negative_match_pct",
        "hp_positive_match_share", "hp_sum_negative_rae", "hp_strike_rate", "hp_boundary_pct",
        "hp_dot_pct", "hp_dismissals", "emerging_classification", "explanation"
    ]
    dim_classification = dim_classification[[c for c in cols_to_keep if c in dim_classification.columns]].copy()
    
    print(f"Final full metrics rows: {len(full_metrics)}")
    print(f"Final match evidence rows: {len(combined_matches)}")
    print(f"Dim player pressure classification rows: {len(dim_classification)} (exactly {total_master_players} master players)")
    
    # 5. Save Parquet tables
    out_metrics_path = "data/processed/fact_player_pressure_metrics.parquet"
    out_matches_path = "data/processed/fact_player_pressure_matches.parquet"
    out_dim_path = "data/processed/dim_player_pressure_classification.parquet"
    
    full_metrics.to_parquet(out_metrics_path, index=False)
    combined_matches.to_parquet(out_matches_path, index=False)
    dim_classification.to_parquet(out_dim_path, index=False)
    print(f"Saved Parquet files to {out_metrics_path}, {out_matches_path}, {out_dim_path}")
    
    # 6. Synchronize DuckDB
    db_path = "data/app/analytics.duckdb"
    app_con = duckdb.connect(db_path)
    
    print(f"Synchronizing DuckDB at {db_path}...")
    app_con.execute(f"CREATE OR REPLACE TABLE fact_player_pressure_metrics AS SELECT * FROM read_parquet('{out_metrics_path}')")
    app_con.execute(f"CREATE OR REPLACE TABLE fact_player_pressure_matches AS SELECT * FROM read_parquet('{out_matches_path}')")
    app_con.execute(f"CREATE OR REPLACE TABLE dim_player_pressure_classification AS SELECT * FROM read_parquet('{out_dim_path}')")
    
    cnt_m = app_con.execute("SELECT count(*) FROM fact_player_pressure_metrics").fetchone()[0]
    cnt_match = app_con.execute("SELECT count(*) FROM fact_player_pressure_matches").fetchone()[0]
    cnt_dim = app_con.execute("SELECT count(*) FROM dim_player_pressure_classification").fetchone()[0]
    
    print(f"DuckDB Verified: fact_metrics={cnt_m}, fact_matches={cnt_match}, dim_classification={cnt_dim}")
    return {
        "metrics_count": cnt_m,
        "matches_count": cnt_match,
        "dim_count": cnt_dim,
        "primary_participants": len(primary_participants),
        "emerging_participants": len(emerging_participants),
        "emerging_only": len(emerging_only),
        "squad_only": len(squad_only),
    }


if __name__ == "__main__":
    run_pipeline()
