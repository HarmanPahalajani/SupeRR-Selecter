# SupeRR Intelligence — Unified Pressure Performer Leaderboard
## Final Analytical Closure & Methodological Verification Report

---

### Executive Summary

This report delivers complete analytical closure for the **Unified Pressure Performer Leaderboard** within SupeRR Intelligence. In accordance with analytical verification requirements, this document provides empirical proof, mathematical justifications, source-code lineages, population reconciliations, and delivery-level attribution audits across five key areas:

1. **CRAI Uncertainty Penalty Sensitivity Analysis**: Empirical sensitivity tests of the uncertainty multiplier $k \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$ across full-sample rank stability, Top 10/25 membership churn, and chronological out-of-sample predictive performance ($\le 2024 \to 2025$, $N=202$ qualifying players). Multiplier $k=0.50$ is selected as a calibrated production trade-off.
2. **Pressure-Engine Lineage & Model Distinction**: Exact source-code file paths, class names, functions, and mathematical formulas demonstrating how `DynamicPressureEngine` governs delivery-level pressure without data leakage. Concrete separation between the pressure threshold engine and the ball-level expected-batter-runs model is proven, confirming no direct target leakage or circular computation.
3. **Emerging Population Reconciliation**: Mathematical reconciliation of all **172 Emerging participants** against the **114 assessed batters**. Complete itemized accounting of the remaining **58 unassessed players** (13 specialist bowlers who never batted, 45 batters who faced zero qualifying high-pressure deliveries), with dual-scope players rigorously tracked.
4. **Batting Pressure RAE Integrity & Wide Ball Attribution Audit**: Comprehensive delivery-level audit distinguishing arithmetic correctness from delivery eligibility. Wides are strictly bowling events where batters face no delivery and cannot score off the bat; they contribute **zero** to `expected_batter_runs` ($0.0$), **zero** to `hp_balls` ($0$), and **zero** to batting RAE ($0.0$). Legal deliveries resulting in byes or leg-byes retain valid negative batting RAE ($0 - \text{expected\_batter\_runs}$), while wide runs remain accounted for in bowler-conceded runs.
5. **Recomputed Production Metrics**: Full re-aggregation of all 5,034 player-context metrics, 21,004 match evidence records, and leaderboard rankings across Primary and Emerging scopes, fully synchronized in DuckDB and verified across all target players.

---

### 1. CRAI Uncertainty Penalty Sensitivity Analysis

The **Conservative Risk-Adjusted Impact (CRAI)** is the official ranking metric on the Unified Pressure Performer Leaderboard:
$$\text{CRAI}(k) = \theta_{\text{post}, i} - k \cdot \sigma_{\text{post}, i}$$
where $\theta_{\text{post}, i}$ is the Empirical Bayes posterior mean runs above expected per 100 high-pressure balls, $\sigma_{\text{post}, i}$ is the posterior standard error, and $k$ is the uncertainty penalty multiplier.

We tested five penalty values $k \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$ across the recomputed production dataset (`IPL_T20I` combined scope, `ALL` pressure context, $N=207$ qualified ranked Primary batters). 

> [!NOTE]
> **Cohort Distinction:**
> The **207-player cohort** analyzed in Sections 1.1–1.3 represents the full-dataset production population of Primary batters who met qualification criteria ($\ge 25$ HP balls, $\ge 3$ matches, and $\mu_{\text{post}} > 0.0$ on the complete dataset through 2026 following the wide-ball correction). This is strictly distinct from the **202-player forward evaluation cohort** analyzed in Section 1.4, which consists of players meeting qualification criteria on historical data ($\le 2024$) with $\ge 10$ high-pressure deliveries in forward calendar year 2025.

#### 1.1 Top 10 Leaderboard Composition across Multipliers $k$ (Independently Sorted)

Every column below is independently sorted in descending CRAI order for that multiplier:

| Rank | $k = 0.00$ (Posterior Mean) | $k = 0.25$ (Quarter-Sigma) | $k = 0.50$ (Production Trade-Off) | $k = 0.75$ (Three-Quarter) | $k = 1.00$ (One-Sigma LCB) |
|:---:|---|---|---|---|---|
| **#1** | Kyle Mayers (+34.8) | Phil Salt (+31.6) | **Phil Salt (+29.1)** | Phil Salt (+26.6) | Phil Salt (+24.1) |
| **#2** | Phil Salt (+34.1) | Kyle Mayers (+31.4) | **Kyle Mayers (+28.1)** | Kyle Mayers (+24.8) | Kyle Mayers (+21.5) |
| **#3** | Shamar Springer (+29.9) | Shamar Springer (+27.0) | **Shamar Springer (+24.2)** | Shamar Springer (+21.3) | Suryakumar Yadav (+19.5) |
| **#4** | Gudakesh Motie (+28.8) | Gudakesh Motie (+26.1) | **Gudakesh Motie (+23.5)** | Suryakumar Yadav (+20.9) | Shamar Springer (+18.5) |
| **#5** | Ijaz Ahmadzai (+27.8) | Ijaz Ahmadzai (+24.9) | **Suryakumar Yadav (+22.3)** | Gudakesh Motie (+20.9) | Gudakesh Motie (+18.2) |
| **#6** | Vipraj Nigam (+27.0) | Vipraj Nigam (+24.2) | **Ijaz Ahmadzai (+22.0)** | Ijaz Ahmadzai (+19.0) | Naman Dhir (+16.7) |
| **#7** | Naman Dhir (+25.7) | Suryakumar Yadav (+23.7) | **Vipraj Nigam (+21.4)** | Naman Dhir (+18.9) | Ijaz Ahmadzai (+16.1) |
| **#8** | Suryakumar Yadav (+25.1) | Naman Dhir (+23.5) | **Naman Dhir (+21.2)** | Vipraj Nigam (+18.6) | Jason Holder (+16.1) |
| **#9** | Travis Head (+24.0) | Jason Holder (+22.0) | **Jason Holder (+20.0)** | Jason Holder (+18.0) | Vipraj Nigam (+15.8) |
| **#10** | Prabhsimran Singh (+24.0) | Travis Head (+21.5) | **Abhishek Sharma (+19.1)** | Tim David (+17.3) | Tim David (+15.7) |

#### 1.2 Top Cohort Stability & Overlap vs Production ($k = 0.50$) across $N = 207$ Batters

| Multiplier $k$ | Top 10 Overlap with $k=0.50$ | Top 10 Jaccard Similarity | Top 25 Overlap with $k=0.50$ | Top 25 Jaccard Similarity |
|:---:|:---:|:---:|:---:|:---:|
| **$k = 0.00$** | 8 / 10 (80.0%) | 0.667 | 24 / 25 (96.0%) | 0.923 |
| **$k = 0.25$** | 9 / 10 (90.0%) | 0.818 | 25 / 25 (100.0%) | 1.000 |
| **$k = 0.50$ (Production)** | **10 / 10 (100.0%)** | **1.000** | **25 / 25 (100.0%)** | **1.000** |
| **$k = 0.75$** | 9 / 10 (90.0%) | 0.818 | 23 / 25 (92.0%) | 0.852 |
| **$k = 1.00$** | 9 / 10 (90.0%) | 0.818 | 22 / 25 (88.0%) | 0.786 |

#### 1.3 Full-Sample Rank Stability across All $N = 207$ Qualified Primary Batters

| Multiplier Comparison | Spearman Rank Correlation ($\rho$) | Kendall Rank Correlation ($\tau$) | Analytical Interpretation |
|---|:---:|:---:|---|
| **$k = 0.00$ vs $k = 0.50$** | 0.9876 | 0.9068 | High overall concordance; unpenalized posterior mean inflates smaller samples (e.g. Kyle Mayers 25 balls at #1). |
| **$k = 0.25$ vs $k = 0.50$** | 0.9968 | 0.9556 | Extremely high concordance; 100% Top 25 membership retention. |
| **$k = 0.50$ vs $k = 0.75$** | 0.9971 | 0.9572 | Extremely high concordance; progressive promotion of high-volume veterans (Suryakumar #4, Tim David #10). |
| **$k = 0.50$ vs $k = 1.00$** | 0.9916 | 0.9234 | Strong concordance; one-sigma penalty heavily discounts emerging small-sample performers. |

#### 1.4 Chronological Out-of-Sample Predictive Validation

To assess future performance prediction, a rolling chronological backtest was conducted:
- **Historical Basis**: Matches played up to and including **2024**.
- **Forward Horizon**: Matches played in calendar year **2025**.
- **Evaluation Cohort**: All batters facing $\ge 10$ high-pressure deliveries in 2025 ($N = 202$ qualifying players).
- **Baseline Cohort Prevalence**: 55.4% of players achieved positive future RAE in 2025.

| Uncertainty Multiplier $k$ | Out-of-Sample Spearman $\rho$ | $p$-value | Out-of-Sample Kendall $\tau$ | Precision @ 10 | Precision @ 20 | Lift over Baseline (@20) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$k = 0.00$** | 0.1815 | 0.0097 | 0.1255 | 80.0% | 85.0% | +29.6 percentage points |
| **$k = 0.25$** | 0.1877 | 0.0075 | 0.1296 | 80.0% | 80.0% | +24.6 percentage points |
| **$k = 0.50$ (Production)** | **0.1933** | **0.0058** | **0.1335** | **80.0%** | **80.0%** | **+24.6 percentage points** |
| **$k = 0.75$** | 0.1955 | 0.0053 | 0.1356 | 80.0% | 85.0% | +29.6 percentage points |
| **$k = 1.00$** | 0.1986 | 0.0046 | 0.1387 | 70.0% | 85.0% | +29.6 percentage points |

*(Note on Lift Terminology: All lift figures represent absolute **percentage-point increases** above the 55.4% baseline prevalence, e.g. 80.0% - 55.4% = +24.6 percentage points, equivalent to a +44.4% relative lift).*

#### 1.5 Multiplier Justification: $k = 0.50$ as a Calibrated Production Trade-Off

Rather than asserting that $k = 0.50$ is uniquely mathematically optimal (as $k = 0.75$ and $k = 1.00$ achieve slightly higher Spearman correlation and 85% Precision@20), **$k = 0.50$ is adopted as a calibrated production trade-off**:
1. **Balance Between Sample Size and Ability**: A full $1.0\sigma$ penalty ($k = 1.00$) excessively discounts smaller-sample performers who excelled in their opportunities; for example, Shamar Springer drops from #3 ($k=0.50$, CRAI +24.2) to #4 ($k=1.00$, CRAI +18.5) and Gudakesh Motie drops from #4 to #5 behind high-volume veteran Suryakumar Yadav (who rises to #3 with CRAI +19.5 on 499 balls), while Abhishek Sharma (+19.1 at $k=0.50$) is pushed out of the Top 10 to #13. Conversely, Kyle Mayers retains #2 across both $k=0.50$ (+28.1) and $k=1.00$ (+21.5), demonstrating that elite rate performance (+136.7 raw RAE/100) withstands one-sigma shrinkage.
2. **Protection Against Small-Sample Flukes**: A zero penalty ($k = 0.00$) ignores variance entirely and allows unregularized small samples to claim #1 (e.g., Kyle Mayers at #1 with 25 balls over Phil Salt's 103 balls).
3. **Positive but Modest Forward Association**: Across the separate 202-player forward evaluation cohort ($\le 2024 \to 2025$), $k = 0.50$ demonstrates a modest positive association with future performance that is statistically significant ($\rho = 0.1933, p = 0.0058$, Kendall $\tau = 0.1335$) and achieves **80.0% Precision@20** (16 / 20 positive future RAE vs a 55.4% baseline prevalence, representing a **+24.6 percentage-point lift**). We describe this as a modest positive association that is statistically significant in the reported chronological evaluation, not as proof of strong predictive power.
4. **Leaderboard Robustness**: Across the 207-player qualified Primary population, Top 25 membership is **100.0% identical** between $k = 0.25$ and $k = 0.50$ (25 / 25 retained, Jaccard 1.000) and retains **92.0%** at $k = 0.75$ (23 / 25 retained, Jaccard 0.852), demonstrating high structural stability around the production trade-off.

---

### 2. Validated Pressure-Engine Lineage & Decoupled Model Architecture

#### 2.1 Exact Source-Code Lineage

The pressure computation is entirely executed by the previously validated `DynamicPressureEngine`. No ad-hoc, secondary, or weighted combination formulas are introduced.

| Pipeline Stage | Source File Path | Class / Function Name | Exact Inputs & Data Fields Used | Output Field Produced |
|---|---|---|---|---|
| **Innings 1 Pressure** | `backend/analytics/pressure/engine.py:273` | `DynamicPressureEngine.compute_first_innings_pressure()` | `pre_ball_legal_balls`, `legal_balls_remaining`, `pre_ball_score`, `pre_ball_wickets`, `wickets_in_hand`, `current_run_rate`, `resource_consumed_pct`, `venue_par_score` | `pressure_index` (Innings 1) |
| **Innings 2 Chase Pressure** | `backend/analytics/pressure/engine.py:344` | `DynamicPressureEngine.compute_second_innings_pressure()` | `target_runs`, `revised_target`, `max_legal_balls`, `second_inn_revised_overs`, `pre_ball_legal_balls`, `wickets_in_hand`, `required_run_rate` | `pressure_index` (Innings 2) |
| **High-Pressure Opportunity Filter** | `backend/analytics/pressure_performers/pressure_opportunities.py:33` | `tag_high_pressure_deliveries()` | `innings`, `pressure_index`, `is_super_over` | `is_high_pressure` (Boolean), `pressure_context` |
| **Delivery Contribution** | `backend/analytics/pressure_performers/contribution.py:13` | `compute_delivery_contributions()` | `batter_runs`, `expected_batter_runs`, `extras_wide_runs`, `is_legal_ball`, `is_wicket`, `striker_id`, `dismissed_player_id` | `rae`, `striker_wae`, `is_dot`, `is_boundary` |
| **Match Aggregation** | `backend/analytics/pressure_performers/match_aggregation.py:15` | `aggregate_player_matches()` | Filtered `hp_deliveries` (`is_high_pressure == True`) | Player-match records with aggregated `hp_balls`, `hp_runs`, `hp_rae` |
| **Empirical Bayes & CRAI** | `backend/analytics/pressure_performers/reliability.py:43` | `compute_career_pressure_metrics()` | Match-level `hp_rae`, `hp_balls`, career summaries | `hp_posterior_mean`, `hp_posterior_se`, `hp_risk_adjusted_impact` |

#### 2.2 Mathematical Specifications of the Engine

1. **Innings 1 (First-Innings Acceleration & Death Overs)**:
   $$\text{Shortfall}(t) = \frac{\text{Par}_{\text{venue}} - \mathbb{E}[S_{\text{final}} \mid \text{State}(t)]}{\sigma_{\text{venue}}}$$
   $$P_{\text{inn1}}(t) = \text{clip}\left(\frac{10.0}{1.0 + \exp(-1.05 \cdot \text{Shortfall}(t))}, 0.2, 9.8\right)$$
   where $\mathbb{E}[S_{\text{final}}]$ is predicted by the Ridge regression model (`expected_score_ridge.joblib`, regularization $\alpha = 100.0$).
2. **Innings 2 (Decoupled Monotonic Chase Model)**:
   $$P(1) = \text{clip}\left(10.0 \cdot \frac{\text{Initial RRR}}{13.5}, 1.0, 9.5\right)$$
   $$\Delta C(t) = \text{RRR}(t) - \text{Initial RRR}$$
   $$\text{Progress}(t) = \frac{\text{Balls Elapsed}(t)}{B_{\max}}$$
   $$\text{WicketDeficit}(t) = \frac{10 - \text{Wickets in Hand}(t)}{10.0}$$
   $$\text{Stress}(t) = \Delta C(t) \cdot \text{Progress}(t) + 1.50 \cdot \text{WicketDeficit}(t)$$
   $$P_{\text{chase}}(t) = \text{clip}\left(\frac{10.0}{1.0 + \left(\frac{10.0}{P(1)} - 1.0\right) \cdot \exp(-0.45 \cdot \text{Stress}(t))}, 0.2, 9.9\right)$$
3. **Threshold Qualification**:
   Deliveries qualify as high pressure when pre-delivery $P \ge 75\text{th percentile}$:
   - Primary Scope (`IPL_T20I`): Innings 1 $\ge 5.83$; Innings 2 $\ge 8.60$.
   - Emerging Scope: Innings 1 $\ge 6.59$; Innings 2 $\ge 7.99$.

#### 2.3 Structural Decoupling: Pressure Engine vs Expected Batter Runs Model

There is strict architectural decoupling between the macro-state pressure engine and the ball-level expected runs model:
- **`DynamicPressureEngine` (Macro-State Tension Engine)**: Determines **WHEN** a delivery qualifies as high pressure based solely on pre-delivery match state (wickets down, runs needed, balls remaining, venue par score). It has no knowledge of individual player identity and never predicts single-ball outcomes.
- **`expected_batter_runs` (Ball-Level Neutral Baseline Model)**: Determines **WHAT** a neutral batter is expected to score on that specific delivery given phase, over, ball number, and wickets in hand.
- **Batting RAE**: Evaluates individual performance strictly on qualified legal opportunities:
  $$\text{RAE} = \text{batter\_runs} - \text{expected\_batter\_runs}$$
This architecture guarantees **no direct target leakage, no circular computation, and clean structural decoupling** between pre-delivery situation severity and post-delivery execution quality.

---

### 3. Complete Emerging Population Reconciliation

The master population reconciliation identified **172 Emerging competition participants** in `data/processed/fact_delivery_canonical.parquet`. The Unified Pressure Performer Leaderboard report identified **114 assessed batters**. The remaining **58 participants** are reconciled below.

#### 3.1 Population Reconciliation Summary

```
Total Emerging Participants: 172
├── Assessed in Emerging High-Pressure Batting (hp_balls >= 1): 114
│   ├── Officially Ranked Batters (hp_balls >= 15, hp_matches >= 2, CRAI > 0): 4
│   ├── Unranked Positive Batters with Limited Evidence: 38
│   └── Below Baseline Emerging Batters (Raw RAE <= 0): 72
└── Unassessed in Emerging High-Pressure Batting: 58
    ├── Specialist Bowlers (0 balls faced, active bowler): 13
    └── Batters with Zero High-Pressure Opportunities (1 to 174 balls faced, 0 HP balls): 45
Reconciliation: 114 + 13 + 45 = 172 participants (100.0% reconciled)
```

#### 3.2 Breakdown of Scope Membership for the 58 Unassessed Players

- **Dual-Scope Participants** (IPL/T20I + Emerging): **33 players**
  - Active in both senior cricket and Emerging tournaments. While they may have faced pressure in IPL/T20I, they faced zero qualifying high-pressure deliveries in the Emerging tournament.
  - Examples: Abhishek Sharma (faced 66 Emerging balls, 0 in high pressure), Nuwanidu Fernando (faced 174 Emerging balls, 0 in high pressure), Towhid Hridoy (faced 69 Emerging balls, 0 in high pressure), Sai Kishore (specialist bowler, 24 balls bowled, 0 balls faced), Rahul Chahar (3 balls faced, 0 in high pressure).
- **Emerging-Only Participants**: **25 players**
  - Competed strictly in Emerging tournaments and recorded zero qualifying high-pressure balls.
  - Examples: Yashodha Lanka (93 regular balls faced, 0 in high pressure), Bukkapatnam Siddharth (specialist bowler, 6 balls bowled, 0 balls faced).

The complete itemized roster of all 58 unassessed players is archived at `artifacts/reports/emerging_58_unassessed_reconciliation.csv`.

---

### 4. Delivery-Level Batting RAE & Wide Ball Attribution Audit

#### 4.1 Distinguishing Arithmetic Correctness from Delivery Eligibility

In cricket scoring and performance attribution:
1. **Batter Runs (`batter_runs`)**: Only runs struck off the bat (or running off bat-strokes) belong to the batter.
2. **Extras (`extras_wide_runs`, `extras_noball_runs`, `extras_bye_legbye_runs`)**: Conceded by the bowling team.
3. **Delivery Eligibility for Batting Evaluation**:
   - **Wide Deliveries (`extras_wide_runs > 0`, `is_legal_ball == False`)**: Wides are bowling events. The batter does not face the delivery, cannot hit the ball, and is not given an opportunity to score off the bat. Therefore, **a wide is not an eligible batting opportunity**.
   - An equation evaluating $\text{batter\_runs} - \text{expected\_batter\_runs} = 0 - 1.20 = -1.20$ is **arithmetically trivial but attributionally defective**: it docks a batter 1.20 runs for a ball bowled out of reach by the opposition.
   - On wide deliveries: $\text{expected\_batter\_runs} = 0.0$, $\text{hp\_balls} = 0$, and $\text{rae} = 0.0$.
4. **Valid Batting Attribution for Byes and Leg-Byes**:
   - A legal delivery resulting in a bye or leg-bye (`is_legal_ball == True`, `extras_bye_legbye_runs > 0`, `batter_runs == 0`) **is an eligible batting opportunity**. The batter faced a legal ball and failed to score off the bat. Here, $\text{expected\_batter\_runs} > 0$ and $\text{rae} = 0 - \text{expected\_batter\_runs} < 0$ is a valid batting penalty.
5. **Preservation of Bowler Conceded Runs**:
   - In the bowling pipeline (`backend/analytics/pressure_bowlers/contribution.py`), wide runs remain fully included:
     $$\text{bowler\_conceded\_runs} = \text{batter\_runs} + \text{extras\_wide\_runs} + \text{extras\_noball\_runs}$$

#### 4.2 Quantification of Wide Ball Changes & Leaderboard Impact

- **Previous Defect**: In the original scoring pipeline, 2,021 high-pressure wide deliveries (1,967 Primary, 54 Emerging) carried non-zero `expected_batter_runs` and negative RAE, inappropriately docking runs from batters.
- **Affected Players**: Across the 124 evaluated Primary batters, exactly **112 players** had suffered negative penalties from opposition wides.
- **Removed Penalty**: The average RAE penalty removed was **+10.516 runs** (median: +6.033 runs, min: +0.668 runs, max: +66.225 runs).
- **Invariance of Balls Faced**: Total balls faced (`hp_balls`) remained strictly unchanged ($\Delta = 0.00$) across all players because wides were already excluded from `is_legal_ball`.
- **Leaderboard Position Shifts**:
  - Among the 124 previously ranked qualifying batters, **111 leaderboard positions shifted** (89.5% churn).
  - Across the 112 directly affected batters: **40 improved rank**, **59 dropped rank** (due to sharper gains from peers or newly qualifying entries), and **13 retained identical rank** (including Phil Salt at #1, Kyle Mayers at #2, Shamar Springer at #3, Gudakesh Motie at #4, Suryakumar Yadav at #5, Ijaz Ahmadzai at #6, Vipraj Nigam at #7, Naman Dhir at #8, Rilee Rossouw at #41, M Shahrukh Khan at #42, Jonny Bairstow at #64, Shreyas Iyer at #67, Jamie Overton at #75).
- **Expansion of Qualified Leaderboard**:
  - Crucially, zeroing out wide penalties unmasked genuine positive contributions for **83 additional batters** whose posterior means had previously been artificially suppressed below zero ($\mu_{\text{post}} \le 0.0$).
  - As a result, the official qualifying ranked Primary leaderboard expanded from **124 to 207 batters** ($\ge 25$ HP balls, $\ge 3$ matches, and $\mu_{\text{post}} > 0.0$).
- **Production System Confirmation**:
  - The production DuckDB database (`fact_player_pressure_metrics`), the FastAPI backend (`/api/v1/pressure-performers/leaderboard`), and the Next.js frontend (`/discovery?tab=pressure`) display the recomputed post-fix values with zero discrepancy.
  - The corrected dataset is permanently preserved in `data/processed/fact_delivery_scored.parquet` and `data/app/analytics.duckdb`.

The table below documents the before and after metrics for key affected Primary batters on the Unified Leaderboard:

| Player Name | Pre RAE | Post RAE | RAE Gain ($\Delta$) | Pre Post. Mean | Post Post. Mean | Pre CRAI | Post CRAI | Pre Rank | Post Rank | Rank Shift |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Namboori Tilak Varma** | +9.66 | +75.89 | **+66.22** | +0.91 | +10.40 | -1.55 | +7.94 | #94 | #66 | **+28** |
| **Dinesh Karthik** | +9.65 | +51.19 | **+41.55** | +2.04 | +15.98 | -1.65 | +12.28 | #95 | #39 | **+56** |
| **Nicholas Pooran** | +16.37 | +54.54 | **+38.17** | +2.61 | +10.90 | -0.34 | +7.94 | #82 | #65 | **+17** |
| **Tim David** | +57.42 | +95.29 | **+37.87** | +12.42 | +22.11 | +9.22 | +18.91 | #24 | #13 | **+11** |
| **Sherfane Rutherford** | +11.01 | +47.98 | **+36.97** | +2.36 | +14.48 | -1.26 | +10.85 | #89 | #47 | **+42** |
| **Shivam Dube** | +67.04 | +103.08 | **+36.04** | +12.83 | +20.97 | +9.83 | +17.96 | #21 | #16 | **+5** |
| **Marcus Stoinis** | +48.10 | +83.32 | **+35.21** | +9.98 | +18.78 | +6.83 | +15.62 | #35 | #24 | **+11** |
| **Rashid Khan** | +44.84 | +78.10 | **+33.27** | +9.45 | +17.98 | +6.26 | +14.79 | #38 | #28 | **+10** |
| **Rinku Singh** | +35.79 | +67.99 | **+32.20** | +6.95 | +14.73 | +3.87 | +11.64 | #53 | #45 | **+8** |
| **Rovman Powell** | +48.52 | +80.43 | **+31.90** | +6.69 | +12.03 | +4.12 | +9.46 | #50 | #53 | -3 |
| **Shimron Hetmyer** | +17.40 | +46.44 | **+29.03** | +3.08 | +10.20 | -0.01 | +7.10 | #80 | #71 | **+9** |
| **Ayush Badoni** | +33.11 | +61.33 | **+28.22** | +7.59 | +15.83 | +4.23 | +12.46 | #49 | #38 | **+11** |
| **David Miller** | +47.63 | +74.84 | **+27.21** | +7.99 | +13.66 | +5.15 | +10.82 | #43 | #48 | -5 |
| **Andre Russell** | +31.14 | +54.78 | **+23.63** | +8.29 | +16.56 | +4.65 | +12.92 | #47 | #35 | **+12** |
| **Abhishek Sharma** | +40.58 | +64.20 | **+23.63** | +13.18 | +23.08 | +9.22 | +19.10 | #25 | #10 | **+15** |
| **Suryakumar Yadav** | +121.06 | +143.35 | **+22.29** | +20.45 | +25.12 | +17.66 | +22.32 | #5 | #5 | 0 |
| **Dasun Shanaka** | +24.83 | +46.48 | **+21.65** | +5.96 | +13.08 | +2.46 | +9.57 | #61 | #52 | **+9** |
| **Heinrich Klaasen** | +69.59 | +89.24 | **+19.65** | +14.26 | +19.44 | +11.15 | +16.33 | #15 | #22 | -7 |
| **Moeen Ali** | +6.22 | +24.86 | **+18.63** | +1.08 | +8.64 | -2.75 | +4.80 | #104 | #90 | **+14** |
| **Glenn Maxwell** | +22.68 | +40.21 | **+17.53** | +8.42 | +17.84 | +4.05 | +13.45 | #52 | #34 | **+18** |
| **Jason Holder** | +51.04 | +68.13 | **+17.09** | +19.98 | +24.02 | +15.98 | +20.02 | #9 | #9 | 0 |
| **Dhruv Jurel** | +41.74 | +58.23 | **+16.49** | +16.63 | +20.41 | +12.71 | +16.49 | #22 | #20 | **+2** |
| **Ashutosh Sharma** | +44.75 | +58.69 | **+13.94** | +19.41 | +23.21 | +15.19 | +18.99 | #10 | #11 | -1 |
| **Sunil Narine** | +25.74 | +38.55 | **+12.81** | +17.15 | +22.26 | +12.20 | +17.31 | #23 | #18 | **+5** |
| **Travis Head** | +30.39 | +39.99 | **+9.60** | +20.24 | +24.03 | +15.15 | +18.95 | #11 | #12 | -1 |
| **Finn Allen** | +21.90 | +28.87 | **+6.97** | +18.79 | +22.09 | +13.04 | +16.34 | #20 | #21 | -1 |

#### 4.3 Audited Sample Deliveries with Extras

The table below shows delivery-level attribution following the wide-ball correction:

| Match ID | Innings | Over.Ball | Striker | Delivery Type | Batter Runs | Wide | Bye/LegBye | Expected Batter Runs | Batting RAE | Bowler Conceded | Bowler Saved Runs |
|:---:|:---:|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **13511** | 1.0 | 7.4 | Eoin Morgan | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.1537 |
| **13511** | 1.0 | 8.1 | Eoin Morgan | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.0705 |
| **13511** | 1.0 | 8.2 | Eoin Morgan | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.0763 |
| **13512** | 1.0 | 10.1 | Moeen Ali | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.0403 |
| **13512** | 1.0 | 10.4 | Moeen Ali | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.0457 |
| **13512** | 2.0 | 15.2 | Fabian Allen | Leg-Bye | **0** | 0 | 1 | **1.2458** | **-1.2458** | 0 | +1.3547 |
| **13512** | 2.0 | 16.2 | Romario Shepherd | Leg-Bye | **0** | 0 | 1 | **1.4440** | **-1.4440** | 0 | +1.4775 |
| **13512** | 2.0 | 16.6 | Romario Shepherd | Leg-Bye | **0** | 0 | 1 | **1.4566** | **-1.4566** | 0 | +1.4779 |
| **13512** | 2.0 | 18.6 | Romario Shepherd | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.0380 |
| **13512** | 2.0 | 20.1 | Akeal Hosein | Wide | **0** | 1 | 0 | **0.0000** | **0.0000** | 1 | +0.0254 |

#### 4.4 Authoritative High-Pressure Delivery Reconciliation & Scope Accounting

A comparison across documentation drafts identified two separate delivery metrics requiring reconciliation:
1. The **373-delivery threshold delta** between unpartitioned global filtering (50,052) and scope-isolated production filtering (49,679).
2. The **176-delivery scope allocation discrepancy** between drafted figures (193,812 Primary / 7,149 Emerging) and canonical production headers (193,988 Primary / 6,973 Emerging).

##### 1. Reconciling the 176-Delivery Scope Partition & Exact Match 39809 Audit:
- **Exact Identification of 176 Deliveries:**
  An exact audit across all 883 matches in `data/processed/fact_delivery_scored.parquet` identifies precisely one fixture with exactly 176 records:
  - **Match ID:** `39809`
  - **Competition ID:** `2793`
  - **Competition Name:** `Pakistan in New Zealand T20I Series 2025` (Match 2, 2025-03-18 at Dunedin; New Zealand won by 5 wickets).
- **Match 39809 Delivery Breakdown:**
  - **Total Delivery Rows:** **176 rows** (Innings 1: 92 rows, Innings 2: 84 rows).
  - **Legal Balls Faced (`is_legal_ball == True`):** **169 balls** (Innings 1: 90 legal balls, Innings 2: 79 legal balls).
  - **Extras (Non-Legal Deliveries):** **7 deliveries** (6 wide deliveries yielding 6 wide runs, 1 no-ball yielding 1 no-ball run).
  - **Terminology Confirmation:** The 176-record scope difference refers strictly to **total delivery rows** (not legal balls). The dataset scope partitions total regular deliveries ($193,988 + 6,973 = 200,961$ total delivery rows).
- **Scope Allocation Root Cause:**
  - In a preliminary documentation draft, Match 39809 was inadvertently aggregated into the non-primary cohort in text tables, yielding $6,973 + 176 = 7,149$ and $193,988 - 176 = 193,812$.
  - In the canonical production database (`dim_competition.parquet`, `dim_match.parquet`, `fact_delivery_scored.parquet`), Match 39809 is strictly marked `is_primary_scope = True` and `format_scope = T20I`.
  - **Complete Definition of Emerging Scope:** Emerging scope is strictly defined as the two Asian Cricket Council age-group / development tournaments:
    1. `Mens T20 Emerging Teams Asia Cup 2024` (comp_id 2670): 3,519 total delivery rows across 15 matches.
    2. `Asia Cup Rising Stars 2025` (comp_id 3289): 3,454 total delivery rows across 15 matches.
    - Total: **30 matches, 6,973 total delivery rows, and 172 unique participants** (67 Emerging-Only, 105 Dual-Scope).
  - All references to other leagues (e.g. CPL, MLC, BBL) were early scoping concepts; the canonical dataset exclusively contains the 30 ACC tournament matches for Emerging scope. The drafted figures of 193,812 and 7,149 are formally labeled as superseded drafting artifacts.

##### 2. Reconciling the 373 High-Pressure Qualification Difference:
The 373-delivery delta between 50,052 and 49,679 occurs strictly from **cohort-isolated empirical thresholding** vs **unpartitioned global filtering**:
- **Dataset Version Integrity:** Both figures derive from the identical canonical dataset `fact_delivery_scored.parquet` containing **200,961 regular deliveries** (105,727 first-innings and 95,234 second-innings deliveries; 0 Super Overs).
- **Unpartitioned Benchmark (50,052):** Evaluated by an audit script (`scripts/verify_item4.py`) that applied Primary thresholds ($P_i \ge 5.83$ Inn 1, $P_i \ge 8.60$ Inn 2) across all 200,961 deliveries.
- **Production Scope-Isolated (49,679):** The production pipeline ([`backend/analytics/pressure_performers/pressure_opportunities.py`](file:///c:/Users/Win11%20Pro/Desktop/Rajasthan%20Royals%20Competition/backend/analytics/pressure_performers/pressure_opportunities.py)) isolates cohorts:
  - **Primary Scope ($N = 193,988$):** Innings 1 $\ge 5.83$, Innings 2 $\ge 8.60 \implies \mathbf{47,935\text{ qualifying deliveries}}$.
  - **Emerging Scope ($N = 6,973$):** Calibrated to empirical 75th percentiles of the Emerging cohort: Innings 1 $\ge 6.59$, Innings 2 $\ge 7.99 \implies \mathbf{1,744\text{ qualifying deliveries}}$.
  - **Total Production Canonical:** $47,935 + 1,744 = \mathbf{49,679\text{ qualifying deliveries}}$.
- **Exact Arithmetic Breakdown of the 373 Emerging Difference ($2,117 - 1,744 = 373$):**
  - Emerging deliveries passing Primary thresholds (5.83 / 8.60): **2,117 deliveries**
  - Emerging deliveries passing calibrated Emerging thresholds (6.59 / 7.99): **1,744 deliveries**
  - *Innings 1 ($5.83 \le P_i < 6.59$):* $+587$ balls excluded by higher Emerging acceleration threshold ($6.59$ vs $5.83$).
  - *Innings 2 ($7.99 \le P_i < 8.60$):* $-214$ balls included by lower Emerging chase threshold ($7.99$ vs $8.60$).
  - *Net:* $+587 - 214 = \mathbf{+373\text{ deliveries}}$.

##### Authoritative Published Delivery Counts by Explicit Scope:

| Scope Definition | Competitions Included | Innings 1 Threshold | Innings 2 Threshold | Total Deliveries Evaluated | Qualifying High-Pressure Deliveries | Authoritative Production Status |
|---|---|:---:|:---:|:---:|:---:|---|
| **Primary Scope** | IPL (87,673) & Bilateral/ICC T20I (106,315) | $P_i \ge 5.83$ | $P_i \ge 8.60$ | **193,988** | **47,935** | **Authoritative Production Primary Count** |
| **Emerging Scope** | ACC Emerging Asia Cup 2024 & Rising Stars 2025 | $P_i \ge 6.59$ | $P_i \ge 7.99$ | **6,973** | **1,744** | **Authoritative Production Emerging Count** |
| **Combined Canonical (Global)** | Complete 883-match canonical database | *Partitioned* | *Partitioned* | **200,961** | **49,679** | **Authoritative Global Production Count** |
| *Superseded Draft Allocation* | *Draft misattribution of Match 39809 (NZ v PAK)* | *Partitioned* | *Partitioned* | *193,812 / 7,149* | *49,679* | *Historical Drafting Artifact (Superseded)* |
| *Unpartitioned Global Benchmark* | *Cross-cohort uncalibrated application* | $P_i \ge 5.83$ | $P_i \ge 8.60$ | 200,961 | *50,052* | *Audit Benchmark (Superseded)* |

---

### 5. Recomputed Production Leaderboard for Target Players

The table below reflects the updated production leaderboard (`IPL_T20I` Combined Scope, `ALL` Pressure Context):

| Player | Unified Rank | HP Balls | HP Matches | Raw RAE/100b | Posterior Mean | CRAI ($k=0.50$) | HP Strike Rate | Positive Matches % | Analytical Evidence Status |
|---|---|---|---|---|---|---|---|---|---|
| **Phil Salt** | **#1** | 103 | 9 | +58.3 | +34.1 | +29.1 | 219.4 | 55.6% (5/9) | Ranked Pressure Performer |
| **Kyle Mayers** | **#2** | 25 | 5 | +136.7 | +34.8 | +28.1 | 272.0 | 100.0% (5/5) | Ranked Pressure Performer |
| **Shamar Springer** | **#3** | 61 | 7 | +65.5 | +29.9 | +24.2 | 185.2 | 71.4% (5/7) | Ranked Pressure Performer |
| **Gudakesh Motie** | **#4** | 85 | 15 | +53.3 | +28.8 | +23.5 | 168.2 | 46.7% (7/15) | Ranked Pressure Performer |
| **Suryakumar Yadav** | **#5** | 499 | 37 | +28.7 | +25.1 | +22.3 | 173.9 | 70.3% (26/37) | Ranked Pressure Performer |
| **Ijaz Ahmadzai** | **#6** | 54 | 4 | +65.0 | +27.8 | +22.0 | 183.3 | 75.0% (3/4) | Ranked Pressure Performer |
| **Vipraj Nigam** | **#7** | 66 | 7 | +56.5 | +27.0 | +21.4 | 193.9 | 71.4% (5/7) | Ranked Pressure Performer |
| **Naman Dhir** | **#8** | 142 | 17 | +38.7 | +25.7 | +21.2 | 179.6 | 76.5% (13/17) | Ranked Pressure Performer |
| **Jason Holder** | **#9** | 213 | 27 | +32.0 | +24.0 | +20.0 | 162.0 | 63.0% (17/27) | Ranked Pressure Performer |
| **Abhishek Sharma** | **#10** | 207 | 17 | +31.0 | +23.1 | +19.1 | 181.6 | 70.6% (12/17) | Ranked Pressure Performer |
| **Ashutosh Sharma** | **#11** | 182 | 19 | +32.2 | +23.2 | +19.0 | 178.0 | 57.9% (11/19) | Ranked Pressure Performer |
| **Travis Head** | **#12** | 95 | 8 | +42.1 | +24.0 | +18.9 | 194.7 | 75.0% (6/8) | Ranked Pressure Performer |
| **Tim David** | **#13** | 360 | 34 | +26.5 | +22.1 | +18.9 | 179.4 | 58.8% (20/34) | Ranked Pressure Performer |
| **Prabhsimran Singh** | **#14** | 77 | 7 | +46.2 | +24.0 | +18.6 | 215.6 | 71.4% (5/7) | Ranked Pressure Performer |
| **Jitesh Sharma** | **#15** | 195 | 21 | +30.6 | +22.5 | +18.4 | 161.5 | 66.7% (14/21) | Ranked Pressure Performer |
| **Shivam Dube** | **#16** | 421 | 38 | +24.5 | +21.0 | +18.0 | 159.4 | 57.9% (22/38) | Ranked Pressure Performer |
| **Shai Hope** | **#17** | 163 | 16 | +32.0 | +22.3 | +17.9 | 173.6 | 62.5% (10/16) | Ranked Pressure Performer |
| **Sunil Narine** | **#18** | 102 | 20 | +37.8 | +22.3 | +17.3 | 166.7 | 50.0% (10/20) | Ranked Pressure Performer |
| **Andrew Balbirnie** | **#19** | 33 | 5 | +72.8 | +23.1 | +16.7 | 218.2 | 80.0% (4/5) | Ranked Pressure Performer |
| **Dhruv Jurel** | **#20** | 214 | 19 | +27.2 | +20.4 | +16.5 | 180.8 | 63.2% (12/19) | Ranked Pressure Performer |
| **Finn Allen** | **#21** | 60 | 8 | +48.1 | +22.1 | +16.3 | 203.3 | 75.0% (6/8) | Ranked Pressure Performer |
| **Mahipal Lomror** | **#23** | 35 | 4 | +68.3 | +22.5 | +16.2 | 205.7 | 75.0% (3/4) | Ranked Pressure Performer |
| **Akeal Hosein** | **#37** | 139 | 20 | +25.7 | +17.1 | +12.6 | 145.3 | 55.0% (11/20) | Ranked Pressure Performer |
| **Jason Roy** | **#40** | 67 | 4 | +35.9 | +17.6 | +12.1 | 173.1 | 75.0% (3/4) | Ranked Pressure Performer |
| **Asif Khan** | **#56** | 68 | 4 | +28.7 | +14.4 | +8.8 | 183.8 | 50.0% (2/4) | Ranked Pressure Performer |
| **Shamar Joseph** | **#57** | 28 | 6 | +52.0 | +15.2 | +8.6 | 153.6 | 50.0% (3/6) | Ranked Pressure Performer |
| **Jake McGurk** | **Unranked** | 18 | 1 | +180.4 | +35.5 | +28.7 | 361.1 | 100.0% (1/1) | Limited Evidence (<25 HP balls) |
| **Josh Inglis** | **Unranked** | 40 | 6 | -16.2 | -4.3 | -10.5 | 115.0 | 16.7% (1/6) | Below Baseline Contribution |
| **Ben Duckett** | **Unranked** | 30 | 3 | -33.6 | -8.0 | -14.5 | 93.3 | 0.0% (0/3) | Below Baseline Contribution |

---

### 6. Production Verification Status

| Module / Verification Check | Scope / Target File | Status | Notes |
|---|---|:---:|---|
| **Wide-Ball RAE Attribution** | `backend/analytics/pressure_performers/contribution.py` | **PASS** | Wides contribute 0 expected runs, 0 balls, and 0 RAE to batters. |
| **Match Aggregation Defense** | `backend/analytics/pressure_performers/match_aggregation.py` | **PASS** | Aggregated `hp_rae` strictly equals sum of eligible delivery contributions. |
| **Bowler Wide Run Inclusion** | `backend/analytics/pressure_bowlers/contribution.py` | **PASS** | Bowler conceded runs strictly include wides and no-balls. |
| **Legal Bye / Leg-Bye RAE** | `backend/analytics/pressure_performers/contribution.py` | **PASS** | Legal balls with byes retain valid negative RAE ($0 - \text{expected\_runs}$). |
| **Independent Regression Tests** | `backend/tests/test_batting_wide_rae_attribution.py` | **PASS** | 5 of 5 targeted regression tests passed. |
| **Full Backend Test Suite** | `python -m pytest backend/tests/ -q` | **PASS** | **106 of 106 tests passed** in 11.93s. |
| **Frontend Production Build** | `npm --prefix frontend run build` | **PASS** | 10 of 10 routes compiled with 0 errors. |
| **Live UI Availability** | `http://127.0.0.1:3000/discovery?tab=pressure` | **PASS** | Unified leaderboard fully operational with clean live data. |
