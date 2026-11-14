"""
Pressure Performer Service
Part of SupeRR Intelligence — Pressure Performer Intelligence

Provides high-performance, scope-isolated queries from DuckDB for
the Unified Pressure Performer Leaderboard, discovery statistics,
player pressure profiles, and comparative analytics.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import duckdb
import pandas as pd
import numpy as np


class PressurePerformerService:
    DB_PATH = Path("data/app/analytics.duckdb")

    @classmethod
    def get_connection(cls):
        return duckdb.connect(str(cls.DB_PATH), read_only=True)

    @classmethod
    def get_leaderboard(
        cls,
        scope: str = "IPL_T20I",
        context: str = "ALL",
        classification: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "pressure_rank",
        sort_dir: str = "asc",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieves the unified pressure performer leaderboard for a given competition scope and context.
        Supports bidirectional sorting across all performance and opportunity dimensions.
        """
        con = cls.get_connection()
        query = """
            SELECT 
                player_id, player_name, bat_style, bowl_style, is_wk,
                classification, evidence_level, pressure_rank, is_pressure_ranked,
                hp_matches, hp_balls, hp_runs, hp_exp_runs, hp_rae,
                hp_raw_rae_per_100, hp_posterior_mean, hp_risk_adjusted_impact,
                hp_lcb, hp_ucb, hp_lcb_95, hp_ucb_95,
                hp_ci_low, hp_ci_high, hp_positive_matches, hp_negative_matches,
                hp_positive_match_pct, hp_negative_match_pct, hp_strike_rate,
                hp_boundary_pct, hp_dot_pct, hp_dismissals, explanation,
                competition_scope, pressure_context
            FROM fact_player_pressure_metrics
            WHERE competition_scope = ? AND pressure_context = ?
        """
        params = [scope, context]

        if classification and classification != "ALL":
            query += " AND classification = ?"
            params.append(classification)

        if search:
            query += " AND LOWER(player_name) LIKE ?"
            params.append(f"%{search.lower()}%")

        # Sort order configuration
        is_desc = sort_dir.lower() == "desc"
        dir_sql = "DESC" if is_desc else "ASC"
        nulls_sql = "NULLS LAST"

        valid_sorts = {
            "pressure_rank": f"pressure_rank {dir_sql} {nulls_sql}, hp_risk_adjusted_impact DESC {nulls_sql}, hp_balls DESC",
            "hp_risk_adjusted_impact": f"hp_risk_adjusted_impact {dir_sql} {nulls_sql}, hp_posterior_mean {dir_sql} {nulls_sql}, hp_balls DESC",
            "hp_lcb": f"hp_risk_adjusted_impact {dir_sql} {nulls_sql}, hp_posterior_mean {dir_sql} {nulls_sql}, hp_balls DESC",
            "hp_posterior_mean": f"hp_posterior_mean {dir_sql} {nulls_sql}, hp_risk_adjusted_impact {dir_sql} {nulls_sql}, hp_balls DESC",
            "hp_raw_rae_per_100": f"hp_raw_rae_per_100 {dir_sql} {nulls_sql}, hp_balls DESC",
            "hp_rae": f"hp_rae {dir_sql} {nulls_sql}, hp_balls DESC",
            "hp_positive_match_pct": f"hp_positive_match_pct {dir_sql} {nulls_sql}, hp_matches DESC",
            "hp_negative_match_pct": f"hp_negative_match_pct {dir_sql} {nulls_sql}, hp_matches DESC",
            "hp_strike_rate": f"hp_strike_rate {dir_sql} {nulls_sql}, hp_balls DESC",
            "hp_balls": f"hp_balls {dir_sql} {nulls_sql}, hp_matches DESC",
            "hp_matches": f"hp_matches {dir_sql} {nulls_sql}, hp_balls DESC",
            "player_name": f"player_name {dir_sql} {nulls_sql}",
        }
        order_clause = valid_sorts.get(sort_by, valid_sorts["pressure_rank"])
        
        # Count total
        count_query = f"SELECT count(*) FROM ({query}) sub"
        total_count = con.execute(count_query, params).fetchone()[0]

        query += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        df = con.execute(query, params).df()
        con.close()

        # Clean NaN to None for JSON compliance
        records = df.replace({np.nan: None}).to_dict(orient="records")

        return {
            "scope": scope,
            "context": context,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "players": records
        }

    @classmethod
    def get_discovery_summary(cls, scope: str = "IPL_T20I") -> Dict[str, Any]:
        """
        Returns objective leaderboard summary statistics and top verified pressure performers.
        Eliminates promotional tier counts (Elite, Reliable, Hidden, Struggles).
        """
        con = cls.get_connection()
        
        # Aggregate statistics from fact_player_pressure_metrics
        stats_row = con.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE hp_balls > 0) AS total_batters_assessed,
                COUNT(*) FILTER (WHERE hp_raw_rae_per_100 > 0) AS positive_batters,
                COUNT(*) FILTER (WHERE is_pressure_ranked = TRUE) AS ranked_batters,
                COUNT(*) FILTER (WHERE hp_raw_rae_per_100 < 0) AS below_baseline_batters
            FROM fact_player_pressure_metrics
            WHERE competition_scope = ? AND pressure_context = 'ALL'
        """, [scope]).fetchone()

        total_assessed = stats_row[0] if stats_row else 0
        positive_batters = stats_row[1] if stats_row else 0
        ranked_batters = stats_row[2] if stats_row else 0
        below_baseline = stats_row[3] if stats_row else 0

        # High pressure matches count
        match_count = con.execute("""
            SELECT COUNT(DISTINCT match_id)
            FROM fact_player_pressure_matches
            WHERE competition_scope = ?
        """, [scope]).fetchone()[0]

        # Top 10 Verified Performers on Unified Leaderboard
        top_df = con.execute("""
            SELECT player_id, player_name, pressure_rank, evidence_level,
                   hp_matches, hp_balls, hp_runs, hp_rae, hp_raw_rae_per_100,
                   hp_posterior_mean, hp_risk_adjusted_impact, hp_lcb,
                   hp_positive_matches, hp_negative_matches, hp_positive_match_pct,
                   hp_strike_rate, explanation
            FROM fact_player_pressure_metrics
            WHERE competition_scope = ? AND pressure_context = 'ALL' 
              AND is_pressure_ranked = TRUE
            ORDER BY pressure_rank ASC
            LIMIT 10
        """, [scope]).df()
        
        con.close()
        top_performers = top_df.replace({np.nan: None}).to_dict(orient="records")

        return {
            "scope": scope,
            "total_batters_assessed": total_assessed,
            "positive_batters": positive_batters,
            "sufficient_evidence_batters": ranked_batters,
            "total_pressure_matches": match_count,
            "below_baseline_batters": below_baseline,
            "top_performers": top_performers,
            # Backward-compatible dictionary so older callers don't fail:
            "category_counts": {
                "Ranked Pressure Performer": ranked_batters,
                "Positive Batters": positive_batters,
                "Total Batters": total_assessed,
            }
        }

    @classmethod
    def get_player_pressure_profile(cls, player_id: int) -> Optional[Dict[str, Any]]:
        """
        Returns complete pressure performance profile across all contexts and competition scopes.
        """
        con = cls.get_connection()
        p_df = con.execute("""
            SELECT * FROM fact_player_pressure_metrics
            WHERE player_id = ?
            ORDER BY competition_scope ASC, pressure_context ASC
        """, [player_id]).df()
        
        if p_df.empty:
            con.close()
            return None

        # Matches log (up to 20 recent high-pressure matches)
        m_df = con.execute("""
            SELECT * FROM fact_player_pressure_matches
            WHERE player_id = ?
            ORDER BY match_date DESC
            LIMIT 20
        """, [player_id]).df()
        
        con.close()

        records_by_context = {}
        for _, row in p_df.iterrows():
            key = f"{row['competition_scope']}_{row['pressure_context']}"
            records_by_context[key] = row.replace({np.nan: None}).to_dict()

        # Primary ALL summary record
        primary_all = records_by_context.get("IPL_T20I_ALL") or records_by_context.get(list(records_by_context.keys())[0])

        matches_list = m_df.replace({np.nan: None}).to_dict(orient="records")

        return {
            "player_id": player_id,
            "player_name": primary_all["player_name"],
            "primary_rank": primary_all.get("pressure_rank"),
            "is_pressure_ranked": primary_all.get("is_pressure_ranked", False),
            "primary_evidence_level": primary_all["evidence_level"],
            "primary_classification": primary_all["classification"],
            "explanation": primary_all.get("explanation"),
            "contexts": records_by_context,
            "recent_pressure_matches": matches_list
        }

    @classmethod
    def get_player_matches(cls, player_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns full match evidence log for a player.
        """
        con = cls.get_connection()
        m_df = con.execute("""
            SELECT * FROM fact_player_pressure_matches
            WHERE player_id = ?
            ORDER BY match_date DESC
            LIMIT ?
        """, [player_id, limit]).df()
        con.close()
        return m_df.replace({np.nan: None}).to_dict(orient="records")

    @classmethod
    def compare_players(
        cls,
        player_ids: List[int],
        scope: str = "IPL_T20I",
        context: str = "ALL"
    ) -> List[Dict[str, Any]]:
        """
        Returns side-by-side comparative pressure metrics for multiple players.
        """
        if not player_ids:
            return []
            
        con = cls.get_connection()
        placeholders = ",".join(["?"] * len(player_ids))
        query = f"""
            SELECT * FROM fact_player_pressure_metrics
            WHERE player_id IN ({placeholders}) 
              AND competition_scope = ? 
              AND pressure_context = ?
            ORDER BY pressure_rank ASC NULLS LAST, hp_risk_adjusted_impact DESC NULLS LAST
        """
        params = list(player_ids) + [scope, context]
        df = con.execute(query, params).df()
        con.close()
        return df.replace({np.nan: None}).to_dict(orient="records")

    @classmethod
    def get_methodology_overview(cls) -> Dict[str, Any]:
        """
        Returns the analytical parameters, threshold distributions, and validation metrics.
        """
        import json
        metrics_file = Path("artifacts/reports/pressure_performer_validation_metrics.json")
        val_metrics = {}
        if metrics_file.exists():
            with open(metrics_file, "r", encoding="utf-8") as f:
                val_metrics = json.load(f)

        return {
            "engine": "Dynamic Match-Situation Pressure Engine (Validated)",
            "ranking_framework": "Unified Empirical Bayes Conservative Risk-Adjusted Impact (CRAI)",
            "primary_thresholds_75th": {
                "first_innings": 5.83,
                "chase": 8.60,
                "percentile": "75th Percentile"
            },
            "emerging_thresholds_75th": {
                "first_innings": 6.59,
                "chase": 7.99,
                "percentile": "75th Percentile"
            },
            "validation_summary": val_metrics
        }
