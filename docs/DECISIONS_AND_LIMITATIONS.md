# SupeRR Intelligence — Architectural Decisions & Known Limitations

**Document Type:** Architecture Decision Records (ADRs) & Data Boundaries  
**Product:** SupeRR Intelligence  
**Author:** Antigravity Engineering  
**Version:** 1.0.0

---

## 1. Architectural Decisions

### ADR 001: Separation of Analytical OLAP (DuckDB) and Application State (SQLite)
- **Context:** The dataset contains ~200k delivery records and requires sub-second aggregations across slices of phase, pressure, and matchup. Meanwhile, user watchlists, scenario setups, and scouting notes require transactional consistency.
- **Decision:** Use columnar Parquet files queried via embedded DuckDB for analytics. Use SQLite for user watchlists, saved scenarios, and qualitative notes.
- **Consequence:** High performance, zero server overhead, local-first privacy, no database license costs.

### ADR 002: Tabular ML (CatBoost CPU) vs. Deep Learning / LLMs
- **Context:** Spec Rule 4 & 5 forbids paid APIs (OpenAI, Gemini, paid sports APIs) and training an LLM. Tabular sports data with mixed categorical/numerical features performs best on gradient boosted trees.
- **Decision:** Utilize CatBoost on CPU. Use deterministic rule-based template engines for qualitative recruitment summaries.
- **Consequence:** 100% reproducible, explainable, zero runtime cost, operates without internet access.

### ADR 003: Strict Pre-Delivery Information Sets
- **Context:** Any calculation of expected runs or win probability must avoid lookahead bias.
- **Decision:** Features for delivery $t$ are derived exclusively from the state *prior* to ball $t$.
- **Consequence:** Out-of-sample validity and non-inflated evaluation metrics.

---

## 2. Dataset Limitations & Explicit Boundaries

1. **Missing Player Metadata:**
   - The supplied dataset does not include player birth dates/ages, international citizenship/overseas eligibility for IPL, current injury status, or retention contracts.
   - **Handling:** These fields are marked `unknown` in analytical summaries and exposed as user-editable fields in the Auction and Squad modules. No nationality is ever guessed from names.

2. **Absence of Auction Pricing:**
   - The dataset contains purely historical on-field match data from 2022 to 2026. It contains zero auction bids or financial transactions.
   - **Handling:** Player price valuations in Squad Architect and Auction Simulator are treated as user assumptions or historical benchmarks, never as authoritative "machine predictions" of future auction bids.

3. **Bowl Speed Unreliability:**
   - `bowl_speed` contains 77,861 zeros, negative values, and anomalous values (>180 km/h, max 1456 km/h).
   - **Handling:** `bowl_speed` is excluded from all predictive models and marked as an uncertified diagnostic field.

4. **Competition Scope:**
   - 853 matches belong to IPL (2022–2026) and T20Is.
   - 30 matches belong to Emerging Teams Asia Cup and Rising Stars. These are excluded by default from standard leaderboards to avoid skewing elite player metrics with developmental tournament noise.
