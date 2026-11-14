"""
Pressure Bowler Pipeline
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Full-dataset execution engine generating:
1. fact_player_pressure_bowling_metrics.parquet
2. fact_player_pressure_bowling_matches.parquet
3. dim_player_pressure_bowling_ranking.parquet

Isolates all 4 scopes: IPL_T20I, IPL, T20I, and EMERGING.
Reconciles complete 1,217 master player population.
"""

from typing import Dict, Any, List
from pathlib import Path
import os
import numpy as np
import pandas as pd

from backend.analytics.pressure_bowlers.pressure_engine import DefensiveBowlingPressureEngine
from backend.analytics.pressure_bowlers.pressure_opportunities import tag_high_pressure_bowling_deliveries
from backend.analytics.pressure_bowlers.contribution import compute_bowling_delivery_contributions
from backend.analytics.pressure_bowlers.match_aggregation import aggregate_bowler_matches
from backend.analytics.pressure_bowlers.reliability import compute_career_bowler_pressure_metrics
from backend.analytics.pressure_bowlers.ranking import compute_bowler_pressure_rankings
from backend.analytics.pressure_bowlers.validation import run_chronological_bowling_validation


class PressureBowlerPipeline:
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.engine = DefensiveBowlingPressureEngine()
        
    def run_pipeline(self) -> Dict[str, Any]:
        print("Starting Pressure Bowler Pipeline across full dataset...")
        
        scored_file = self.data_dir / "fact_delivery_scored.parquet"
        dim_player_file = self.data_dir / "dim_player.parquet"
        
        if not scored_file.exists():
            raise FileNotFoundError(f"Missing {scored_file}")
        if not dim_player_file.exists():
            raise FileNotFoundError(f"Missing {dim_player_file}")
            
        df = pd.read_parquet(scored_file)
        dim_player = pd.read_parquet(dim_player_file)
        
        # 1. Exclude Super Overs strictly
        if "is_super_over" in df.columns:
            so_count = int(df["is_super_over"].sum())
            df_reg = df[~df["is_super_over"]].copy()
        else:
            so_count = 0
            df_reg = df.copy()
            
        print(f"Loaded {len(df_reg)} regulation deliveries (excluded {so_count} super overs).")
        
        # 2. Compute Defensive Pressure across all regulation deliveries
        print("Computing pre-delivery defensive bowling pressure...")
        df_reg["bowling_pressure_index"] = self.engine.compute_defensive_pressure(df_reg)
        
        # 3. Scopes to evaluate
        # Primary scopes: IPL_T20I, IPL, T20I; Emerging scope: EMERGING
        scope_configs = [
            {"scope": "IPL_T20I", "is_primary": True, "filter_fn": lambda d: d["is_primary_scope"] == True},
            {"scope": "IPL", "is_primary": True, "filter_fn": lambda d: (d["is_primary_scope"] == True) & (d["format_scope"] == "IPL")},
            {"scope": "T20I", "is_primary": True, "filter_fn": lambda d: (d["is_primary_scope"] == True) & (d["format_scope"] == "T20I")},
            {"scope": "EMERGING", "is_primary": False, "filter_fn": lambda d: d["is_primary_scope"] == False},
        ]
        
        all_metrics_list = []
        all_matches_list = []
        all_rankings_list = []
        validation_results = {}
        
        for cfg in scope_configs:
            scope_name = cfg["scope"]
            is_prim = cfg["is_primary"]
            scope_df = df_reg[cfg["filter_fn"](df_reg)].copy()
            print(f"\nProcessing Scope [{scope_name}]: {len(scope_df)} deliveries...")
            
            # Tag high-pressure deliveries
            tagged_df = tag_high_pressure_bowling_deliveries(scope_df, threshold_variant="p75", is_primary=is_prim)
            
            # Compute contributions
            contrib_df = compute_bowling_delivery_contributions(tagged_df)
            
            # Filter to qualifying high-pressure deliveries
            hp_deliveries = contrib_df[contrib_df["is_high_pressure_bowling"]].copy()
            print(f"  Scope [{scope_name}] HP deliveries: {len(hp_deliveries)}")
            
            # Aggregate to match level
            scope_matches = aggregate_bowler_matches(hp_deliveries)
            if not scope_matches.empty:
                scope_matches["competition_scope"] = scope_name
                all_matches_list.append(scope_matches)
                print(f"  Scope [{scope_name}] aggregated matches: {len(scope_matches)}")
                
            # Run chronological validation on primary scope
            if scope_name == "IPL_T20I" and not scope_matches.empty:
                print("  Running chronological validation for IPL_T20I...")
                validation_results = run_chronological_bowling_validation(scope_matches, min_eval_overs=3.0, min_eval_matches=2)
                print("  Chronological Validation Result:", validation_results["status"])
                if "runs_saved_crai" in validation_results:
                    print("  CRAI Runs Saved Spearman rho:", validation_results["runs_saved_crai"]["spearman_rho"])
                
            # Compute career metrics & shrinkage
            min_ov = 4.0 if is_prim else 2.0
            min_m = 3 if is_prim else 2
            career_df = compute_career_bowler_pressure_metrics(
                scope_matches,
                min_eval_overs=min_ov,
                min_eval_matches=min_m,
                n_bootstrap=1000,
                seed=42
            )
            
            # Rank bowlers
            if not career_df.empty:
                ranked_df = compute_bowler_pressure_rankings(
                    career_df,
                    min_overs=min_ov,
                    min_matches=min_m,
                    is_emerging=(not is_prim)
                )
            else:
                ranked_df = pd.DataFrame()
                
            # Population reconciliation: Merge all 1,217 players into scope metrics
            active_pids = set(ranked_df["player_id"]) if not ranked_df.empty else set()
            
            # All players in dim_player
            reconciled_records = []
            for idx, p_row in dim_player.iterrows():
                pid = p_row["player_id"]
                pname = p_row["player_name"]
                style = p_row["bowl_style"] if "bowl_style" in p_row and pd.notna(p_row["bowl_style"]) else "Unknown"
                pace_spin = p_row["pace_or_spin"] if "pace_or_spin" in p_row and pd.notna(p_row["pace_or_spin"]) else "UNKNOWN"
                
                if pid in active_pids:
                    # Player has pressure bowling data
                    bowler_record = ranked_df[ranked_df["player_id"] == pid].iloc[0].to_dict()
                    bowler_record["competition_scope"] = scope_name
                    bowler_record["bowling_style"] = style
                    bowler_record["has_pressure_data"] = True
                    
                    if bowler_record.get("is_pressure_ranked", False):
                        bowler_record["data_status"] = "QUALIFIED_RANKED"
                    elif bowler_record.get("hp_overs", 0) < min_ov:
                        bowler_record["data_status"] = "LIMITED_EVIDENCE"
                    else:
                        bowler_record["data_status"] = "NEGATIVE_IMPACT"
                        
                    reconciled_records.append(bowler_record)
                else:
                    # Check if player bowled in regulation deliveries in this scope
                    bowled_in_scope = (scope_df["bowler_id"] == pid).sum()
                    reconciled_records.append({
                        "player_id": pid,
                        "player_name": pname,
                        "competition_scope": scope_name,
                        "bowling_style": style,
                        "pace_or_spin": pace_spin,
                        "has_pressure_data": False,
                        "data_status": "NO_PRESSURE_BOWLING" if bowled_in_scope > 0 else "NON_BOWLER",
                        "hp_matches": 0,
                        "hp_balls": 0,
                        "hp_overs": 0.0,
                        "hp_runs_conceded": 0.0,
                        "hp_exp_runs_conceded": 0.0,
                        "hp_runs_saved": 0.0,
                        "hp_raw_runs_saved_per_6": np.nan,
                        "hp_raw_runs_saved_per_100": np.nan,
                        "hp_economy_rate": np.nan,
                        "hp_wickets": 0.0,
                        "hp_exp_wickets": 0.0,
                        "hp_wae": 0.0,
                        "hp_wae_per_6": np.nan,
                        "hp_wae_per_100": np.nan,
                        "hp_positive_matches": 0,
                        "hp_negative_matches": 0,
                        "hp_neutral_matches": 0,
                        "hp_positive_match_pct": np.nan,
                        "hp_negative_match_pct": np.nan,
                        "hp_mean_match_runs_saved": np.nan,
                        "hp_median_match_runs_saved": np.nan,
                        "hp_std_match_runs_saved": np.nan,
                        "hp_max_single_match_runs_saved": np.nan,
                        "hp_positive_match_share": np.nan,
                        "hp_single_match_share": np.nan,
                        "hp_sum_negative_runs_saved": 0.0,
                        "hp_worst_single_match_runs_saved": np.nan,
                        "hp_dots": 0,
                        "hp_boundaries_conceded": 0,
                        "hp_sixes_conceded": 0,
                        "hp_dot_pct": np.nan,
                        "hp_boundary_pct": np.nan,
                        "hp_six_pct": np.nan,
                        "hp_ci_low": np.nan,
                        "hp_ci_high": np.nan,
                        "hp_ci_width": np.nan,
                        "hp_eb_prior_mean": np.nan,
                        "hp_eb_shrinkage": np.nan,
                        "hp_posterior_mean": np.nan,
                        "hp_posterior_se": np.nan,
                        "hp_risk_adjusted_impact": np.nan,
                        "hp_lcb": np.nan,
                        "hp_ucb": np.nan,
                        "hp_lcb_95": np.nan,
                        "hp_ucb_95": np.nan,
                        "hp_wae_posterior_mean": np.nan,
                        "hp_wae_posterior_se": np.nan,
                        "hp_wae_crai": np.nan,
                        "is_pressure_ranked": False,
                        "pressure_rank": np.nan,
                        "is_wicket_ranked": False,
                        "pressure_wicket_rank": np.nan,
                    })
                    
            scope_full_df = pd.DataFrame(reconciled_records)
            all_metrics_list.append(scope_full_df)
            
            # Ranking slice (players with rank or activity)
            active_slice = scope_full_df[scope_full_df["has_pressure_data"]].copy()
            all_rankings_list.append(active_slice)
            print(f"  Scope [{scope_name}] master reconciled: {len(scope_full_df)} players ({scope_full_df['is_pressure_ranked'].sum()} ranked).")

        # 4. Save Master Parquet Tables
        print("\nSaving Parquet and DuckDB production artifacts...")
        final_metrics = pd.concat(all_metrics_list, ignore_index=True)
        final_matches = pd.concat(all_matches_list, ignore_index=True) if all_matches_list else pd.DataFrame()
        final_rankings = pd.concat(all_rankings_list, ignore_index=True) if all_rankings_list else pd.DataFrame()
        
        metrics_file = self.data_dir / "fact_player_pressure_bowling_metrics.parquet"
        matches_file = self.data_dir / "fact_player_pressure_bowling_matches.parquet"
        rankings_file = self.data_dir / "dim_player_pressure_bowling_ranking.parquet"
        
        final_metrics.to_parquet(metrics_file, index=False)
        final_matches.to_parquet(matches_file, index=False)
        final_rankings.to_parquet(rankings_file, index=False)
        
        print(f"Saved: {metrics_file} ({len(final_metrics)} rows)")
        print(f"Saved: {matches_file} ({len(final_matches)} rows)")
        print(f"Saved: {rankings_file} ({len(final_rankings)} rows)")
        
        # 5. Synchronize DuckDB
        import duckdb
        db_path = "data/app/analytics.duckdb"
        print(f"Synchronizing DuckDB analytical tables at {db_path}...")
        app_con = duckdb.connect(db_path)
        app_con.execute(f"CREATE OR REPLACE TABLE fact_player_pressure_bowling_metrics AS SELECT * FROM read_parquet('{metrics_file}')")
        app_con.execute(f"CREATE OR REPLACE TABLE fact_player_pressure_bowling_matches AS SELECT * FROM read_parquet('{matches_file}')")
        app_con.execute(f"CREATE OR REPLACE TABLE dim_player_pressure_bowling_ranking AS SELECT * FROM read_parquet('{rankings_file}')")
        
        cnt_m = app_con.execute("SELECT count(*) FROM fact_player_pressure_bowling_metrics").fetchone()[0]
        cnt_match = app_con.execute("SELECT count(*) FROM fact_player_pressure_bowling_matches").fetchone()[0]
        cnt_rank = app_con.execute("SELECT count(*) FROM dim_player_pressure_bowling_ranking").fetchone()[0]
        app_con.close()
        print(f"DuckDB tables verified: metrics={cnt_m}, matches={cnt_match}, rankings={cnt_rank}")
        
        return {
            "status": "SUCCESS",
            "metrics_rows": len(final_metrics),
            "matches_rows": len(final_matches),
            "rankings_rows": len(final_rankings),
            "validation": validation_results,
            "metrics_file": str(metrics_file),
            "matches_file": str(matches_file),
            "rankings_file": str(rankings_file)
        }


if __name__ == "__main__":
    pipeline = PressureBowlerPipeline()
    res = pipeline.run_pipeline()
    print("Pipeline Execution Complete:", res["status"])
