import sqlite3
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

class AnalyticsService:
    DB_PATH = Path("data/app/analytics.duckdb")

    @classmethod
    def get_connection(cls):
        # Open in read-only mode so multiple endpoints can query concurrently
        return duckdb.connect(str(cls.DB_PATH), read_only=True)

    @classmethod
    def get_coverage(cls):
        con = cls.get_connection()
        total_deliveries = con.execute("SELECT count(*) FROM fact_delivery").fetchone()[0]
        # Calculate primary scope deliveries (IPL and T20I matches only)
        primary_deliveries = con.execute("SELECT count(*) FROM fact_delivery WHERE format_scope IN ('IPL', 'T20I')").fetchone()[0]
        ipl_deliveries = con.execute("SELECT count(*) FROM fact_delivery WHERE format_scope = 'IPL'").fetchone()[0]
        t20i_deliveries = con.execute("SELECT count(*) FROM fact_delivery WHERE format_scope = 'T20I'").fetchone()[0]
        total_matches = con.execute("SELECT count(*) FROM dim_match").fetchone()[0]
        primary_matches = con.execute("SELECT count(*) FROM dim_match WHERE format_scope IN ('IPL', 'T20I')").fetchone()[0]
        unique_players = con.execute("SELECT count(*) FROM fact_player_metrics").fetchone()[0]
        con.close()

        return {
            "total_deliveries": total_deliveries,
            "primary_scope_deliveries": primary_deliveries,
            "ipl_deliveries": ipl_deliveries,
            "t20i_deliveries": t20i_deliveries,
            "total_matches": total_matches,
            "primary_scope_matches": primary_matches,
            "unique_players": unique_players,
            "date_range": "2022-01-22 to 2026-11-01"
        }

    @classmethod
    def list_players(cls, role=None, format_scope=None, search=None, sort_by="overall_player_rating", discipline=None, eligible_only=False, confidence_tier=None, page=1, page_size=20):
        con = cls.get_connection()
        query = "SELECT * FROM fact_player_metrics WHERE 1=1"
        params = []

        if role:
            query += " AND UPPER(primary_role) = UPPER(?)"
            params.append(role)
        if search:
            query += " AND LOWER(player_name) LIKE ?"
            params.append(f"%{search.lower()}%")
        if discipline == "batting" or eligible_only == "batting":
            query += " AND batting_ranking_eligible = true"
        elif discipline == "bowling" or eligible_only == "bowling":
            query += " AND bowling_ranking_eligible = true"
        elif eligible_only:
            query += " AND (batting_ranking_eligible = true OR bowling_ranking_eligible = true)"

        if confidence_tier:
            query += " AND (UPPER(batting_confidence_tier) = UPPER(?) OR UPPER(bowling_confidence_tier) = UPPER(?) OR UPPER(confidence_tier) = UPPER(?))"
            params.extend([confidence_tier, confidence_tier, confidence_tier])

        valid_sort_cols = [
            "overall_player_rating", "batting_rating", "bowling_rating",
            "overall_batting_rating", "overall_bowling_rating", "eb_batting_impact",
            "eb_bowling_impact", "total_runs", "bowler_wickets", "batting_sr", "bowling_econ",
            "batting_ranking_score", "bowling_ranking_score"
        ]
        sort_col = sort_by if sort_by in valid_sort_cols else "overall_player_rating"
        query += f" ORDER BY {sort_col} DESC NULLS LAST"

        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)", 1).split("ORDER BY")[0]
        total = con.execute(count_query, params).fetchone()[0]

        # Pagination
        query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        df = con.execute(query, params).df()
        con.close()

        items = []
        for _, r in df.iterrows():
            bat_r = round(float(r['batting_rating']), 1) if pd.notnull(r.get('batting_rating')) else None
            bowl_r = round(float(r['bowling_rating']), 1) if pd.notnull(r.get('bowling_rating')) else None
            balls_f = int(r['balls_faced']) if pd.notnull(r.get('balls_faced')) else 0
            balls_b = int(r['legal_balls_bowled']) if pd.notnull(r.get('legal_balls_bowled')) else 0
            items.append({
                "player_id": int(r['player_id']),
                "player_name": str(r['player_name']),
                "primary_role": str(r['primary_role']),
                "bat_style": str(r['bat_style']),
                "bowl_style": str(r['bowl_style']),
                "total_matches": int(r['total_matches']),
                "balls_faced": balls_f,
                "total_runs": int(r['total_runs']) if pd.notnull(r.get('total_runs')) else 0,
                "balls_bowled": balls_b,
                "bowler_wickets": int(r['bowler_wickets']) if pd.notnull(r.get('bowler_wickets')) else 0,
                "overall_batting_rating": bat_r,
                "overall_bowling_rating": bowl_r,
                "batting_rating": bat_r,
                "bowling_rating": bowl_r,
                "batting_rating_status": str(r.get('batting_rating_status', 'UNRATED_INSUFFICIENT_DATA')),
                "bowling_rating_status": str(r.get('bowling_rating_status', 'UNRATED_INSUFFICIENT_DATA')),
                "batting_confidence_tier": str(r.get('batting_confidence_tier', 'INSUFFICIENT_DATA')),
                "bowling_confidence_tier": str(r.get('bowling_confidence_tier', 'INSUFFICIENT_DATA')),
                "batting_sample_size": int(r.get('batting_sample_size', 0)),
                "bowling_sample_size": int(r.get('bowling_sample_size', 0)),
                "batting_uncertainty": round(float(r['batting_uncertainty']), 3) if pd.notnull(r.get('batting_uncertainty')) else 0.5,
                "bowling_uncertainty": round(float(r['bowling_uncertainty']), 3) if pd.notnull(r.get('bowling_uncertainty')) else 0.5,
                "batting_ranking_eligible": bool(r.get('batting_ranking_eligible', False)),
                "bowling_ranking_eligible": bool(r.get('bowling_ranking_eligible', False)),
                "batting_official_rank": int(r['batting_official_rank']) if pd.notnull(r.get('batting_official_rank')) else None,
                "bowling_official_rank": int(r['bowling_official_rank']) if pd.notnull(r.get('bowling_official_rank')) else None,
                "overall_player_rating": round(float(r['overall_player_rating']), 1) if pd.notnull(r.get('overall_player_rating')) else None,
                "eb_batting_impact": round(float(r['eb_batting_impact']), 3) if pd.notnull(r.get('eb_batting_impact')) else None,
                "eb_bowling_impact": round(float(r['eb_bowling_impact']), 3) if pd.notnull(r.get('eb_bowling_impact')) else None,
                "batting_sr": round(float(r['batting_sr']), 1) if (pd.notnull(r.get('batting_sr')) and balls_f > 0) else None,
                "bowling_econ": round(float(r['bowling_econ']), 2) if (pd.notnull(r.get('bowling_econ')) and balls_b > 0) else None,
                "confidence_tier": str(r['confidence_tier']),
                "is_undervalued": bool(r['is_undervalued_talent'])
            })

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @classmethod
    def get_player_profile(cls, player_id: int):
        con = cls.get_connection()
        m_df = con.execute(f"SELECT * FROM fact_player_metrics WHERE player_id = {player_id}").df()
        if len(m_df) == 0:
            con.close()
            return None
        r = m_df.iloc[0]

        # Phase breakdown for player
        bat_phase_df = con.execute(f"""
            SELECT phase, count(*) as balls, sum(batter_runs) as runs, sum(rae) as total_rae
            FROM fact_delivery
            WHERE striker_id = {player_id}
            GROUP BY phase
        """).df()
        
        bowl_phase_df = con.execute(f"""
            SELECT phase, count(*) as balls, sum(bowler_conceded_runs) as runs, sum(is_bowler_wicket) as wickets
            FROM fact_delivery
            WHERE bowler_id = {player_id} AND is_legal_ball = true
            GROUP BY phase
        """).df()

        # Match timeline (last 10 matches)
        timeline_df = con.execute(f"""
            SELECT d.match_id, m.match_date, m.home_team, m.away_team,
                   sum(case when d.striker_id = {player_id} then d.batter_runs else 0 end) as bat_runs,
                   sum(case when d.striker_id = {player_id} then d.rae else 0 end) as bat_rae,
                   sum(case when d.bowler_id = {player_id} then d.is_bowler_wicket else 0 end) as wickets
            FROM fact_delivery d
            JOIN dim_match m ON d.match_id = m.match_id
            WHERE d.striker_id = {player_id} OR d.bowler_id = {player_id}
            GROUP BY d.match_id, m.match_date, m.home_team, m.away_team
            ORDER BY m.match_date DESC
            LIMIT 10
        """).df()
        con.close()

        bat_r = round(float(r['batting_rating']), 1) if pd.notnull(r.get('batting_rating')) else None
        bowl_r = round(float(r['bowling_rating']), 1) if pd.notnull(r.get('bowling_rating')) else None

        summary = {
            "player_id": int(r['player_id']),
            "player_name": str(r['player_name']),
            "primary_role": str(r['primary_role']),
            "bat_style": str(r['bat_style']),
            "bowl_style": str(r['bowl_style']),
            "total_matches": int(r['total_matches']),
            "overall_batting_rating": bat_r,
            "overall_bowling_rating": bowl_r,
            "batting_rating": bat_r,
            "bowling_rating": bowl_r,
            "batting_rating_status": str(r.get('batting_rating_status', 'UNRATED_INSUFFICIENT_DATA')),
            "bowling_rating_status": str(r.get('bowling_rating_status', 'UNRATED_INSUFFICIENT_DATA')),
            "batting_confidence_tier": str(r.get('batting_confidence_tier', 'INSUFFICIENT_DATA')),
            "bowling_confidence_tier": str(r.get('bowling_confidence_tier', 'INSUFFICIENT_DATA')),
            "batting_sample_size": int(r.get('batting_sample_size', 0)),
            "bowling_sample_size": int(r.get('bowling_sample_size', 0)),
            "balls_faced": int(r['balls_faced']) if pd.notnull(r.get('balls_faced')) else 0,
            "total_runs": int(r['total_runs']) if pd.notnull(r.get('total_runs')) else 0,
            "balls_bowled": int(r['legal_balls_bowled']) if pd.notnull(r.get('legal_balls_bowled')) else 0,
            "bowler_wickets": int(r['bowler_wickets']) if pd.notnull(r.get('bowler_wickets')) else 0,
            "batting_uncertainty": round(float(r['batting_uncertainty']), 3) if pd.notnull(r.get('batting_uncertainty')) else 0.5,
            "bowling_uncertainty": round(float(r['bowling_uncertainty']), 3) if pd.notnull(r.get('bowling_uncertainty')) else 0.5,
            "batting_ranking_eligible": bool(r.get('batting_ranking_eligible', False)),
            "bowling_ranking_eligible": bool(r.get('bowling_ranking_eligible', False)),
            "batting_official_rank": int(r['batting_official_rank']) if pd.notnull(r.get('batting_official_rank')) else None,
            "bowling_official_rank": int(r['bowling_official_rank']) if pd.notnull(r.get('bowling_official_rank')) else None,
            "overall_player_rating": round(float(r['overall_player_rating']), 1) if pd.notnull(r.get('overall_player_rating')) else None,
            "eb_batting_impact": round(float(r['eb_batting_impact']), 3) if pd.notnull(r.get('eb_batting_impact')) else None,
            "eb_bowling_impact": round(float(r['eb_bowling_impact']), 3) if pd.notnull(r.get('eb_bowling_impact')) else None,
            "batting_sr": round(float(r['batting_sr']), 1) if (pd.notnull(r.get('batting_sr')) and r['balls_faced'] > 0) else None,
            "bowling_econ": round(float(r['bowling_econ']), 2) if (pd.notnull(r.get('bowling_econ')) and r['legal_balls_bowled'] > 0) else None,
            "confidence_tier": str(r['confidence_tier']),
            "is_undervalued": bool(r['is_undervalued_talent'])
        }

        career = {
            "matches": int(r['total_matches']),
            "runs": int(r['total_runs']),
            "balls_faced": int(r['balls_faced']),
            "strike_rate": round(float(r['batting_sr']), 1) if (pd.notnull(r.get('batting_sr')) and r['balls_faced'] > 0) else None,
            "average": round(float(r['batting_avg']), 1) if (pd.notnull(r.get('batting_avg')) and r['dismissals'] > 0) else None,
            "fours": int(r['fours']),
            "sixes": int(r['sixes']),
            "wickets": int(r['bowler_wickets']),
            "balls_bowled": int(r['legal_balls_bowled']),
            "economy": round(float(r['bowling_econ']), 2) if (pd.notnull(r.get('bowling_econ')) and r['legal_balls_bowled'] > 0) else None,
            "bowling_strike_rate": round(float(r['bowling_sr']), 1) if (pd.notnull(r.get('bowling_sr')) and r['bowler_wickets'] > 0) else None
        }

        pressure = {
            "pressure_balls_faced": int(r['pressure_balls_faced']),
            "pressure_runs": int(r['pressure_runs']),
            "pressure_rae_per_ball": round(float(r['pressure_rae_per_ball']), 3) if pd.notnull(r.get('pressure_rae_per_ball')) else 0.0,
            "pressure_dot_pct": round(float(r['pressure_dot_pct']), 1) if (pd.notnull(r.get('pressure_dot_pct')) and r['pressure_balls_faced'] > 0) else None,
            "pressure_balls_bowled": int(r['pressure_balls_bowled']),
            "pressure_runs_saved_per_ball": round(float(r['pressure_runs_saved_per_ball']), 3) if pd.notnull(r.get('pressure_runs_saved_per_ball')) else 0.0,
            "eb_posterior_impact": round(float(r['eb_batting_impact'] if r['primary_role'].upper() != 'BOWLER' else r['eb_bowling_impact']), 3) if pd.notnull(r.get('eb_batting_impact')) else 0.0,
            "posterior_uncertainty": round(float(r['batting_uncertainty'] if r['primary_role'].upper() != 'BOWLER' else r['bowling_uncertainty']), 3) if pd.notnull(r.get('batting_uncertainty')) else 0.5
        }

        phases = {
            "batting": bat_phase_df.to_dict(orient="records"),
            "bowling": bowl_phase_df.to_dict(orient="records")
        }

        # Failure signature diagnostics
        failure_sigs = []
        if r['pressure_dot_pct'] > 50.0 and r['pressure_balls_faced'] >= 15:
            failure_sigs.append(f"High pressure dot ball vulnerability ({r['pressure_dot_pct']:.1f}% dots in pressure situations)")
        if r['batting_sr'] < 115.0 and r['balls_faced'] >= 50:
            failure_sigs.append(f"Sub-par scoring acceleration (Career SR {r['batting_sr']:.1f})")
        if r['bowling_econ'] > 9.5 and r['legal_balls_bowled'] >= 60:
            failure_sigs.append(f"Leakage prone under assault (Career Econ {r['bowling_econ']:.2f})")
        if r['confidence_tier'] in ['Limited Evidence', 'Insufficient Data', 'Low Evidence / High Uncertainty']:
            failure_sigs.append("Limited sample size across verified competitions (high uncertainty)")
        if not failure_sigs:
            failure_sigs.append("No critical structural vulnerabilities detected in observed sample")

        # Recruitment verdict
        is_high_bat = pd.notnull(r['batting_rating']) and r['batting_rating'] >= 75
        is_high_bowl = pd.notnull(r['bowling_rating']) and r['bowling_rating'] >= 75
        recruitment_label = "Shortlist" if is_high_bat or is_high_bowl else (
            "Further Scouting" if r['confidence_tier'] in ['Limited Evidence', 'Insufficient Data', 'Low Evidence / High Uncertainty'] else "Watchlist"
        )
        verdict = {
            "recommendation": recruitment_label,
            "evidence_strength": str(r['confidence_tier']),
            "best_role_fit": f"Observed {r['primary_role'].replace('_', ' ').title()}",
            "primary_asset": f"Pressure Batting Impact: +{r['eb_batting_impact']:.2f} Runs Above Expected/ball" if r['primary_role'].upper() != 'BOWLER' else f"Runs Saved: +{r['eb_bowling_impact']:.2f} Runs/ball",
            "primary_risk": failure_sigs[0]
        }

        return {
            "summary": summary,
            "career_stats": career,
            "pressure_stats": pressure,
            "phase_stats": phases,
            "matchup_stats": {
                "format_portability_score": round(float(r['format_portability_score']), 1) if pd.notnull(r['format_portability_score']) else None,
                "has_both_formats": bool(r['has_both_formats']),
                "recent_timeline": timeline_df.to_dict(orient="records")
            },
            "failure_signatures": failure_sigs,
            "recruitment_verdict": verdict
        }

    @classmethod
    def compare_players(cls, player_ids: list):
        con = cls.get_connection()
        ids_str = ",".join(str(p) for p in player_ids)
        df = con.execute(f"SELECT * FROM fact_player_metrics WHERE player_id IN ({ids_str})").df()
        con.close()

        players_data = []
        for _, r in df.iterrows():
            bat_r = round(float(r['batting_rating']), 1) if pd.notnull(r.get('batting_rating')) else None
            bowl_r = round(float(r['bowling_rating']), 1) if pd.notnull(r.get('bowling_rating')) else None
            players_data.append({
                "player_id": int(r['player_id']),
                "player_name": str(r['player_name']),
                "primary_role": str(r['primary_role']),
                "overall_batting_rating": bat_r,
                "overall_bowling_rating": bowl_r,
                "batting_rating": bat_r,
                "bowling_rating": bowl_r,
                "batting_ranking_eligible": bool(r.get('batting_ranking_eligible', False)),
                "bowling_ranking_eligible": bool(r.get('bowling_ranking_eligible', False)),
                "eb_batting_impact": round(float(r['eb_batting_impact']), 3) if pd.notnull(r.get('eb_batting_impact')) else None,
                "eb_bowling_impact": round(float(r['eb_bowling_impact']), 3) if pd.notnull(r.get('eb_bowling_impact')) else None,
                "batting_sr": round(float(r['batting_sr']), 1) if (pd.notnull(r.get('batting_sr')) and r['balls_faced'] > 0) else None,
                "bowling_econ": round(float(r['bowling_econ']), 2) if (pd.notnull(r.get('bowling_econ')) and r['legal_balls_bowled'] > 0) else None,
                "balls_faced": int(r['balls_faced']),
                "balls_bowled": int(r['legal_balls_bowled']),
                "total_matches": int(r['total_matches']),
                "confidence_tier": str(r['confidence_tier'])
            })

        # Winner by Scenario logic - strictly compares ELIGIBLE players!
        scenarios = {}
        # Scenario 1: Best high-pressure batter
        bat_cand = df[df['batting_ranking_eligible'] == True]
        if len(bat_cand) > 0:
            best_bat = bat_cand.sort_values(by="batting_ranking_score", ascending=False).iloc[0]
            scenarios["Best High-Pressure Batter"] = {
                "winner_id": int(best_bat['player_id']),
                "winner_name": str(best_bat['player_name']),
                "metric": f"{best_bat['batting_rating']:.1f} Rating (+{best_bat['eb_batting_impact']:.3f} Runs Above Expected/ball)"
            }
        else:
            scenarios["Best High-Pressure Batter"] = {
                "winner_id": None,
                "winner_name": "No qualifying batter",
                "metric": "Insufficient evidence"
            }

        # Scenario 2: Best death/pressure bowler
        bowl_cand = df[df['bowling_ranking_eligible'] == True]
        if len(bowl_cand) > 0:
            best_bowl = bowl_cand.sort_values(by="bowling_ranking_score", ascending=False).iloc[0]
            scenarios["Best Pressure Bowler"] = {
                "winner_id": int(best_bowl['player_id']),
                "winner_name": str(best_bowl['player_name']),
                "metric": f"{best_bowl['bowling_rating']:.1f} Rating (+{best_bowl['eb_bowling_impact']:.3f} Runs Saved/ball)"
            }
        else:
            scenarios["Best Pressure Bowler"] = {
                "winner_id": None,
                "winner_name": "No qualifying bowler",
                "metric": "Insufficient evidence"
            }

        # Scenario 3: Highest sample confidence
        best_sample = df.sort_values(by="total_matches", ascending=False).iloc[0]
        scenarios["Highest Statistical Confidence"] = {
            "winner_id": int(best_sample['player_id']),
            "winner_name": str(best_sample['player_name']),
            "metric": f"{int(best_sample['total_matches'])} Matches"
        }

        return {
            "players": players_data,
            "head_to_head_matrix": {p['player_name']: p for p in players_data},
            "winner_by_scenario": scenarios
        }

    @classmethod
    def get_undervalued_talents(cls):
        con = cls.get_connection()
        df = con.execute("""
            SELECT player_id, player_name, primary_role, total_matches, batting_avg, batting_sr,
                   eb_batting_impact, discovery_gap, confidence_tier, batting_rating
            FROM fact_player_metrics
            WHERE is_undervalued_talent = true AND batting_ranking_eligible = true
            ORDER BY discovery_gap DESC
            LIMIT 15
        """).df()
        con.close()

        items = []
        for _, r in df.iterrows():
            items.append({
                "player_id": int(r['player_id']),
                "player_name": str(r['player_name']),
                "primary_role": str(r['primary_role']),
                "total_matches": int(r['total_matches']),
                "batting_avg": round(float(r['batting_avg']), 1),
                "batting_sr": round(float(r['batting_sr']), 1),
                "eb_batting_impact": round(float(r['eb_batting_impact']), 3),
                "batting_rating": round(float(r['batting_rating']), 1) if pd.notnull(r.get('batting_rating')) else None,
                "discovery_gap": round(float(r['discovery_gap']), 1),
                "confidence_tier": str(r['confidence_tier'])
            })
        return items

    @classmethod
    def get_rankings(cls, category="batters", limit=20):
        con = cls.get_connection()
        if category == "batters":
            query = f"""
                SELECT player_id, player_name, primary_role, total_matches, balls_faced, total_runs,
                       batting_avg, batting_sr, eb_batting_impact, batting_rating,
                       batting_rating AS overall_batting_rating, batting_confidence_tier AS confidence_tier,
                       batting_sample_size, batting_uncertainty, batting_ranking_score, batting_official_rank
                FROM fact_player_metrics
                WHERE batting_ranking_eligible = true
                ORDER BY batting_ranking_score DESC
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT player_id, player_name, primary_role, total_matches, legal_balls_bowled, bowler_wickets,
                       bowling_econ, bowling_sr, eb_bowling_impact, bowling_rating,
                       bowling_rating AS overall_bowling_rating, bowling_confidence_tier AS confidence_tier,
                       bowling_sample_size, bowling_uncertainty, bowling_ranking_score, bowling_official_rank
                FROM fact_player_metrics
                WHERE bowling_ranking_eligible = true
                ORDER BY bowling_ranking_score DESC
                LIMIT {limit}
            """
        df = con.execute(query).df()
        con.close()

        results = []
        for rank, (_, r) in enumerate(df.iterrows(), 1):
            item = {}
            for k, v in r.items():
                if pd.isnull(v):
                    item[k] = None
                elif isinstance(v, (np.integer, int)):
                    item[k] = int(v)
                elif isinstance(v, (np.floating, float)):
                    item[k] = round(float(v), 2)
                else:
                    item[k] = str(v)
            item['rank'] = rank
            results.append(item)
        return results
