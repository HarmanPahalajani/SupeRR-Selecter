# SupeRR Intelligence — Data Dictionary & Canonical Schema

**Document Type:** Data Model, Field Semantics, Dimension & Fact Definitions  
**Product:** SupeRR Intelligence  
**Author:** Antigravity Engineering  
**Version:** 1.0.0

---

## 1. Raw Supplied Data Schema

### 1.1 `ball_by_ball.csv` (200,999 records)
- `match_id` (int): Unique match identifier.
- `innings` (int): 1, 2, or Super Over innings.
- `innings_ball_num` (int): Delivery sequence counter within innings.
- `over` (int): 0-indexed over number (0 = 1st over, 19 = 20th over).
- `ball_in_over` (int): 1-indexed ball in the current over.
- `batting_team_id` (int): ID of batting franchise/team.
- `bowling_team_id` (int): ID of bowling franchise/team.
- `striker_id` (int): ID of facing batter.
- `non_striker_id` (int): ID of non-facing batter.
- `bowler_id` (int): ID of delivery bowler.
- `runs` (int): Recorded delivery runs (0 to 6). Validated as batter runs.
- `extras_type` (str): Type of extras (e.g., `wide`, `overstep`, `legbye`, `bye`, `penalty`, `NULL`).
- `extras1_runs` (int): Extras magnitude.
- `extras_2_runs` (int): Secondary extras magnitude (observed in 36 records).
- `is_wicket` (bool): Whether a wicket fell on the delivery.
- `dismissal_type` (str): Dismissal category (`caught`, `bowled`, `lbw`, `run out`, `stumped`, `retired out`, `hit wicket`, etc.).
- `dismissed_player_id` (float/int): ID of the dismissed player.
- `is_four` (bool): Batter four hit.
- `is_six` (bool): Batter six hit.
- `bowl_speed` (float): Ball speed in km/h (flagged unreliable due to zeros/outliers).
- `bat_style` (str): Striker batting style (`RHB`, `LHB`).
- `bowl_style` (str): Bowler style (e.g., `Right-arm fast`, `Slow left-arm orthodox`).
- `pace_or_spin` (str): `Pace` or `Spin`.

### 1.2 `matches.csv` (883 records)
- `match_id` (int): Primary identifier.
- `competition_id` (int): Foreign key to `competitions.csv`.
- `date` (date): Match date (YYYY-MM-DD).
- `team1_id`, `team2_id` (int): Competing teams.
- `venue_country` (str): Match hosting nation.
- `first_inn_target` (int): Target for second innings.
- `revised_target` (float/int): DLS revised target if applicable.
- `first_inn_revised_overs` (float): Revised first innings overs.
- `second_inn_revised_overs` (float): Revised second innings overs.
- `match_result` (str): Outcome summary.

### 1.3 `competitions.csv` (141 records)
- `competition_id` (int): Primary key.
- `competition_name` (str): Name (e.g. `Indian Premier League`, `ICC Men's T20 World Cup`).
- `match_format` (str): `T20`, `ODI`, `Test`.
- `season` (str/int): Competition season year (e.g. `2024`).

### 1.4 `competition_team_player_mapping.csv` (6,413 records)
- `competition_id` (int): Competition ID.
- `team_id` (int): Team ID.
- `player_id` (int): Player ID.
- `player_name` (str): Canonical display name.

---

## 2. Canonical Warehouse Schema

### 2.1 Dimension Tables

#### `dim_player`
- `player_id` (PK, int): Canonical player ID.
- `player_name` (str): Display name.
- `bat_style` (str): Striker style (RHB/LHB).
- `bowl_style` (str): Bowling style.
- `pace_or_spin` (str): Pace / Spin.
- `is_wk` (bool): Known wicketkeeper indicator.
- `observed_roles` (list[str]): Inferred cricket roles (top_order, middle_order, finisher, powerplay_bowler, death_bowler, etc.).
- `role_confidence` (str): High / Medium / Low.
- `total_matches` (int): Career match appearances.

#### `dim_match`
- `match_id` (PK, int): Match identifier.
- `comp_id` (int): Competition ID.
- `comp_name` (str): Competition name.
- `format_scope` (str): `IPL`, `T20I`, or `OTHER_T20`.
- `season` (int): Season year.
- `match_date` (date): Date of match.
- `team1_id`, `team2_id` (int): Teams.
- `innings_limit_overs` (float): Match over length (standard 20.0 or revised).
- `has_delivery_data` (bool): True if deliveries exist.
- `is_completed` (bool): True if completed without abandonment.

### 2.2 Fact Tables

#### `fact_delivery_states`
- `match_id` (int), `innings` (int), `innings_ball_num` (int): Composite PK.
- `over` (int), `ball_in_over` (int).
- `legal_balls_bowled` (int): Legal deliveries bowled prior to this ball.
- `legal_balls_remaining` (int): Legal deliveries remaining in innings.
- `current_score` (int): Innings score prior to ball.
- `wickets_lost` (int): Wickets down prior to ball (0–9).
- `wickets_in_hand` (int): 10 - wickets_lost.
- `target_runs` (int/null): Target runs to win in chase.
- `runs_needed` (int/null): Target - current_score.
- `required_run_rate` (float/null): Runs needed / (balls remaining / 6).
- `current_run_rate` (float): Current score / (balls bowled / 6).
- `resource_consumed_pct` (float): Empirical resource usage proxy (0.0 to 1.0).
- `phase` (str): `powerplay` (overs 0-5), `middle` (overs 6-14), `death` (overs 15-19).
- `chase_pressure_index` (float): Bounded 0–10 pressure metric (Mallawa Arachchi et al.).
- `defensive_pressure_index` (float): Defending team pressure metric (0–10).
- `leverage_index` (float): Match leverage / swing potential (0–10).
- `striker_id`, `non_striker_id`, `bowler_id` (int).
- `batter_runs` (int): Verified batter runs (0-6).
- `bowler_conceded_runs` (int): Runs charged to bowler.
- `is_legal` (bool): True if not wide or overstep/no-ball.
- `is_bowler_wicket` (bool): Dismissal credited to bowler.
- `dismissed_player_id` (int/null).

#### `fact_player_metrics`
- `player_id` (PK, int).
- `player_name` (str).
- `primary_role` (str).
- `format_scope` (str): `IPL`, `T20I`, `COMBINED`.
- `matches_played` (int).
- `pressure_opportunities` (int): Deliveries under high pressure (>= 75th percentile).
- `raw_batting_runs` (int), `raw_balls_faced` (int), `batting_sr` (float), `batting_avg` (float).
- `raw_wickets` (int), `raw_balls_bowled` (int), `bowling_econ` (float), `bowling_sr` (float).
- `runs_above_expected` (float): Total context-adjusted batter runs.
- `runs_saved_above_expected` (float): Total context-adjusted runs saved by bowler.
- `wickets_above_expected` (float): Total wickets above expected credited to bowler.
- `pressure_batting_impact` (float): Pressure-weighted batting RAE per opportunity.
- `pressure_bowling_impact` (float): Pressure-weighted bowling runs saved per ball.
- `eb_posterior_impact` (float): Empirical Bayes regularized pressure impact.
- `eb_posterior_uncertainty` (float): Posterior standard error / credible interval width.
- `positive_match_frequency` (float): Proportion of matches with net positive pressure contribution.
- `format_portability_score` (float): Standardized score stability between IPL and T20I.
- `discovery_gap_percentile` (float): Undervalued metric: adjusted impact percentile minus conventional percentile.
- `confidence_tier` (str): `High Evidence`, `Moderate Evidence`, `Low Evidence / High Uncertainty`.
