# SupeRR Intelligence — Cricket Scouting & Auction Decision Platform

---

## 1. Overview

**SupeRR Intelligence** is an evidence-first, locally runnable, professional cricket analytics workstation. It moves past superficial averages and strike rates by evaluating players in context: quantifying situational pressure, calculating Runs Above Expected (RAE), applying Empirical Bayes reliability shrinkage, detecting statistically under-recognized talent, optimizing squads using Google OR-Tools CP-SAT, and running Monte Carlo auction simulations.

The platform operates **100% locally with free and open-source software (FOSS)** without any paid APIs, internet dependencies, or external cloud costs.

---

## 2. Key Modules

1. **Intelligence Overview:** Dataset metrics, validated model cards, top pressure batters/bowlers, and highlighted undervalued talents.
2. **Player Discovery:** Multi-parameter progressive filtering across roles, styles, formats, and pressure impact percentiles.
3. **Player Intelligence Profile:** Comprehensive dossiers featuring career performance, high-pressure breakdowns, match phase splits, failure signatures, and recruitment intelligence verdicts.
4. **Player Comparison Lab:** Multi-candidate head-to-head evaluation (2–4 players), comparative radar charts, and "Winner by Scenario" arbitration.
5. **Squad Architect & What-if Engine:** Google OR-Tools CP-SAT optimization across 3 strategies (Balanced, High Upside, Risk Controlled), role minimums, overseas limits, and dynamic what-if re-solving.
6. **Auction Decision Simulator:** Monte Carlo valuation simulation (1,000 runs) using triangular market price distributions, bid cap curves, and fallback replacement decision trees.
7. **Scouting Watchlists & Dossier Records:** Custom shortlists, priority tags, and private qualitative notes persisted in SQLite.
8. **Methodology & Validation Centre:** Formal mathematical formulations, certified scoring semantics mappings, and out-of-sample model evaluation cards.

---

## 3. Technology Stack

- **Analytics Engine:** Python 3.13, Pandas, NumPy, SciPy, Statsmodels.
- **Tabular ML:** CatBoost CPU Regressors & Classifiers, scikit-learn.
- **Optimization:** Google OR-Tools CP-SAT (Integer constraint programming).
- **Data & Storage:** Columnar Parquet, DuckDB (vectorized analytical store), SQLite (user store).
- **Backend API:** FastAPI, Uvicorn, Pydantic v2.
- **Frontend Dashboard:** Next.js 14 App Router, React 18, TypeScript, Tailwind CSS, Lucide React, Plotly.js.
- **Design Principles:** Hallmark & Impeccable human-crafted aesthetic standards (design tokens, zero decorative AI slop, accessible data density).

---

## 4. Mathematical Methodology & Formulation

- **Second-Innings Situational Pressure $P(t)$:**
  $$P(t) = \frac{10}{1 + \left(\frac{10}{P(1)} - 1\right) \cdot \exp\left(-10 \cdot k \cdot \sum_{s=1}^{t-1} \Delta C(s) \cdot \Delta R(s)\right)}$$
  *Adapted from Mallawa Arachchi, Manage & Scariano (2024), Journal of Sports Analytics.*
- **Context-Adjusted Impact:**
  $$\text{RAE}(t) = \text{Actual Runs}(t) - \mathbb{E}[\text{Runs}(t) \mid \mathbf{x}_t]$$
  Evaluated with CatBoost on CPU strictly using pre-delivery features without player identity.
- **Empirical Bayes Reliability:**
  $$\hat{\theta}_i = B_i \mu_0 + (1 - B_i) \bar{y}_i, \quad B_i = \frac{\sigma_i^2 / n_i}{\tau^2 + \sigma_i^2 / n_i}$$
  Shrinks low-sample player performance safely to role cohort priors.
- **Discovery Gap:**
  $$\Delta_{\text{disc}} = \text{Percentile}(\text{Adjusted Impact}) - \text{Percentile}(\text{Conventional Avg} \times \text{SR})$$
