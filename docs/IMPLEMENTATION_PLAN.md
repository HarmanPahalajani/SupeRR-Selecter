# SupeRR Intelligence — Technical Implementation Plan (Revised v2.0)

**Document Type:** Formal Technical Architecture, Mathematical Foundations & Milestone Specification  
**Product:** SupeRR Intelligence (Cricket Scouting, Auction Analytics & Squad Decision Platform)  
**Status:** Approved Architecture with Mandatory Methodological & Dataset Corrections  
**Author:** Antigravity Engineering  
**Version:** 2.0.0

---

## 1. System Architecture & Operating Principles

SupeRR Intelligence operates as a fully decoupled, evidence-first, local-first analytics workstation:

```
[ Supplied Dataset: 200,999 Deliveries, 883 Matches (2022–2026) ]
                               │
                               ▼
  [ Milestone 1: Rigorous Ingestion, Audit & Separation ]
     ├── 1-based Overid (1–20): Powerplay (1–6), Middle (7–15), Death (16–20)
     ├── Chronological Legal-Ball Progression (Wides & Oversteps excluded from legal count)
     ├── Super Over Isolation (Innings > 2 segregated from regulation innings)
     ├── Revised Overs & Revised Targets (DLS/Weather handling)
     ├── Non-Silent Audit Trail: Anomaly flagging table (no silent drops)
     └── Certified Canonical Parquet Datasets
                               │
                               ▼
  [ Milestone 2: Match-State Reconstruction & Pressure Engine ]
     ├── Chronological Pre-delivery State (Score, Wickets, Remaining Legal Balls, RRR)
     ├── Disclosed Empirical Resource Proxy R(t) in [0, 1]
     ├── Second-Innings Chase Pressure P(t) (Mallawa Arachchi et al. 2024 calibrated on Train)
     ├── First-Innings Acceleration & Defensive Risk Formulations
     ├── Situational vs. Psychological Pressure demarcation
     └── Sensitivity Analysis over Parameter k & Cutoff Quantiles
                               │
                               ▼
  [ Milestone 3: Machine Learning & Neutral Baselines (No Leakage) ]
     ├── Strict Pre-Delivery Context (No player IDs in neutral expected baselines)
     ├── Pre-match Only Historical Features (strictly shifted prior to match date)
     ├── Out-of-Sample Predictions for Residuals (RAE, Runs Saved, WAE)
     ├── Benchmark vs Statistical Baselines (Cohort Mean & GLM)
     ├── Rolling-Origin & Match-Grouped Temporal Validation (Train: 2022-2024, Val: 2025, Test: 2026)
     └── Calibrated Win Probability & Wicket Probability (Brier Scores & Reliability Curves)
                               │
                               ▼
  [ Milestone 4: Player Impact, Reliability & Scouting Signals ]
     ├── Pressure-Weighted Impact per Opportunity
     ├── Role- & Format-Specific Normal-Normal & Beta-Binomial Empirical Bayes Shrinkage
     ├── Match-Level Bootstrap Uncertainty Intervals (95% Credible Bounds)
     ├── Opportunity-Gated Failure Signatures (Min sample rules; no spec on tiny samples)
     ├── Evidence-Conditional Cross-Format Portability (IPL vs T20I)
     └── Statistical Under-Recognition Detector ("Discovery Gap" vs Conventional Avg*SR)
                               │
                               ▼
  [ Milestone 5: Local Analytical Store & REST Backend ]
     ├── Vectorized DuckDB Engine over Scored Parquet
     ├── Transactional SQLite Store for Watchlists, Notes, and Editable Player Attributes
     ├── FastAPI v1 REST API with Strict Pydantic Contracts
     └── Transparent Provenance & Confidence Disclosures
                               │
                               ▼
  [ Milestone 6: Optimization Engines (OR-Tools CP-SAT & Monte Carlo) ]
     ├── User-Attributed Auction Pool (Explicitly labeled assumptions, never fake predictions)
     ├── Google OR-Tools CP-SAT Solver with scaled integer arithmetic
     ├── Distinct 3-Strategy Generation (Balanced, Upside, Risk-Controlled)
     ├── True What-if Dynamic Re-optimization & Replacement Trees
     └── Monte Carlo Price Uncertainty Simulation (Triangular Distributions & Bid Curves)
                               │
                               ▼
  [ Milestone 7: Hallmark / Impeccable Frontend Design System ]
     ├── 8 Dedicated Full-Product Modules (Overview, Discovery, Profile, Comparison, Squad Architect, Auction Simulator, Watchlist, Methodology)
     ├── Strict Hallmark Design Tokens (:root, deep navy/charcoal, controlled pink accent)
     ├── High information density, zero decorative AI slop, accessible tables & Plotly charts
     └── Real Data Wiring across 100% of routes and interactive controls
```

---

## 2. Dataset Corrections & Strict Ingestion Rules

1. **Over Indexing & Phase Boundaries:**
   - Inspection confirms `overid` in `ball_by_ball.csv` is 1-based, taking values from 1 to 20.
   - Phases are strictly bounded as:
     - **Powerplay:** `overid` $\in [1, 6]$
     - **Middle:** `overid` $\in [7, 15]$
     - **Death:** `overid` $\in [16, 20]$
2. **Legal Deliveries:**
   - Neither `innings_ball_num` nor `over_ball_num` represent legal-ball counts (both increment on wides and no-balls).
   - Legal balls are derived strictly via `extras_type not in ['wide', 'Overstep']`.
   - Legal progression within an over is tracked independently to enforce standard 6-legal-ball overs.
3. **Super Overs & Incomplete Matches:**
   - Regulation innings are strictly `innings in [1, 2]`.
   - Deliveries where `innings > 2` are classified as Super Overs and segregated into an isolated special-situation store.
   - Matches with revised overs (`first_inn_revised_overs`, `second_inn_revised_overs`) or revised targets (`revised_target`) dynamically override standard 20-over/first-innings totals.
4. **Non-Silent Audit Trail:**
   - Anomaly rows (such as the 36 `extras_2_runs > 0` rows, dismissal flag inconsistencies, or speed outliers) are never dropped silently; they are logged into `artifacts/reports/scoring_anomalies_audit.json` with documented treatment.

---

## 3. ML Model Design & Leakage Prevention

For all predictive models:

### Model A: Expected Batter Runs per Delivery $\mathbb{E}[Y_{\text{bat}} \mid \mathbf{x}_t]$
- **Target:** Verified batter runs $Y_{\text{bat}} \in \{0, 1, 2, 3, 4, 5, 6\}$.
- **Features $\mathbf{x}_t$:** Legal balls remaining, wickets lost, required run rate, match phase (powerplay/middle/death), striker batting position, striker hand (LHB/RHB), bowler style, pace/spin, striker pre-match historical strike rate and rolling form (strictly pre-match shifted).
- **Leakage Prevention:** Neutral expected-performance baselines strictly **exclude player IDs** (striker_id, bowler_id). It models what an average role-comparable player is expected to produce in that situation.
- **Out-of-Sample Predictions:** Out-of-fold/out-of-sample predictions are generated prior to residual calculation ($\text{RAE} = Y - \hat{Y}$).
- **Benchmarking:** CatBoost is evaluated against:
  1. Naive Phase/Over Cohort Mean
  2. Regularized GLM / Ridge Regression baseline.
  CatBoost is adopted only where it demonstrates superior out-of-sample validation RMSE/MAE.

### Model B: Expected Bowler Runs Conceded $\mathbb{E}[Y_{\text{bowl}} \mid \mathbf{x}_t]$
- **Target:** Runs charged to bowler ($Y_{\text{bat}} + \text{wides} + \text{no-balls}$).
- **Benchmarking:** Compared against phase/style cohort baseline.

### Model C: Bowler-Credited Wicket Probability $\mathbb{P}(W_{\text{bowl}} = 1 \mid \mathbf{x}_t)$
- **Target:** Binary indicator of credited dismissal (`Caught`, `Bowled`, `LBW`, `Stump`, `Hit Wicket`).
- **Benchmarking:** Evaluated via Brier Score and Log Loss against historical phase base rates. Probability outputs are calibrated using Isotonic/Sigmoid calibration.

### Model D: Chase Win Probability
- **Target:** Chase victory indicator (1/0). Evaluated via Brier score and reliability curves.

---

## 4. Pressure Methodology & Calibration

1. **Second-Innings Situational Pressure (Mallawa Arachchi et al. 2024):**
   $$P(t) = \frac{10}{1 + \left(\frac{10}{P(1)} - 1\right) \cdot \exp\left(-10 \cdot k \cdot \sum_{s=1}^{t-1} \Delta C(s) \cdot \Delta R(s)\right)}$$
   - Parameter $k$ is calibrated on the training seasons (2022–2024) to optimize outcome separation.
   - Resource proxy $R(t)$ is explicitly disclosed as:
     $$R(t) = 0.45 \cdot \left(\frac{\text{Balls Bowled}}{\text{Max Legal Balls}}\right) + 0.55 \cdot \left(\frac{\text{Wickets Lost}}{10}\right)$$
2. **First-Innings Acceleration & Defensive Risk:**
   - Separate formulation based on par trajectory, resource exhaustion, and projected finish vs. venue par score.
3. **Situational vs. Psychological Distinction:**
   - Explicitly clarified in UI and methodology: $P(t)$ measures *situational match demand*, not biometric or psychological state.
4. **Sensitivity Testing:**
   - Player pressure rankings are tested across 70th, 75th, 80th, and 85th percentile cutoffs, reporting rank stability coefficients.

---

## 5. Player Evaluation, Reliability & Bayesian Shrinkage

1. **Context-Adjusted Impact:**
   - Runs Above Expected ($\text{RAE}$) and Runs Saved Above Expected weighted continuously by situational pressure.
2. **Empirical Bayes Shrinkage:**
   - Normal-Normal prior within role cohorts (Top Order, Middle Order, Finisher, Powerplay Bowler, Death Bowler) shrinks noisy small-sample impacts toward cohort mean $\mu_0$.
3. **Match-Level Bootstrap Uncertainty:**
   - 500 match-level bootstrap resamples per qualified player to produce 95% confidence bounds.
4. **Failure Signatures:**
   - Sample-gated diagnostic checks (minimum 15 balls faced in phase/matchup). Where sample is small, labeled "Insufficient Sample".
5. **Format Portability:**
   - Portability scores between IPL and T20I are computed only when a player has at least 5 matches in each format; otherwise labeled "Single-Format Evidence".
6. **Undervalued Talent Detector:**
   - Disclosed strictly as **Statistical Under-Recognition**, measuring the gap between contextual pressure impact percentile and conventional Avg $\times$ SR percentile.

---

## 6. Squad Architect & Auction Intelligence

1. **Data Transparency:**
   - Acknowledged that dataset contains historical on-field data only.
   - Player auction pool contains user-editable, source-attributed price assumptions (low, mid, high), availability flags, and overseas eligibility.
2. **CP-SAT Optimization:**
   - Google OR-Tools integer programming with integer-scaled purse values (in Lakhs) to ensure arithmetic precision.
   - Three distinct strategies:
     - **Balanced:** Median price, posterior impact, role constraints.
     - **High Upside:** Ceiling impact (mean + 1.2 uncertainty), mid price.
     - **Risk Controlled:** Conservative posterior (mean - 0.8 uncertainty), conservative high price.
3. **Dynamic What-If Engine:**
   - Real re-optimization on excluded/locked players, returning replacement options and utility deltas.
4. **Monte Carlo Auction Simulation:**
   - Triangular price distribution sampling, bid cap curves, and "if target is lost" replacement trees.

---

## 7. Deliverables & Verification Milestones

- **Milestone 1:** Data Ingestion, Semantic Audit, Non-silent Anomaly Tracking, Canonical Parquet.
- **Milestone 2:** Chronological Pre-delivery State Reconstruction & Pressure Engine.
- **Milestone 3:** Tabular ML & Baseline Models with Rolling-Origin & Temporal Evaluation.
- **Milestone 4:** Player Impact, Empirical Bayes Shrinkage, Bootstrap Intervals & Scouting Signals.
- **Milestone 5:** Vectorized DuckDB & SQLite Layer + FastAPI Endpoints.
- **Milestone 6:** OR-Tools CP-SAT Squad Optimizer, What-if Engine & Auction Simulator.
- **Milestone 7:** Complete Next.js Frontend with 8 Functional Modules (Hallmark / Impeccable Design).
- **Milestone 8:** Comprehensive Testing, Validation Reports & Documentation.
