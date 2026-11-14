# SupeRR Intelligence — Complete Product & Implementation Specification

**Document type:** Product requirements, analytics methodology, technical architecture and build instructions for Antigravity  
**Product status:** Full-product specification (not a Round 1-only implementation plan)  
**Primary data source:** The supplied Rajasthan Royals SupeRR Selector data pack  
**Operating principle:** Evidence-first, locally runnable, free/open-source software, no paid APIs  
**Audience:** Antigravity coding agent and the project owner

---

## 0. Instructions to Antigravity — Read This First

Build **SupeRR Intelligence**, a complete cricket scouting, player analytics, squad construction and auction decision-support platform. This specification is the source of truth.

Do not interpret this as a request to build only a static dashboard, a generic cricket statistics website, or a Round 1 submission microsite. Build the complete functional product described below.

### Non-negotiable implementation rules

1. **Do not fabricate data.** Never invent player statistics, names, ages, nationality, prices, availability, injury status, role labels, model scores or recommendations.
2. **Do not silently guess data semantics.** The `runs`, `extras1_runs`, `extras_2_runs` and `extras_type` fields must pass the scoring-semantics audit described below before derived team runs or bowler-conceded runs are used.
3. **Do not put analytics in the browser.** All authoritative calculations, model predictions, rankings, squad scores and scenario results must come from the Python backend. The frontend only requests, displays and explains backend results.
4. **Do not use paid APIs.** No OpenAI API, Gemini API, Anthropic API, paid sports API, paid database, paid chart service or mandatory cloud service. The product must work locally without API keys.
5. **Do not train an LLM.** Use specialised tabular ML models and transparent statistical methods. Natural-language scouting explanations should initially be generated from verified metrics using deterministic templates.
6. **Do not use a neural network just to claim that the project uses AI.** Use the models specified in this document and retain a model only when validation supports it.
7. **Do not use a random row split for cricket delivery data.** Use date-ordered, match-grouped validation to prevent leakage between deliveries from the same match.
8. **Do not mix IPL and T20I without normalisation.** Always preserve competition/format splits and disclose them.
9. **Do not hardcode current IPL auction rules.** Put squad limits and eligibility constraints in editable, versioned configuration. Verify rules before using them in a live auction scenario.
10. **Do not assume missing player information.** Age, nationality/overseas status, current auction availability, retained status, injury status and price are not reliably provided by the dataset. Add explicit user-managed fields and mark unknown values as unknown.
11. **Do not expose proprietary competition data.** Keep raw data out of public GitHub repositories, public static assets, public demo APIs and browser bundles. Default to local-only operation.
12. **Every visible control must work.** No decorative buttons, dead filters, nonfunctional tabs, fake loading states or hardcoded sample chart values in production mode.
13. **Every recommendation must be traceable.** Show the metric, sample size, competition/season scope, uncertainty and evidence behind every recruitment verdict.
14. **Do not stop after generating a plan.** First inspect the repository and create the implementation plan and contracts; then implement, run tests, fix errors and verify each module in the browser.
15. **Do not ask for confirmation on routine engineering choices.** Use the stack and defaults in this specification. Pause only when a genuinely unresolved data-semantic or external-rule issue could produce false results; document the blocker and build the independent parts meanwhile.

### Required first actions

Before editing application code:

1. Inspect the complete repository and identify existing working code. Preserve useful work; do not overwrite blindly.
2. Inspect the supplied data-pack files and validate the counts in Section 2.
3. Create these project documents:
   - `docs/IMPLEMENTATION_PLAN.md`
   - `docs/DATA_DICTIONARY.md`
   - `docs/ANALYTICS_METHODOLOGY.md`
   - `docs/MODEL_CARD.md`
   - `docs/API_CONTRACT.md`
   - `docs/DECISIONS_AND_LIMITATIONS.md`
4. Create the monorepo structure in Section 4.
5. Implement one vertical slice end-to-end before building every screen: data import → player metrics API → Player Intelligence page → browser test.
6. Continue module by module until the acceptance criteria in Section 13 pass.

---

# 1. Product Definition

## 1.1 Product name

**SupeRR Intelligence**  
*Cricket Scouting, Auction Analytics & Squad Decision Platform*

This is an independent hackathon/product prototype and must not imply that it is an official Rajasthan Royals system unless the organisers explicitly authorise that claim or the use of official marks.

## 1.2 Product objective

Create a professional cricket analytics platform that helps a franchise analyst or scout:

- Discover players matching a specific cricketing role and a set of measurable requirements.
- Understand player performance beyond conventional averages and strike rates.
- Identify batters and bowlers who deliver reliably in high-pressure situations.
- Compare multiple players under the same conditions.
- Detect overlooked or undervalued statistical profiles.
- Inspect a player's weaknesses, volatility, sample size and uncertainty.
- Construct a balanced squad within a budget and configurable eligibility rules.
- Run what-if scenarios when a player is excluded, unavailable or too expensive.
- Simulate auction scenarios using explicit price assumptions rather than invented prices.
- Save scouting watchlists, notes and recruitment priorities.
- Inspect the methodology, data provenance, model validation and limitations.

## 1.3 Product philosophy

The product must be **evidence-first, explainable and decision-oriented**.

A high score alone is not a recruitment recommendation. The system must answer:

1. What did the player do?
2. In what match situation did the player do it?
3. What would an average/role-comparable player be expected to do in the same situation?
4. How far above or below that expectation was the player?
5. Has the player repeated the contribution across matches and tournaments?
6. How much evidence supports the conclusion?
7. Which role could the player fill?
8. What weaknesses or translation risks remain?
9. How would adding the player change the squad?

## 1.4 Complete product modules — locked structure

The application must contain these eight modules:

1. Intelligence Overview
2. Player Discovery
3. Player Intelligence
4. Player Comparison Lab
5. Squad Architect
6. Auction Decision Simulator
7. Scouting Watchlist
8. Methodology & Validation Centre

The following capabilities are integrated into those modules:

- What-if Squad Analysis — inside Squad Architect.
- Undervalued Talent Detector — inside Intelligence Overview and Player Discovery.
- Confidence & Evidence Centre — inside Player Intelligence and Methodology & Validation.
- Winner by Scenario — inside Player Comparison Lab.
- Failure Signature and Pressure Portability — inside Player Intelligence.

Do not create separate navigation items for every small feature. Keep the information architecture compact and clear.

---

# 2. Supplied Dataset — Facts, Scope and Known Limitations

## 2.1 Files supplied

The ZIP contains:

| File | Purpose |
|---|---|
| `ball_by_ball.csv` | Delivery-level batting, bowling, run, wicket, style and shot information |
| `matches.csv` | Match identifiers, date, competition, teams, venue country, innings overs, revised target and result |
| `competitions.csv` | Competition name, format and season |
| `teams.csv` | Competition/team mapping |
| `playing_eleven.csv` | Match/team/player participation, batting order and some player flags |
| `competition_team_player_mapping.csv` | Competition/team/player identifiers and names |
| `Round 1 Problem Statement ...pdf` | Official challenge description and required first-round deliverables |

## 2.2 Verified archive counts

The archive was inspected. Current observed counts are:

| Dataset | Rows / count |
|---|---:|
| `ball_by_ball.csv` | 200,999 delivery records |
| `matches.csv` | 883 match records |
| `competitions.csv` | 141 competition records |
| `teams.csv` | 353 competition/team records |
| `playing_eleven.csv` | 28,381 records |
| `competition_team_player_mapping.csv` | 6,413 records |
| Unique player IDs across the full delivery file | 959 |

The full match data covers 22 January 2022 through 1 November 2026.

## 2.3 Default primary analytics scope

The official brief specifies historical **IPL and T20 International (T20I)** data. Therefore, the default primary analysis scope must be:

- All 482 T20I match records.
- All 371 IPL match records across IPL 2022, 2023, 2024, 2025 and 2026.
- 853 primary-scope match records in total.
- 194,014 primary-scope delivery records.
- 87,687 IPL delivery records.
- 106,327 T20I delivery records.
- 837 primary-scope matches have delivery records; 16 have no delivery records.
- 824 unique strikers, 596 unique bowlers and 892 unique player IDs across all participant roles occur in the primary-scope delivery records.

There are two additional T20 competitions in the supplied pack — Men's T20 Emerging Teams Asia Cup 2024 and Asia Cup Rising Stars 2025 — with 30 match records in total. They must be **excluded from the default IPL/T20I leaderboards**. The data-import configuration may support an optional expanded T20 scope, but the UI must clearly label it and must never mix it into the primary result silently.

## 2.4 Important data-quality observations

The following have been observed and must be rechecked automatically by the import pipeline:

- 200,999 delivery rows contain no exact duplicate rows in the inspected file.
- The natural delivery key `(match_id, innings, innings_ball_num)` is unique in the inspected file.
- All player IDs appearing in striker, non-striker and bowler fields have a corresponding player ID in the competition-player mapping at least once.
- `playing_eleven.csv` contains 40 repeated `(match_id, team_id, player_id)` keys with conflicting batting-order values. Do not blindly trust a single row from this table for batting position.
- 10,881 records have `is_wicket = true`.
- One wicket-flagged row has a missing `dismissed_player_id`.
- Twelve rows have a non-null `dismissed_player_id` while `is_wicket = false`.
- Dismissal labels include Caught, Bowled, LBW, RunOut, Stump, Hit Wicket, Retire Out and obstruction-related labels. A wicket flag does not mean the bowler receives credit.
- `bowl_speed` has 77,861 zero values, one negative value and 19 values above 180; the maximum observed value is 1,456.1. Treat this field as unreliable until individually validated. Do not use it in the default predictive model.
- 36 records have non-zero `extras_2_runs`. Inspect all such rows, not only a sample, because their combinations with `extras_type`, `extras1_runs` and `runs` are not self-explanatory.
- The `runs` field has a maximum of six, and the `is_four`/`is_six` flags are internally consistent with the recorded `runs` in the inspected data. This suggests `runs` may represent batter runs, but that interpretation is **not yet certified**.
- `extras_type`, `extras1_runs` and `extras_2_runs` contain combinations requiring manual reconciliation against source scorecards before total team runs and bowler-conceded runs are computed.
- Primary-scope records include some matches with only one recorded innings and some Super Over records. These must be handled separately from standard completed two-innings matches.

## 2.5 Mandatory scoring-semantics audit

Before calculating total team runs, bowler economy, legal balls or run-equivalent impacts, create `analytics/validation/scoring_semantics.py` and an audit report.

The audit must:

1. Inspect every unique combination of `runs`, `extras_type`, `extras1_runs`, `extras_2_runs`, `is_wicket` and dismissal type.
2. Determine whether `runs` is batter runs or total delivery runs.
3. Determine what `extras1_runs` and `extras_2_runs` represent.
4. Determine which `extras_type` values mean wide, no-ball/overstep, bye, leg-bye, penalty or other.
5. Identify whether `Overstep` represents a no-ball and how its additional run and batter runs are recorded.
6. Define bowler-conceded runs correctly: batter runs plus bowler-chargeable extras; byes and leg-byes are not charged to the bowler; penalty handling must follow verified data semantics.
7. Define legal deliveries correctly. Wides and no-balls normally do not count as legal balls, but validate the source representation before deriving the legal-ball count.
8. Reconcile at least 20 representative innings against reliable scorecards, including wide, no-ball/overstep, bye, leg-bye, run-out, bowler-credited wicket and Super Over examples.
9. Store the mapping in a versioned configuration file, e.g. `config/scoring_semantics.yml`.
10. Emit a machine-readable pass/fail report and keep unresolved rows flagged.

**Do not guess.** If public scorecard reconciliation is unavailable for a specific edge case, keep the affected calculation disabled or label it provisional.

## 2.6 Match inclusion policy

Create a configurable, auditable inclusion policy:

- Default competition filter: T20I plus competition names beginning with `IPL` where `match_format == T20`.
- Exclude Super Overs from standard-innings model training and standard pressure rankings. Keep Super Over events in a separate special-situation view.
- Exclude abandoned, incomplete and no-result innings from models requiring a completed innings or known match winner.
- Keep valid delivery-level performance from a match only where its match and innings data passes the relevant calculation requirements.
- Use `revised_target`, `first_inn_revised_overs` and `second_inn_revised_overs` where applicable. Do not assume every chase is a 20-over chase or that the first-innings total is always the final target.
- Treat ties, Super Overs, DLS/revised targets and incomplete scorecards as separate cases. Do not convert missing results into wins or losses.
- Preserve all excluded-row counts in the audit report.

## 2.7 Missing player attributes

The supplied files do not reliably provide:

- Age as of a selected date.
- Nationality or IPL overseas eligibility.
- Current 2027 auction availability.
- Retention status.
- Injury/fitness status.
- Auction base price, sold price or expected 2027 bid.
- A canonical franchise role such as finisher, powerplay bowler or death bowler.

Create an editable `player_attributes` table for these external/manual attributes. Fields should include source, source date, confidence/status and editor. Unknown must remain `NULL`/`unknown`; never infer nationality from a player's name or infer auction availability from historical participation.

---

# 3. Technical Decisions — Use This Stack

All mandatory components must be free to install and run locally. Prefer permissive open-source licences. Pin compatible dependency versions in lockfiles and record licences in `THIRD_PARTY_NOTICES.md`.

## 3.1 Frontend — Antigravity builds this

| Component | Required choice | Purpose |
|---|---|---|
| Framework | Next.js App Router | Application pages and routing |
| UI | React + TypeScript | Component architecture and type safety |
| Styling | Tailwind CSS | Responsive design system |
| Component primitives | shadcn/ui + Radix-based components | Accessible controls and consistent components |
| Charts | Plotly.js + `react-plotly.js` | Interactive statistical charts |
| Tables | TanStack Table or accessible native tables | Large filterable player tables |
| Forms/validation | React Hook Form + Zod | Scenario inputs and validation |
| API state | TanStack Query | Fetching, caching, loading and error states |
| Icons | Lucide React | Consistent iconography |

Do not use paid dashboard templates, paid chart packages, paid UI kits or external font APIs that are required at runtime. Bundle locally available fonts or use system font stacks.

## 3.2 Backend

| Component | Required choice | Purpose |
|---|---|---|
| Language | Python | Analytics and API |
| API framework | FastAPI | REST endpoints and OpenAPI schema |
| Validation | Pydantic | Request and response contracts |
| Analytical query engine | DuckDB | Fast local analytical queries over Parquet |
| Data format | Parquet via PyArrow | Efficient processed data storage |
| App metadata database | SQLite | Watchlists, notes, saved scenarios and local user profile |
| Server | Uvicorn | Run FastAPI locally |

DuckDB/Parquet is the analytical store. SQLite is for mutable application records. Do not put all delivery rows into a relational ORM just for the sake of using an ORM.

## 3.3 Analytics and machine learning

| Component | Required choice | Purpose |
|---|---|---|
| Data processing | Pandas + NumPy | Cleaning and feature engineering |
| Tabular ML | CatBoost CPU | Contextual run-expectation and classification models |
| Baselines/statistics | SciPy + Statsmodels | Regression baselines, distributions and statistical estimates |
| Model evaluation | scikit-learn | Grouped/time-based validation, calibration, metrics |
| Bayesian reliability | Empirical Bayes implementation using SciPy/NumPy; PyMC only if justified | Shrink noisy small-sample player estimates |
| Explainability | CatBoost feature importance + permutation importance; SHAP only if practical | Explain model behaviour |
| Squad optimisation | Google OR-Tools CP-SAT | Constraint-based squad selection |
| Simulation | NumPy/SciPy | Reproducible price and availability scenarios |

### Primary model choice

Use **CatBoost on CPU** as the first-choice tabular ML algorithm. It supports numeric and categorical features without requiring fragile manual one-hot encoding and is licensed under Apache 2.0. It is suitable for this moderate-sized structured cricket dataset. This is the recommended starting model, not a guarantee that it beats simpler baselines. Compare it against a role/context cohort mean and a regularised GLM. Keep CatBoost only if it improves out-of-sample evaluation and calibration.

Do not add XGBoost, LightGBM, TensorFlow, PyTorch or a transformer unless a measured experiment proves that the addition materially improves the model. No GPU is required.

### No mandatory LLM

Do not integrate any paid or external LLM API. Generate scouting explanation text from verified metric objects using templates and rule-based summaries. The product must operate without internet after installation. If a local LLM is added later, it must be optional, disabled by default and must not calculate or fabricate statistics.

## 3.4 Free operation and deployment model

**Default deployment: local-first application.**

- Frontend runs locally through Node.js.
- Backend runs locally through Python/Uvicorn.
- Processed Parquet and DuckDB files remain on the local machine.
- SQLite stores local notes and scenarios.
- The model artifacts are loaded from local files.
- No API keys or hosted database are required.
- Runtime analytics must not need internet access.

Provide scripts for Windows PowerShell and, where practical, macOS/Linux. The application can later be hosted, but cloud free tiers are not a guaranteed permanent free service. Do not claim that a cloud deployment is free forever. Do not upload the proprietary data pack to a public hosting provider.

---

# 4. Repository and Runtime Architecture

Use a single repository with separated frontend, backend and shared documentation.

```text
superr-intelligence/
├── README.md
├── THIRD_PARTY_NOTICES.md
├── .gitignore
├── .env.example
├── config/
│   ├── dataset.yml
│   ├── scoring_semantics.yml
│   ├── pressure.yml
│   ├── model.yml
│   ├── ranking.yml
│   └── squad_rules.default.yml
├── data/
│   ├── raw/                  # gitignored; original supplied files only
│   ├── interim/              # gitignored
│   ├── processed/            # gitignored
│   ├── app/                  # local DuckDB/SQLite files; gitignored
│   └── exports/              # local exports; gitignored
├── artifacts/
│   ├── models/               # local model files; may be reproducibly regenerated
│   ├── metrics/
│   └── reports/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── security/
│   ├── analytics/
│   │   ├── ingestion/
│   │   ├── validation/
│   │   ├── state/             # match-state reconstruction
│   │   ├── features/
│   │   ├── pressure/
│   │   ├── batting/
│   │   ├── bowling/
│   │   ├── impact/
│   │   ├── reliability/
│   │   ├── discovery/
│   │   ├── validation_models/
│   │   └── ranking/
│   ├── optimisation/
│   │   ├── squad/
│   │   ├── what_if/
│   │   └── auction/
│   ├── scripts/
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.lock
├── frontend/
│   ├── app/
│   │   ├── (workspace)/
│   │   │   ├── overview/
│   │   │   ├── discovery/
│   │   │   ├── players/[playerId]/
│   │   │   ├── comparison/
│   │   │   ├── squad-architect/
│   │   │   ├── auction-simulator/
│   │   │   ├── watchlist/
│   │   │   └── methodology/
│   ├── components/
│   │   ├── shell/
│   │   ├── charts/
│   │   ├── tables/
│   │   ├── player/
│   │   ├── comparison/
│   │   ├── squad/
│   │   ├── auction/
│   │   └── ui/
│   ├── hooks/
│   ├── lib/
│   ├── services/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── package-lock.json
└── docs/
    ├── IMPLEMENTATION_PLAN.md
    ├── DATA_DICTIONARY.md
    ├── ANALYTICS_METHODOLOGY.md
    ├── MODEL_CARD.md
    ├── API_CONTRACT.md
    └── DECISIONS_AND_LIMITATIONS.md
```

### Data flow

```text
Raw CSV files
    ↓
Ingestion + schema validation
    ↓
Scoring-semantics audit + inclusion policy
    ↓
Clean, canonical Parquet datasets
    ↓
Match-state reconstruction
    ↓
Feature engineering
    ↓
Pressure + expected-performance models
    ↓
Player impact + reliability estimates
    ↓
Player metrics / rankings / evidence records
    ↓
DuckDB analytical store + local model artifacts
    ↓
FastAPI services
    ↓
Next.js dashboard
```

### Runtime responsibilities

- `analytics/` owns every statistical definition and model calculation.
- `optimisation/` owns squad and auction scenario logic.
- `repositories/` owns database access.
- `services/` assembles validated data into API response objects.
- `frontend/` displays results and collects user inputs; it must not implement duplicate ranking formulas.

---

# 5. Data Engineering Requirements

## 5.1 Canonical identifiers

Use numeric `player_id`, `match_id`, `comp_id` and `team_id` as primary identifiers. Names are display attributes, never join keys.

Create canonical tables:

- `dim_player`
- `dim_team`
- `dim_competition`
- `dim_match`
- `dim_player_competition`
- `fact_delivery`
- `fact_player_match_batting`
- `fact_player_match_bowling`
- `fact_player_pressure_event`
- `fact_player_metrics`
- `fact_model_evaluation`

Preserve source values in raw columns and store derived/cleaned fields separately. Do not destroy provenance.

## 5.2 Match state before each delivery

For every delivery, reconstruct the state immediately **before** the delivery. At minimum:

- Match, competition and season IDs.
- Innings number and innings type.
- Batting team and bowling team.
- Current score before delivery.
- Wickets lost before delivery.
- Legal balls bowled before delivery.
- Legal balls remaining under the applicable innings limit.
- Runs required and revised target, where applicable.
- Required run rate, where applicable.
- Current run rate.
- Current striker and non-striker.
- Batter runs and balls faced before delivery.
- Batting order/position.
- Bowler and bowling style.
- Pace/spin category.
- Match phase (powerplay, middle, death), derived from actual legal-ball limits.
- Target/innings limit source (standard or revised).
- Current match result availability.

Sort deliveries by a verified chronological key. Do not assume `innings_ball_num` counts legal deliveries until validated. Derive legal-ball progression from confirmed wide/no-ball semantics.

All features used for a delivery prediction must be known before that delivery. Never use runs, dismissal, post-ball score, next batter, final total or match result as an input feature for a pre-delivery prediction.

## 5.3 Role inference

The dataset does not contain a definitive franchise role table. Create **observed role profiles** with confidence labels:

- Top-order batter: distribution of batting positions, e.g. typical position 1–3.
- Middle-order batter: typical position 4–6.
- Lower-order/finisher: typical position 6–8, with phase-specific evidence.
- Bowling role: powerplay, middle-over and death-over usage based on actual overs bowled.
- Pace/spin role: based on reliable bowling-style and `pace_or_spin` fields.
- All-rounder profile: meaningful batting and bowling participation under explicit minimum-opportunity thresholds.
- Wicketkeeper: use `is_wk` where reliable and reconcile across matches; show unknown otherwise.

Do not hardcode all players into exactly one role. Players can have multiple role capabilities. Display role inference confidence and supporting matches/innings.

## 5.4 Data build commands

Implement deterministic commands such as:

```bash
python -m analytics.ingestion.run
python -m analytics.validation.run_all
python -m analytics.state.build_states
python -m analytics.features.build_all
python -m analytics.train.run_all
python -m analytics.ranking.build
python -m analytics.export.build_dashboard_tables
```

A full pipeline should be reproducible with one documented command, e.g. `python -m analytics.pipeline.run_all --config config/dataset.yml`.

---

# 6. Analytics Methodology — Required Models and Definitions

This section is the source of truth for the numerical system. Treat weights and thresholds as configuration values, version them, and test sensitivity. Do not invent scores solely to make a player rank higher.

## 6.1 Use separate concepts, not one opaque score

Keep these concepts distinct:

- **Pressure intensity:** how demanding the match situation is.
- **Match leverage:** how much the next event could alter the probability of winning.
- **Player impact:** how much better/worse the player performed than context expected.
- **Reliability:** how repeatable that contribution appears across matches.
- **Confidence:** how much evidence supports the estimate.
- **Role suitability:** whether the observed skills fit a selected cricketing role.

The UI must not label match leverage as pressure or call raw strike rate a pressure score.

## 6.2 Pressure contexts

Build separate pressure contexts for:

1. Second-innings/chase batting.
2. Second-innings/bowling while defending.
3. First-innings batting (supplementary innings-acceleration pressure).
4. First-innings bowling (supplementary par-score defence pressure).

Do not pool these contexts without normalisation and validation. The strongest, most directly interpretable pressure framework is second-innings pressure because target, required rate, wickets and balls remaining are observable.

### A. Chase pressure

Use the 2024 Mallawa Arachchi, Manage & Scariano pressure-index paper as a baseline. The paper models pressure as a bounded/logistic process related to required run rate and resource depletion, with pressure calculated immediately before a delivery. Re-estimate parameters using the supplied IPL/T20I data; do not copy the older paper's historical target ceiling or parameter values blindly.

Inputs:

- Required run rate before the delivery.
- Initial required run rate.
- Balls/resources consumed and remaining.
- Wickets lost and wickets in hand.
- Match-specific target/revised target.
- Remaining legal balls.
- Format and innings length.

A practical implementation should use the paper's published logistic form as the first candidate. In the paper's notation, the bounded index is:

`P(t) = 10 / [1 + (10 / P(1) - 1) * exp(-10 * k * SUM_s(ΔC(s) * ΔR(s)))]`

where:

- `P(t)` is pressure immediately before delivery `t`, on a 0–10 scale.
- `C(t)` is the required run rate immediately before delivery `t`.
- `R(t)` is the proportion of resources consumed before delivery `t` (between 0 and 1).
- `k` is a fitted sensitivity parameter.
- `P(1)` is the initial pressure derived from the initial required rate relative to a feasible maximum initial required rate.
- `ΔC(s)` and `ΔR(s)` are the changes between adjacent pre-delivery states.

Implementation rules:

1. Calculate the exact required run rate using the true revised target and remaining legal balls.
2. Prefer a legitimate DLS resource table only if it can be used lawfully and the table is available in the project. Otherwise derive and label an empirical resource proxy from the supplied data; do not call the proxy an official DLS resource value.
3. Do not carry over the 2024 paper's historical maximum-target assumption. Estimate a feasible initial required-rate reference from the training period only, document it, and freeze it for validation/test.
4. Fit `k` using training matches only. Use a validation period to select it; do not tune it on the final test season.
5. Compare this pressure index with simpler baselines (required-rate percentile, resource-adjusted required-rate ratio) and test whether it helps explain held-out outcomes.
6. Test monotonicity and saturation using realistic state examples. Extreme, almost-impossible chases should not cause unlimited linear pressure growth.
7. Show the formula, parameter values, resource definition and limits on the Methodology page.

The pressure index is not the same as a player's ability. It only weights the context in which the player's contribution occurred.

### B. Bowling pressure while defending

Build a separate opponent-state/defensive-pressure view. Use the match state from the bowling team's perspective: runs to defend, balls remaining, wickets available to the chasing side, required rate and the calibrated win probability.

Keep **defensive pressure** and **match leverage** as separate fields. A useful match-leverage measure is highest when the win probability is close to 0.5 and lower when the result is nearly certain. A useful defensive-pressure measure should reflect the defending side's risk and the difficulty of preventing the target. Validate its direction with worked examples and held-out match outcomes.

Do not simply copy batting pressure and relabel it for bowlers.

### C. First-innings pressure

Because there is no target to chase in the first innings, use a distinct supplementary measure:

- A season/format/competition-specific expected par trajectory at each stage.
- Projected final total conditional on score, balls and wickets available.
- Difference between projected final total and the relevant par benchmark.
- Remaining resources and innings phase.

This produces an **innings-acceleration pressure** metric. Clearly label it as different from chase pressure. It may be shown in player profiles, but it must not be merged into the primary pressure rating until sensitivity and predictive tests show that the two contexts are comparable.

### D. Pressure categories

Use continuous scores in the model. For readable UI categories, expose configurable quantile cutoffs such as low/moderate/high/very high. The default high-pressure cut should be selected from validation and sensitivity analysis, not chosen to make a preferred player look good.

Run rankings at multiple thresholds (for example 70th, 75th, 80th and 85th percentile). Show rank stability when the threshold changes.

## 6.3 Machine-learning model selection

Use CPU CatBoost as the primary challenger model. Always compare against a simple statistical baseline. Store model artifacts and evaluation outputs.

### Model A — Expected batter runs per delivery

- Algorithm: `CatBoostRegressor`.
- Target: verified batter runs on the delivery (0–6), only after `runs` semantics have been audited.
- Objective: start with RMSE; compare MAE/Huber where appropriate.
- Features: format, season bucket, innings, over/phase, legal balls remaining, wickets lost, current score/rate, batter's position, batter handedness, bowler style, pace/spin, striker pre-delivery balls/runs and other valid pre-delivery context.
- Exclude `striker_id`, `bowler_id`, `dismissed_player_id`, final match result, post-delivery runs and future information from the neutral baseline. The baseline should estimate an appropriate average outcome, not memorise the player's name.
- Compare to a cohort-mean model and a regularised count/linear model.

### Model B — Expected bowler-conceded runs per delivery

- Algorithm: `CatBoostRegressor`.
- Target: correctly derived runs charged to the bowler per delivery.
- Do not train until extras and legal-delivery semantics have passed the audit.
- Inputs: pre-delivery match state, phase, batter hand, bowling style, pace/spin, format, wickets, balls remaining, required rate (for chases), and valid contextual variables.
- Exclude bowler identity from the neutral expected-performance baseline; player-specific effect is calculated from residuals after the model prediction.

### Model C — Bowler-credited wicket probability

- Algorithm: `CatBoostClassifier`.
- Target: binary indicator for a dismissal credited to the bowler, based on a documented dismissal-type map.
- Do not count run-outs, retired-out or obstruction dismissals as bowler-credited wickets unless the source definition explicitly says otherwise.
- Calibrate probabilities using scikit-learn calibration methods only where the validation data supports calibration.
- Report Brier score, log loss, calibration curve and class prevalence. Accuracy alone is not sufficient for an imbalanced event.

### Model D — Chase win probability

- Algorithm: begin with logistic regression as an interpretable baseline; compare with `CatBoostClassifier`.
- Target: whether the chasing team ultimately wins.
- Training observations: pre-delivery state snapshots from completed standard second innings only.
- Weight observations so that a long match does not dominate solely because it contains more delivery rows; use match-balanced sample weighting or a pre-declared state-sampling strategy.
- Exclude ties, no-results, unresolved outcomes and Super Overs from the binary training target.
- Inputs: state known before delivery only, including target, score, wickets, legal balls remaining, required rate, format and other valid contextual features.
- Evaluate with Brier score, log loss, calibration plots and match-grouped temporal holdout. Do not report accuracy as the sole metric.

### Model selection rule

Keep the simplest model that is well calibrated and improves held-out performance over the baseline. If CatBoost does not improve the baseline, use the baseline. This is not a failure; it is a valid model-selection result.

## 6.4 Validation protocol — no leakage

The dataset spans 2022–2026. Use time-ordered splits and group by `match_id`:

- Training: earliest seasons/years (initial suggestion: 2022–2024).
- Validation: next season/year (initial suggestion: 2025).
- Final temporal test: 2026.

Because competition sizes differ, also report separate IPL and T20I metrics. If a year/season split leaves too few examples, document a revised split before training.

Use `GroupKFold` only for supplemental grouped diagnostics, not as a replacement for final temporal evaluation. No match may appear in both train and test in the same fold.

All model feature creation must be performed using information available at prediction time. Rolling player form features, if added, must be shifted so they only use earlier matches.

## 6.5 Context-adjusted impact

For each delivery:

`Runs Above Expected (RAE) = observed runs - expected runs from the neutral context model`

Keep batter runs, total team runs and bowler-conceded runs as separate variables.

For a batter, calculate the residual using the verified batter-run target. A dismissal cost can be added only after a validated wicket-value estimate exists. Attribute the dismissal to `dismissed_player_id`, not automatically to the striker on the delivery.

For a bowler:

- `Runs Saved Above Expected = expected bowler-conceded runs - actual bowler-conceded runs`.
- `Wickets Above Expected = credited wicket event - expected credited wicket probability`.
- Preserve run prevention and wicket creation as separate components until a defensible run-equivalent wicket-value model is implemented and validated.

### Optional advanced wicket value

A later advanced version may estimate the marginal value of a wicket from an innings-state value function. A backward dynamic-programming/Bellman-expectation calculation can estimate expected remaining runs at states with different wickets in hand. Use it only if the state transition, incoming-batter quality assumption and wicket credit attribution are explicit and validation is credible. Otherwise keep the run and wicket components separate rather than inventing a fixed “20 runs per wicket” multiplier.

## 6.6 Pressure-weighted player contribution

For each player and match:

1. Calculate delivery-level context-adjusted impact.
2. Apply the continuous pressure weight from the relevant pressure context.
3. Aggregate delivery impacts within the match.
4. Normalise by meaningful opportunity exposure (e.g. balls faced or legal balls bowled) and role cohort.
5. Preserve total impact and rate metrics separately.

Do not let a player accumulate a high rating solely from a very small number of high-pressure balls. Require minimum exposure policies and shrink low-sample estimates toward a role/format prior.

## 6.7 Reliability and empirical Bayes shrinkage

Reliability is not raw average impact and not simply low variance.

For each player, compute at minimum:

- Pressure opportunities.
- Matches with pressure opportunities.
- Mean match-level pressure impact.
- Median match-level impact.
- Match-to-match standard deviation.
- Positive-impact match frequency.
- Total pressure contribution.
- Opportunity-normalised contribution.
- IPL/T20I split.
- Tournament portability.
- Confidence interval.

For continuous player impact, use a Normal-Normal empirical Bayes shrinkage model within suitable role/format cohorts:

- Estimate cohort prior mean `mu0` and between-player variance `tau2` from training data.
- Estimate each player's mean `ybar`, within-player variance and effective match count.
- Estimate posterior mean and posterior uncertainty.
- Shrink small-sample player estimates more strongly toward the cohort mean.

For positive-contribution frequency, use a Beta-Binomial prior/posterior. Report posterior mean and credible interval.

Use match-level bootstrap resampling (not delivery-level bootstrap) to preserve within-match dependence. Use a fixed random seed and report the number of bootstrap repetitions.

## 6.8 Final rating and rankings

Do not define an arbitrary composite with undocumented weights.

Build separate transparent components:

- Pressure-adjusted batting impact.
- Pressure-adjusted bowling run prevention.
- Pressure-adjusted wicket creation.
- Repeatability/reliability.
- Confidence/evidence strength.
- Format-specific performance.

For a single ordered shortlist, standardise the relevant validated impact components within role and competition format, and define the aggregation rule in `config/ranking.yml`. The default should weight **estimated impact** more heavily than consistency, while using confidence/shrinkage to prevent small samples from dominating. Do not use a player's conventional rank as a direct input to the pressure ranking.

Before finalising the composite:

1. Run sensitivity analysis over plausible weight settings.
2. Check whether the top 10 changes materially.
3. Report stable and unstable ranks.
4. Show separate IPL and T20I ratings alongside any combined rating.
5. If one player has only one format represented, display that fact and do not pretend they have cross-format portability evidence.
6. Do not label a player “reliable” with a tiny sample. Use labels such as “high estimated impact — low evidence” where appropriate.

## 6.9 Undervalued Talent Detector

This means **statistically under-recognised by conventional metrics**, not a verified financial bargain. The supplied data has no auction prices.

Candidate signal:

- Strong context-adjusted pressure impact.
- Conventional average/strike-rate rank materially weaker than adjusted rank.
- Adequate opportunity and match count.
- Positive held-out / cross-tournament validation where possible.
- Stable result under pressure-threshold and scoring-weight sensitivity tests.

Display a “Discovery Gap” with a clear direction. Use percentiles and confidence bands, not a misleading rank subtraction with inconsistent direction.

## 6.10 Failure Signature

Create role-specific diagnostic patterns from verified data:

**Batters:**
- Dismissal frequency by phase.
- Runs/impact versus pace and spin.
- Dot-ball rate by phase and pressure category.
- Boundary frequency by phase.
- Entry situation (wickets lost and score when batter arrives).
- Chase vs first-innings split.
- Left/right-handed matchup only if data volume supports it.

**Bowlers:**
- Runs conceded by phase.
- Boundary conceded rate.
- Dot-ball rate.
- Credited wicket rate.
- Pressure vs non-pressure split.
- Performance against left/right-handed batters.
- Pace/spin and style splits.

Every weakness label needs a minimum sample rule and uncertainty. Never infer a weakness from three balls.

## 6.11 Pressure Portability

Measure whether a player's pressure-adjusted performance is stable across:

- IPL vs T20I.
- Seasons.
- Competitions/series.
- Match phases.
- Batting positions or bowling phases.

Do not compare raw runs or raw economy across formats. Use standardised cohort-adjusted impact. Show “insufficient evidence” where a player has too few matches in a segment.

---

# 7. Squad Architect, What-if Analysis and Auction Simulator

## 7.1 Required principle

Do not optimise the squad by selecting the ten or twenty highest individual player scores. A balanced cricket squad needs role coverage, skill complementarity, replacement depth, eligibility constraints and uncertainty awareness.

## 7.2 Player pool requirements

The supplied dataset only provides historical performance. Create a user-editable player master/auction pool with:

- `player_id` (linked to analytics player if known)
- Display name
- Age (optional, manually sourced)
- Nationality / overseas eligibility (unknown until supplied)
- Available for this scenario (yes/no/unknown)
- Auction eligibility (yes/no/unknown)
- Primary role and secondary roles (manual/analyst-approved)
- Batting handedness
- Bowling style
- Skill tags: top order, middle order, finisher, powerplay, middle overs, death overs, spin, pace, wicketkeeper, all-rounder
- Estimated price low / midpoint / high
- Price source and source date
- Price confidence (low/medium/high)
- Notes

A player with unknown overseas status must not be counted as an Indian player by default. Require user resolution before enforcing an overseas cap.

## 7.3 Squad Architect workflow

### Step 1 — Create scenario

Inputs:

- Scenario name.
- Total purse / remaining purse.
- Existing or retained players.
- Existing spend.
- Number of players to acquire.
- Maximum squad size.
- Maximum overseas slots and current overseas count.
- Role requirements (minimum/target/maximum).
- Risk preference: balanced, upside-seeking, risk-controlled, custom.
- Optional playing XI structure.

All league rules must come from editable scenario configuration, not hardcoded constants.

### Step 2 — Define role requirements

Examples:

- Top-order batter.
- Middle-order batter.
- Finisher.
- Wicketkeeper-batter.
- Pace bowler.
- Spin bowler.
- Powerplay specialist.
- Death-overs specialist.
- Batting all-rounder.
- Bowling all-rounder.

A player may satisfy more than one skill tag, but the optimiser must avoid double-counting the same player slot incorrectly.

### Step 3 — Optimise

Use Google OR-Tools CP-SAT with binary selection variables. Scale numeric objective values to integers for CP-SAT.

A conceptual objective:

`Maximise: expected_player_value + role_coverage_bonus + complementarity_bonus - risk_penalty - unmet_requirement_penalty`

Subject to:

- Total estimated cost <= remaining purse.
- Required acquisition count.
- Squad size limit.
- Overseas-player limit.
- Minimum role coverage.
- Maximum role counts where specified.
- Player eligibility and availability.
- No duplicate player selection.
- Existing squad constraints.

The utility must include uncertainty. A risk-controlled strategy should penalise uncertain estimates more strongly; an upside-seeking strategy may use an optimistic estimate but must show the downside risk.

Do not use invented player prices. If price is missing, the squad solver must either ask the user to enter a price assumption or exclude that player from budget-feasible optimisation while allowing a non-budgeted scouting shortlist.

### Step 4 — Generate strategy alternatives

Return up to three clearly different solutions:

1. **Balanced:** value + role fit + controlled risk.
2. **High upside:** greater weight on ceiling/potential, with explicit volatility warning.
3. **Risk controlled:** conservative posterior estimates and stronger uncertainty penalty.

Do not merely return the same squad three times with different labels. Include a solution diversity constraint or a transparent reason for identical results.

### Step 5 — Explain the squad

For every result, show:

- Selected players and roles.
- Estimated cost and source.
- Remaining budget.
- Role coverage.
- Indian/overseas count where known.
- Pressure reliability contribution.
- Complementary skills.
- Biggest remaining vulnerabilities.
- Uncertainty and assumptions.
- Why each player is selected over the nearest alternative.

## 7.4 What-if Analysis

The What-if tool must perform a real re-optimisation.

User actions:

- Remove/exclude one player.
- Mark a player unavailable.
- Change the estimated price.
- Change the purse.
- Change role requirements.
- Change risk appetite.
- Lock a selected player.
- Increase/decrease overseas slots.

The backend must rerun the optimiser and return:

- Best replacement(s).
- Updated squad.
- Change in projected utility.
- Change in role coverage.
- Budget released/consumed.
- Remaining purse.
- Overseas dependency change.
- Risk/uncertainty change.
- Any new vulnerabilities.

Provide two explicit replacement modes:

1. **Pre-purchase substitution:** replace a candidate before the bid; no fictitious refund is assumed.
2. **Hypothetical roster removal:** user may choose whether the modeled player cost is released; clearly label this as a what-if assumption, not an actual auction mechanic.

## 7.5 Auction Decision Simulator

The supplied dataset has no auction prices or competitor bidding records. Therefore:

- Never claim the model predicts an actual 2027 hammer price.
- Allow manual low/mid/high price estimates or imported historical auction data from a user-provided lawful source.
- Record source, date and confidence for each price.
- Simulate price uncertainty using user-defined distributions, e.g. triangular(low, most_likely, high).
- Allow user-specified competitor demand/price inflation scenarios.
- Simulate a configurable number of runs with a fixed seed.
- Show probability of winning at a bid cap, expected spend, chance of exceeding budget and replacement if the player becomes unaffordable.
- Show the assumptions behind each simulated result.

Auction tools:

- Maximum bid calculator based on remaining budget and role needs.
- Target price sensitivity.
- “If target is lost” replacement tree.
- Bid cap vs squad utility curve.
- Reserve budget planner.
- Scenario comparison.

All prices must be clearly marked as **user assumptions**, **historical reference**, or **unknown**.

---

# 8. Detailed Dashboard / UX Requirements

## 8.1 Design direction

Create a premium, professional sports analytics interface. Use a refined navy/charcoal base with controlled Rajasthan-inspired pink accents, soft neutral surfaces, restrained blue/teal data colours and clear status colours.

Do not copy the official Rajasthan Royals website or use an official logo without permission. Do not use overdone gradients, neon glows, excessive glassmorphism or giant decorative hero sections. This is an analyst workstation, not a marketing landing page.

Design priorities:

- Desktop-first analytics workspace, responsive for tablet and mobile.
- Persistent left navigation on desktop; compact collapsible navigation on smaller screens.
- Clear filters and breadcrumbs.
- High information density without tiny unreadable text.
- Strong table sorting, search and saved filter states.
- Reusable metric cards, player cards, chart containers and evidence panels.
- Accessible colour contrast and keyboard navigation.
- Tooltips describing non-obvious metrics.
- Show units, sample size, date scope and format on every metric.
- Every chart has an explanatory title and a clear legend.
- Avoid chart junk and decorative visualisations that do not answer a scouting question.

## 8.2 Global application shell

Header:

- Product wordmark: SupeRR Intelligence.
- Current data scope / selected season filters.
- Data version and model version.
- Local/system status.
- User menu / local profile.

Sidebar:

1. Overview
2. Player Discovery
3. Player Intelligence (opened through player profile)
4. Comparison Lab
5. Squad Architect
6. Auction Simulator
7. Watchlist
8. Methodology & Validation

Global filters should not silently change saved scenarios. Always show when a filter is active.

## 8.3 Module 1 — Intelligence Overview

Purpose: a decision-ready summary of player and squad intelligence.

Required widgets:

- Dataset coverage: competitions, seasons, matches and delivery rows.
- Model status: version, last training date, test metrics and status.
- Top pressure-reliable batters.
- Top pressure-reliable bowlers.
- Highest-confidence hidden opportunities.
- Players with high impact but low evidence.
- Biggest pressure performers by format/season.
- Recent model/data warnings.
- Quick links: discover player, compare players, build squad.

Visuals:

- Batter/bowler leaderboard with rank movement and confidence.
- Pressure impact distribution.
- IPL vs T20I performance split.
- Reliability vs impact scatter plot.
- Role cohort heatmap.

Do not show invented “live” data. This dataset is historical and its latest match date is 1 November 2026; label the data coverage accordingly.

## 8.4 Module 2 — Player Discovery

Create advanced filters with progressive disclosure.

### Basic filters

- Batter / bowler / all-rounder / wicketkeeper profile.
- IPL / T20I / both.
- Season and competition.
- Batting hand.
- Pace/spin and bowling style.
- Observed batting role / bowling phase role.

### Performance filters

- Minimum matches/innings/balls.
- Pressure impact.
- Pressure opportunities.
- Positive-impact frequency.
- Reliability estimate.
- Confidence level.
- Match phase performance.
- Format portability.
- Failure-signature metrics.

### Advanced scouting filters

- Strong pressure performer.
- Strong death-overs role.
- Powerplay specialist.
- Performs against pace/spin.
- High impact / high uncertainty.
- High impact / stable evidence.
- Undervalued statistical profile.

Do not expose filters for age, nationality, overseas status or price unless those fields have been populated in the editable player master.

Each result must show:

- Player name.
- Observed role tags.
- Main rating.
- Pressure impact.
- Reliability estimate.
- Pressure sample count.
- Confidence label.
- Main strength and main risk.

Allow sorting by every relevant column. Allow multi-select comparison. Explain the match logic in the UI.

## 8.5 Module 3 — Player Intelligence Profile

Each player page must include these six sections:

### A. Performance overview

- Matches and competitions.
- Batting innings / not-outs if derivable.
- Runs, batting average and strike rate (only after scoring semantics verified).
- Balls faced.
- Boundaries.
- Wickets (bowling-credited only where appropriate).
- Runs conceded, economy and legal balls (only after extras audit).
- Role profile and role inference confidence.

### B. Pressure analysis

- Pressure opportunities.
- High-pressure runs / runs prevented.
- Pressure-adjusted impact.
- Pressure success frequency.
- Pressure vs normal performance.
- Batting/bowling pressure split.
- Pressure by match phase.
- Pressure across seasons and formats.

### C. Consistency & reliability

- Match-wise contribution timeline.
- Rolling average with minimum-match rules.
- Match-to-match volatility.
- Positive contribution frequency.
- Empirical Bayes/posterior estimate.
- Confidence/credible interval.
- Sample size warning.

### D. Match-situation analysis

- Powerplay / middle / death.
- First innings vs chase.
- Strong vs weak opposition only if an objective and documented strength proxy exists.
- Batting position.
- Pace vs spin.
- Left/right-handed matchup where support exists.
- Tournament and season split.

Do not call a team “strong” or “weak” based only on fame or reputation. Define any opposition-strength proxy (e.g. opponent Elo/rolling win strength) and calculate it without future leakage.

### E. Failure Signature

Show the player's repeatable failure patterns with sample counts and uncertainty. Separate observed weakness from unsupported speculation.

### F. Recruitment Intelligence

Create a structured evidence card:

- **Recruitment fit:** role/role gap this player may fill.
- **Why consider:** two to four evidence-backed points.
- **Best use case:** specific batting position/phase or bowling phase where data supports it.
- **What can go wrong:** top limitations.
- **Evidence strength:** match count, pressure sample and confidence interval.
- **Format translation:** IPL/T20I split and portability evidence.
- **Recommendation label:** Shortlist / Further scouting / Watchlist / Insufficient evidence.

Do not create an unqualified “Buy this player” statement. State that this is statistical scouting support, not a guarantee of future performance.

## 8.6 Module 4 — Player Comparison Lab

- Compare up to four players.
- Default to same-role comparison; allow cross-role comparison only with an explicit warning.
- Compare under the same format, season, match phase and pressure filters where possible.
- Use a metric table and charts, not only a radar chart.
- Show sample size and confidence interval next to every key score.

Required outputs:

- Overall context-adjusted impact.
- Pressure impact.
- Reliability/posterior estimate.
- Pressure sample count.
- Positive-impact frequency.
- Phase performance.
- Pace/spin matchup.
- Failure signature.
- Format portability.

### Winner by Scenario

Display a winner for each defined scenario, e.g.:

- Best estimated high-pressure impact.
- Most reliable with adequate sample.
- Best death-overs contribution.
- Best against spin.
- Best evidence confidence.
- Best role fit.

A winner must be shown only when the difference is supported by data and uncertainty. Otherwise display **No clear statistical winner**.

## 8.7 Module 5 — Squad Architect

Use the workflow and optimisation logic in Section 7. The UI must include:

- Scenario setup wizard.
- Existing/retained squad editor.
- Player pool and eligibility editor.
- Role requirement builder.
- Purse and price assumptions.
- Risk-preference selector.
- Generate squad action.
- Three strategy tabs.
- Role coverage visualisation.
- Budget waterfall / budget remaining.
- Player utility breakdown.
- Missing role / vulnerability warnings.
- Export scenario report.

Every result must show solver status: optimal, feasible, infeasible or time limit reached. Never label a feasible incumbent as globally optimal if the solver has not proven optimality.

## 8.8 Module 6 — Auction Decision Simulator

Create:

- Auction scenario setup.
- Price assumption editor/importer.
- Bid cap calculator.
- Budget reserve planner.
- Scenario simulation controls.
- Results distribution.
- Probability of losing a target at different bid limits.
- Replacement tree.
- “If we lose this player” scenario.
- Budget stress test.

Show the number of simulations and random seed. Clearly distinguish model prediction from analyst-entered assumptions.

## 8.9 Module 7 — Scouting Watchlist

Allow the user to:

- Add/remove players.
- Create custom watchlists.
- Add private scouting notes.
- Tag role priority.
- Set priority (High/Medium/Low).
- Save a comparison.
- Attach an analyst verdict.
- Export CSV/PDF/Markdown shortlist.

Persist this data in SQLite. Notes must not be overwritten when analytics are refreshed.

## 8.10 Module 8 — Methodology & Validation Centre

This is a core product module, not a footnote.

Show:

- Dataset coverage and last import.
- Data-quality report and unresolved warnings.
- Scoring-semantics mapping.
- Pressure definitions and formulas.
- Model cards for every trained model.
- Training/validation/test date ranges.
- Metrics: MAE/RMSE, Brier score, log loss, calibration summaries.
- Match-grouping and temporal validation rules.
- Feature definitions and units.
- Feature importance / permutation importance.
- Player-level evidence trails.
- Pressure threshold sensitivity analysis.
- Ranking weight sensitivity analysis.
- Known limitations.
- Reproducibility command and model version.

Include downloadable methodology and model-validation reports.

---

# 9. API Contract

Use versioned REST endpoints under `/api/v1`. Define Pydantic schemas and document the OpenAPI output. All numbers must include units and sample metadata where relevant.

## 9.1 Core endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Backend and data readiness |
| GET | `/api/v1/meta/coverage` | Dataset coverage and filters |
| GET | `/api/v1/meta/model-status` | Model versions and validation status |
| GET | `/api/v1/players` | Search/filter players |
| GET | `/api/v1/players/{player_id}` | Player master/display data |
| GET | `/api/v1/players/{player_id}/profile` | Complete profile summary |
| GET | `/api/v1/players/{player_id}/metrics` | Conventional and adjusted metrics |
| GET | `/api/v1/players/{player_id}/pressure` | Pressure profile and match events |
| GET | `/api/v1/players/{player_id}/failure-signature` | Weakness diagnostic metrics |
| GET | `/api/v1/players/{player_id}/portability` | Format/season portability |
| POST | `/api/v1/players/compare` | Compare 2–4 players |
| GET | `/api/v1/discovery/undervalued` | Hidden statistical opportunities |
| GET | `/api/v1/rankings/batters` | Batter ranking with filters |
| GET | `/api/v1/rankings/bowlers` | Bowler ranking with filters |
| POST | `/api/v1/squads/optimise` | Generate squad alternatives |
| POST | `/api/v1/squads/what-if` | Re-optimise changed scenario |
| POST | `/api/v1/auction/simulate` | Run auction scenario simulation |
| GET/POST | `/api/v1/watchlists` | List/create watchlists |
| POST | `/api/v1/watchlists/{id}/players` | Add/remove players |
| POST | `/api/v1/watchlists/{id}/notes` | Save notes |
| GET | `/api/v1/methodology` | Metric and model methodology |
| GET | `/api/v1/validation` | Model validation results |

## 9.2 Example player list response

```json
{
  "items": [
    {
      "player_id": 123,
      "player_name": "Example Player",
      "observed_roles": ["middle_order_batter"],
      "pressure_impact": 0.0,
      "reliability_estimate": 0.0,
      "pressure_matches": 0,
      "confidence_label": "insufficient_evidence",
      "format_scope": ["IPL"],
      "primary_strength": null,
      "primary_risk": null
    }
  ],
  "total": 0,
  "filters_applied": {},
  "data_version": "...",
  "model_version": "..."
}
```

The example uses placeholders only. Never seed example values into production datasets.

## 9.3 Example squad optimisation request

```json
{
  "scenario_name": "Balanced rebuild",
  "budget_remaining": 25000000,
  "players_to_acquire": 5,
  "locked_player_ids": [],
  "excluded_player_ids": [],
  "risk_profile": "balanced",
  "role_requirements": {
    "top_order_batter": {"min": 1, "target": 1, "max": 2},
    "middle_order_batter": {"min": 1, "target": 2, "max": 3},
    "pace_bowler": {"min": 1, "target": 2, "max": 3},
    "spin_bowler": {"min": 1, "target": 1, "max": 2}
  },
  "ruleset_id": "user_configured_rules_v1"
}
```

All prices and counts are scenario inputs, not embedded facts. Validate budget units and display currency explicitly (INR).

## 9.4 API rules

- Return `422` with clear validation messages for invalid inputs.
- Return a clear solver status for infeasible squad configurations.
- Use pagination for large tables.
- Do not return the full ball-by-ball dataset to the browser.
- Use filters and aggregation queries in DuckDB.
- Add a local API rate limit only if required; this is a local app and must not add external dependency.
- Use CORS restricted to the local frontend origin.
- Do not log raw proprietary records or user notes unnecessarily.

---

# 10. Local Persistence, Security and Privacy

## 10.1 Data storage

- Raw files: `data/raw/`, never edited.
- Clean data: Parquet under `data/processed/`.
- Analytical views/indexes: DuckDB under `data/app/`.
- Watchlists, saved scenarios and notes: SQLite under `data/app/`.
- Model files: `artifacts/models/`.
- Reports: `artifacts/reports/`.

## 10.2 Git hygiene

Add to `.gitignore`:

```gitignore
.env
.env.*
!.env.example
/data/raw/
/data/interim/
/data/processed/
/data/app/*.duckdb
/data/app/*.db
/data/exports/
/artifacts/models/
/artifacts/reports/private/
__pycache__/
.venv/
node_modules/
.next/
```

Do not commit the supplied proprietary data pack or derived tables that recreate it.

## 10.3 Local access

Default to localhost. If a LAN-access mode is added, make it explicitly opt-in and explain that the machine owner is responsible for network access. Add a local password/profile if multiple users need separate watchlists or notes. Do not add external authentication providers that require an API or account.

## 10.4 Exports

Exports must be initiated by the user and stored locally. Include a warning if an export contains proprietary player data. No automatic public upload.

---

# 11. Testing and Validation Requirements

Testing is mandatory. A dashboard that renders is not proof that the analytics are correct.

## 11.1 Data tests

- Row counts and schemas match the source files.
- Every delivery references a valid match.
- Every player/team/competition join is explainable.
- Natural delivery key is unique.
- Delivery order and legal-ball logic are valid.
- Innings totals reconcile with selected source scorecards.
- Extras and bowler-conceded runs reconcile.
- Dismissal credit attribution is correct.
- DLS/revised-target handling is tested.
- Super Overs are isolated.
- Abandoned/no-result matches are handled as documented.

## 11.2 Analytics unit tests

- Pressure score is bounded.
- Chase pressure uses only pre-delivery data.
- A comfortable chase should not receive a higher pressure score than a materially harder equivalent state without a defensible reason.
- Pressure curves saturate at extreme states if using the logistic-index model.
- Expected-run residual equals observed minus expected.
- Bowler-run residual direction is correct (positive means runs saved).
- Bowler wickets exclude non-credit dismissals.
- The dismissed batter is charged, not automatically the striker.
- Player aggregation is stable and correctly grouped by match.
- Bayesian shrinkage pulls low-sample estimates toward cohort priors.
- Higher sample volume should generally reduce posterior uncertainty under equivalent variance.
- Unknown player attributes remain unknown.

## 11.3 Model tests

- Baseline and CatBoost comparison.
- Temporal held-out evaluation.
- Grouped match integrity.
- No future feature leakage.
- Brier/log-loss and reliability diagrams for classifiers.
- MAE/RMSE for regression models.
- Calibration across IPL and T20I subgroups.
- Sensitivity analysis for pressure thresholds.
- Ranking stability under bootstrap resampling.
- Model reproducibility with fixed seeds.

## 11.4 Optimisation tests

- Cannot exceed purse.
- Cannot exceed configured squad size.
- Cannot exceed overseas cap when status is known.
- Does not select unavailable/excluded players.
- Does not select the same player twice.
- Respects locked players.
- Returns infeasible when constraints cannot be satisfied.
- What-if action excludes the requested player and re-solves.
- Price uncertainty is respected.
- Identical alternative squads are not mislabelled as distinct strategies.
- Solver status is displayed accurately.

## 11.5 Frontend tests

Use unit/component tests and browser end-to-end tests. Test:

- All navigation routes.
- Player search/filter/sort/pagination.
- Opening a player profile.
- Comparing 2–4 players.
- Winner by Scenario empty/uncertain states.
- Squad scenario submission and validation errors.
- What-if rerun and replacement output.
- Auction scenario controls.
- Watchlist create/add/remove/note persistence.
- Methodology links and downloadable reports.
- Responsive layout and empty states.
- API failure, loading and no-data states.

No primary route may be a blank page or static placeholder at release.

---

# 12. Development Milestones and Definition of Done

Build the complete platform in vertical slices. Do not build every UI screen first and leave it disconnected from the backend.

## Milestone 1 — Foundation and data audit

Deliver:

- Repository structure.
- Environment setup.
- CSV ingestion.
- Data dictionary.
- Scoring-semantics audit.
- Match inclusion report.
- Data-quality report.
- Canonical player and match tables.

**Exit condition:** Data imports reproducibly and every unresolved scoring/data issue is documented.

## Milestone 2 — Match-state and feature pipeline

Deliver:

- Pre-delivery match state.
- Legal-ball logic.
- Revised target/overs handling.
- Pressure-context features.
- Batter/bowler role features.
- Processed Parquet datasets.

**Exit condition:** Unit tests pass and sample match reconstructions reconcile with scorecards.

## Milestone 3 — Model training and validation

Deliver:

- Baseline expected performance model.
- CatBoost challenger model.
- Wicket-credit model.
- Win-probability model.
- Temporal/match-grouped validation.
- Model cards and evaluation outputs.

**Exit condition:** No leakage; metrics are reported; model choices are justified against baselines.

## Milestone 4 — Player impact and reliability

Deliver:

- Pressure scores and pressure categories.
- Context-adjusted batting/bowling impact.
- Reliability/shrinkage estimates.
- Confidence intervals.
- Format splits and portability.
- Failure signatures.
- Undervalued Talent Detector.
- Player rankings and evidence tables.

**Exit condition:** Every score can be traced to event rows and validated formulas.

## Milestone 5 — API and Player Intelligence vertical slice

Deliver:

- FastAPI service.
- Player metrics/profile endpoints.
- Frontend shell.
- Player Intelligence profile.
- Plotly chart components.

**Exit condition:** A real player ID loads fully computed, database-backed analytics in the browser.

## Milestone 6 — Discovery and Comparison Lab

Deliver:

- Dynamic filters.
- Sorting and pagination.
- Saved searches if time allows.
- Multi-player comparison.
- Winner by Scenario with uncertainty-aware tie/no-winner logic.

**Exit condition:** No hardcoded player rankings or fake chart data.

## Milestone 7 — Squad Architect and What-if

Deliver:

- User-managed player attributes/price pool.
- Scenario wizard.
- CP-SAT optimisation.
- Alternative squad generation.
- Role coverage and budget explanation.
- Exclusion/substitution what-if re-optimisation.

**Exit condition:** All squad constraints pass automated tests.

## Milestone 8 — Auction Simulator and Watchlist

Deliver:

- Price assumption import/edit.
- Monte Carlo auction scenarios.
- Replacement trees.
- Local watchlists and notes.
- Export functionality.

**Exit condition:** Simulations are reproducible and assumptions are visible.

## Milestone 9 — Methodology, QA and release

Deliver:

- Methodology Centre.
- Model cards and validation displays.
- Final browser QA.
- Local run scripts.
- README and troubleshooting guide.
- Privacy and proprietary-data safeguards.

**Exit condition:** A new user can install, import data, train models, run the application and reproduce the documented outputs from the README.

## Final Definition of Done

The project is complete only when:

- It runs locally with no paid API keys.
- All eight modules load and function.
- All data-backed metrics originate from the backend.
- Rankings can be reproduced from a clean pipeline run.
- Model validation is temporal and match-grouped.
- Player profile evidence traces to underlying data.
- Squad optimisation respects configured constraints.
- What-if analysis actually re-runs the optimiser.
- Auction prices are identified as assumptions or sourced values.
- The app clearly labels unknown data and model uncertainty.
- Raw proprietary data is not publicly exposed.
- Tests pass and the README describes the exact commands to reproduce everything.

---

# 13. Practical Build and Run Commands

Antigravity must create and verify Windows-friendly commands. Suggested final interface:

```powershell
# 1. Set up Python environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.lock

# 2. Install frontend dependencies
cd frontend
npm ci
cd ..

# 3. Put the supplied CSV files under data/raw/ (user performs this local step)

# 4. Run data audit and preprocessing
python -m backend.analytics.pipeline.run_all --config config/dataset.yml

# 5. Train/validate models
python -m backend.analytics.train.run_all --config config/model.yml

# 6. Build player metrics and dashboard tables
python -m backend.analytics.ranking.build

# 7. Start backend (terminal 1)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 8. Start frontend (terminal 2)
cd frontend
npm run dev
```

Antigravity may adjust package/module paths to fit the final implementation, but the README must provide commands that actually work from a clean checkout. Add a single convenience script such as `run-local.ps1` once the individual commands are verified.

---

# 14. Build Time and Resource Planning

The complete platform is estimated at approximately **120–180 focused developer hours** for a functional prototype, including analytics, frontend, backend, optimisation, testing and documentation. This is a planning range, not a guarantee. Data reconciliation, model iteration and browser integration are the major uncertainty drivers.

Suggested effort allocation:

| Workstream | Approximate focused hours |
|---|---:|
| Data pipeline and validation | 8–12 |
| Pressure and ML models | 18–26 |
| Player impact and reliability | 10–16 |
| Discovery and undervalued detection | 6–10 |
| Comparison Lab | 5–8 |
| Squad Architect | 8–12 |
| What-if analysis | 5–8 |
| Auction simulator | 10–16 |
| Watchlist and evidence | 5–8 |
| Frontend implementation | 20–30 |
| API integration | 8–12 |
| Testing/deployment/documentation | 10–16 |

Run CPU-first. The supplied dataset is around 200,000 delivery rows; it does not require a GPU or a large language model. Use DuckDB/Parquet for query efficiency and CatBoost CPU for model training. Profile memory and runtime before adding infrastructure.

---

# 15. Research Basis and Technical References

Use these as methodological references. Do not copy any paper mechanically; adapt to the supplied dataset, record assumptions and validate out of sample.

## Cricket analytics research

1. **Mallawa Arachchi, Manage & Scariano (2024), “A pressure index for the team batting second in T20I cricket.”** Journal of Sports Analytics. Provides a mathematically motivated, bounded pressure index linked to required run rate and resource depletion, with pressure computed before each delivery. Use as the chase-pressure baseline and re-estimate parameters using the supplied data.  
   https://doi.org/10.3233/JSA-240792  
   https://journals.sagepub.com/doi/full/10.3233/JSA-240792

2. **Bhattacharjee & Lemmer (2016), “Quantifying the pressure on the teams batting or bowling in the second innings of limited overs cricket matches.”** International Journal of Sports Science & Coaching. Covers pressure on both batting and bowling teams during the second innings. Full text may be access-restricted; use the abstract as a directional reference unless a lawful full copy is available.  
   https://doi.org/10.1177/1747954116667106

3. **Davis, Perera & Swartz (2015), “Player evaluation in Twenty20 cricket.”** Journal of Sports Analytics. Motivates expected-run-differential evaluation against role-specific standard players. Use this to justify role-cohort baselines rather than raw cross-role leaderboards.  
   https://doi.org/10.3233/JSA-150002  
   https://journals.sagepub.com/doi/full/10.3233/JSA-150002

4. **Bandyopadhyay (2026), “Runs Above Expected (RAE) and Wicket Effect (WE): A Context-adjusted and Unified Impact Metric for Twenty20 Cricket.”** arXiv preprint, posted August 2026. Proposes delivery-level runs above expected, empirical-Bayes shrinkage and dynamic-programming wicket value in run-equivalent units. This is a recent preprint, not an established standard; use it as an advanced design reference and independently validate any adaptation.  
   https://arxiv.org/abs/2608.18020

## Model/library documentation

5. **CatBoost documentation — categorical features and regression objectives.**  
   https://catboost.ai/docs/en/features/categorical-features  
   https://catboost.ai/docs/en/concepts/loss-functions-regression  
   CatBoost repository licence: Apache 2.0.  
   https://github.com/catboost/catboost/blob/master/LICENSE

6. **scikit-learn — grouped validation and probability calibration.**  
   https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html  
   https://scikit-learn.org/stable/modules/calibration.html

7. **Google OR-Tools — open-source optimisation toolkit, Apache 2.0.**  
   https://developers.google.com/optimization/  
   https://github.com/google/or-tools

8. **DuckDB — analytical database documentation.**  
   https://duckdb.org/docs/

9. **FastAPI — API framework documentation.**  
   https://fastapi.tiangolo.com/

10. **Next.js documentation.**  
    https://nextjs.org/docs

11. **Tailwind CSS documentation.**  
    https://tailwindcss.com/docs

12. **Plotly.js / React Plotly.**  
    https://plotly.com/javascript/  
    https://github.com/plotly/react-plotly.js

13. **shadcn/ui.**  
    https://ui.shadcn.com/docs

---

# 16. Final Instruction to Antigravity

Build SupeRR Intelligence as a complete, maintainable, locally runnable product—not as a collection of mocked screens.

The most important engineering priorities, in order, are:

1. Data correctness and scoring-semantics validation.
2. Valid match-state reconstruction.
3. Pressure and expected-performance modelling without leakage.
4. Player-level impact, reliability and confidence.
5. Explainable player discovery and comparison.
6. Constraint-correct squad optimisation and genuine what-if re-solving.
7. Auction simulation with explicit, user-controlled price assumptions.
8. Polished, responsive dashboard and clear methodology.

The best implementation is not the one with the largest number of AI models or charts. It is the one that makes defensible cricket decisions, explains the evidence, exposes uncertainty, never invents missing information and works without paid services.

**Start by auditing the repository and data pack. Then create the project plan and contracts. After that, build and test the first end-to-end vertical slice before continuing through the milestones.**
