"""
Pressure Bowler Service
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Provides high-performance, scope-isolated queries from DuckDB for
the Unified Pressure Bowler Leaderboard, discovery statistics,
bowler pressure profiles, match-level breakdowns, and comparative analytics.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import duckdb
import pandas as pd
import numpy as np


class PressureBowlerService:
    DB_PATH = Path("data/app/analytics.duckdb")

    @classmethod
    def get_connection(cls):
        return duckdb.connect(str(cls.DB_PATH), read_only=True)

    @classmethod
    def get_leaderboard(
        cls,
        scope: str = "IPL_T20I",
        bowling_style: Optional[str] = None,
        pace_or_spin: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "pressure_rank",
        sort_dir: str = "asc",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieves the unified pressure bowler leaderboard for a given competition scope.
        Supports bidirectional sorting across run prevention, wicket creation, and opportunity dimensions.
        """
        con = cls.get_connection()
        query = """
            SELECT 
                player_id, player_name, bowling_style, pace_or_spin,
                pressure_rank, is_pressure_ranked,
                pressure_wicket_rank, is_wicket_ranked,
                data_status, has_pressure_data,
                hp_matches, hp_balls, hp_overs, hp_runs_conceded, hp_exp_runs_conceded,
                hp_runs_saved, hp_raw_runs_saved_per_6, hp_raw_runs_saved_per_100,
                hp_economy_rate, hp_wickets, hp_exp_wickets, hp_wae,
                hp_wae_per_6, hp_wae_per_100,
                hp_posterior_mean, hp_risk_adjusted_impact,
                hp_lcb, hp_ucb, hp_lcb_95, hp_ucb_95,
                hp_ci_low, hp_ci_high, hp_positive_matches, hp_negative_matches,
                hp_positive_match_pct, hp_negative_match_pct,
                hp_dot_pct, hp_boundary_pct, hp_six_pct,
                competition_scope
            FROM fact_player_pressure_bowling_metrics
            WHERE competition_scope = ?
        """
        params = [scope]

        if pace_or_spin and pace_or_spin.upper() != "ALL":
            query += " AND UPPER(pace_or_spin) = ?"
            params.append(pace_or_spin.upper())

        if bowling_style and bowling_style.upper() != "ALL":
            query += " AND LOWER(bowling_style) LIKE ?"
            params.append(f"%{bowling_style.lower()}%")

        if search:
            query += " AND LOWER(player_name) LIKE ?"
            params.append(f"%{search.lower()}%")

        # Sort order configuration
        is_desc = sort_dir.lower() == "desc"
        dir_sql = "DESC" if is_desc else "ASC"
        nulls_sql = "NULLS LAST"

        valid_sorts = {
            "pressure_rank": f"pressure_rank {dir_sql} {nulls_sql}, hp_risk_adjusted_impact DESC {nulls_sql}, hp_overs DESC",
            "pressure_wicket_rank": f"pressure_wicket_rank {dir_sql} {nulls_sql}, hp_wae DESC {nulls_sql}, hp_overs DESC",
            "hp_risk_adjusted_impact": f"hp_risk_adjusted_impact {dir_sql} {nulls_sql}, hp_posterior_mean {dir_sql} {nulls_sql}, hp_overs DESC",
            "hp_raw_runs_saved_per_6": f"hp_raw_runs_saved_per_6 {dir_sql} {nulls_sql}, hp_overs DESC",
            "hp_runs_saved": f"hp_runs_saved {dir_sql} {nulls_sql}, hp_overs DESC",
            "hp_wae": f"hp_wae {dir_sql} {nulls_sql}, hp_wickets DESC, hp_overs DESC",
            "hp_wickets": f"hp_wickets {dir_sql} {nulls_sql}, hp_wae DESC, hp_overs DESC",
            "hp_overs": f"hp_overs {dir_sql} {nulls_sql}, hp_matches DESC",
            "hp_matches": f"hp_matches {dir_sql} {nulls_sql}, hp_overs DESC",
            "hp_economy_rate": f"hp_economy_rate {dir_sql} {nulls_sql}, hp_overs DESC",
            "hp_positive_match_pct": f"hp_positive_match_pct {dir_sql} {nulls_sql}, hp_matches DESC",
            "player_name": f"player_name {dir_sql} {nulls_sql}",
        }
        order_clause = valid_sorts.get(sort_by, valid_sorts["pressure_rank"])
        
        # Count total
        count_query = f"SELECT count(*) FROM ({query}) sub"
        total_count = con.execute(count_query, params).fetchone()[0]

        query += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        df = con.execute(query, params).df()

        # Summary statistics from DuckDB
        summary_query = """
            SELECT 
                COUNT(*) as total_players,
                COUNT(CASE WHEN has_pressure_data THEN 1 END) as total_assessed,
                COUNT(CASE WHEN is_pressure_ranked THEN 1 END) as sufficient_evidence,
                COUNT(CASE WHEN hp_runs_saved > 0 THEN 1 END) as positive_runs_saved,
                COUNT(CASE WHEN hp_wae > 0 THEN 1 END) as positive_wae
            FROM fact_player_pressure_bowling_metrics
            WHERE competition_scope = ?
        """
        summ_row = con.execute(summary_query, [scope]).fetchone()
        
        # Count distinct pressure matches evaluated in this scope
        matches_count_query = """
            SELECT COUNT(DISTINCT match_id) 
            FROM fact_player_pressure_bowling_matches 
            WHERE competition_scope = ?
        """
        match_count = con.execute(matches_count_query, [scope]).fetchone()[0]
        
        con.close()

        records = df.replace({np.nan: None}).to_dict(orient="records")

        # Format user explanations for top records
        for r in records:
            r["explanation"] = cls._generate_bowler_explanation(r)

        return {
            "scope": scope,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "summary": {
                "total_bowlers_assessed": summ_row[1] if summ_row else 0,
                "positive_runs_saved_bowlers": summ_row[3] if summ_row else 0,
                "positive_wae_bowlers": summ_row[4] if summ_row else 0,
                "sufficient_evidence_bowlers": summ_row[2] if summ_row else 0,
                "pressure_matches_evaluated": match_count
            },
            "records": records
        }

    @classmethod
    def get_discovery_summary(cls, scope: str = "IPL_T20I") -> Dict[str, Any]:
        """
        Provides analytical summary metrics for the discovery cards.
        """
        con = cls.get_connection()
        summary_query = """
            SELECT 
                COUNT(*) as total_players,
                COUNT(CASE WHEN has_pressure_data THEN 1 END) as total_assessed,
                COUNT(CASE WHEN is_pressure_ranked THEN 1 END) as sufficient_evidence,
                COUNT(CASE WHEN hp_runs_saved > 0 THEN 1 END) as positive_runs_saved,
                COUNT(CASE WHEN hp_wae > 0 THEN 1 END) as positive_wae
            FROM fact_player_pressure_bowling_metrics
            WHERE competition_scope = ?
        """
        row = con.execute(summary_query, [scope]).fetchone()
        
        matches_query = """
            SELECT COUNT(DISTINCT match_id) 
            FROM fact_player_pressure_bowling_matches 
            WHERE competition_scope = ?
        """
        match_cnt = con.execute(matches_query, [scope]).fetchone()[0]
        con.close()

        return {
            "scope": scope,
            "total_bowlers_assessed": row[1] if row else 0,
            "positive_contributors": row[3] if row else 0,
            "positive_wae_bowlers": row[4] if row else 0,
            "sufficient_evidence_bowlers": row[2] if row else 0,
            "pressure_matches_evaluated": match_cnt
        }

    @classmethod
    def get_player_pressure_profile(cls, player_id: int, scope: str = "IPL_T20I") -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed pressure bowling profile for a single player across all scopes.
        """
        con = cls.get_connection()
        query = """
            SELECT * FROM fact_player_pressure_bowling_metrics
            WHERE player_id = ?
        """
        df = con.execute(query, [player_id]).df()
        con.close()

        if df.empty:
            return None

        # Scope-specific records
        scopes_dict = {}
        for _, row in df.iterrows():
            sc = row["competition_scope"]
            clean_row = row.replace({np.nan: None}).to_dict()
            clean_row["explanation"] = cls._generate_bowler_explanation(clean_row)
            scopes_dict[sc] = clean_row

        active_profile = scopes_dict.get(scope, scopes_dict.get("IPL_T20I", next(iter(scopes_dict.values()))))

        return {
            "player_id": player_id,
            "player_name": active_profile["player_name"],
            "bowling_style": active_profile["bowling_style"],
            "pace_or_spin": active_profile["pace_or_spin"],
            "active_scope": scope,
            "profile": active_profile,
            "all_scopes": scopes_dict
        }

    @classmethod
    def get_player_matches(cls, player_id: int, scope: str = "IPL_T20I", limit: int = 50) -> Dict[str, Any]:
        """
        Retrieves match-level pressure bowling evidence for explainability.
        """
        con = cls.get_connection()
        query = """
            SELECT 
                match_id, comp_name, season, match_date, format_scope, innings,
                hp_balls, hp_overs, hp_runs_conceded, hp_exp_runs_conceded, hp_runs_saved,
                hp_wickets, hp_exp_wickets, hp_wae, hp_economy_rate, hp_dot_pct,
                hp_avg_pressure, entry_score, entry_wickets, entry_rrr, entry_balls_rem,
                is_positive_impact
            FROM fact_player_pressure_bowling_matches
            WHERE player_id = ? AND competition_scope = ?
            ORDER BY match_date DESC, match_id DESC
            LIMIT ?
        """
        df = con.execute(query, [player_id, scope, limit]).df()
        con.close()

        matches = df.replace({np.nan: None}).to_dict(orient="records")
        return {
            "player_id": player_id,
            "scope": scope,
            "matches_count": len(matches),
            "matches": matches
        }

    @classmethod
    def compare_players(cls, player_ids: List[int], scope: str = "IPL_T20I", context: str = "ALL") -> Dict[str, Any]:
        """
        Evaluates 2 to 4 bowlers side-by-side on pressure run prevention and wicket creation.
        """
        if not player_ids:
            return {"candidates": []}

        placeholders = ",".join(["?"] * len(player_ids))
        con = cls.get_connection()
        query = f"""
            SELECT * FROM fact_player_pressure_bowling_metrics
            WHERE competition_scope = ? AND player_id IN ({placeholders})
        """
        params = [scope] + player_ids
        df = con.execute(query, params).df()
        con.close()

        records = df.replace({np.nan: None}).to_dict(orient="records")
        for r in records:
            r["explanation"] = cls._generate_bowler_explanation(r)

        return {
            "scope": scope,
            "candidate_count": len(records),
            "candidates": records
        }

    @classmethod
    def get_methodology_overview(cls) -> Dict[str, Any]:
        """
        Analytical methodology overview and validation results.
        """
        return {
            "engine": "Defensive Bowling Pressure Engine v1.0",
            "innings_1": "Opposition Restriction Pressure (Surge above venue par + death surge)",
            "innings_2": "Target Defence Pressure (Threat ratio r_par(w)/RRR + margin closeness)",
            "thresholds": {
                "primary_75th": {"innings_1": 6.91, "innings_2": 7.79},
                "emerging_75th": {"innings_1": 5.62, "innings_2": 8.41}
            },
            "validation": {
                "method": "Chronological holdout (Train <=2024, Test >=2025)",
                "status": "VALIDATED",
                "spearman_rho_runs_saved": 0.1291,
                "empirical_marginal_wicket_value": 7.96
            }
        }

    @classmethod
    def _generate_bowler_explanation(cls, r: Dict[str, Any]) -> str:
        """
        Generates clean, professional plain-English explanation of bowler performance under pressure.
        """
        overs = r.get("hp_overs") or 0.0
        if overs < 2.0:
            return "Not enough high-pressure bowling data to make a reliable assessment."

        rs = r.get("hp_runs_saved") or 0.0
        wae = r.get("hp_wae") or 0.0
        crai = r.get("hp_risk_adjusted_impact") or 0.0
        rank = r.get("pressure_rank")

        if rank and rank <= 10:
            if wae > 2.0 and rs > 20.0:
                return f"Elite dual-threat pressure bowler (Rank #{int(rank)}): consistently prevents scoring while creating high-value breakthrough wickets."
            elif rs > 20.0:
                return f"Premier defensive anchor (Rank #{int(rank)}): elite run suppression in demanding match situations (+{rs:.1f} runs saved above expectation)."
            else:
                return f"Top-tier pressure contributor (Rank #{int(rank)}) with demonstrated repeatability across matches."
        elif rank and rank <= 30:
            if wae > 2.0:
                return f"Proven pressure bowler (Rank #{int(rank)}): high wicket creation under pressure supported by solid run prevention."
            else:
                return f"Reliable defensive contributor (Rank #{int(rank)}): concedes fewer runs than expected when defending difficult positions."
        elif rs > 0.0 and overs >= 4.0:
            return "Positive pressure contributor with moderate sample size; delivers steady defensive containment."
        elif wae > 1.0:
            return "Wicket-hunting pressure specialist: creates breakthrough opportunities despite conceding runs in difficult phases."
        elif rs < 0.0 and overs >= 4.0:
            return "Experienced pressure bowler who has conceded more runs than expected in defensive phases."
        else:
            return "Limited match evidence; requires further scouting evaluation under defensive pressure."
