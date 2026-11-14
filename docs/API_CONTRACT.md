# SupeRR Intelligence — API Contract & Specifications

**Document Type:** REST API Specification & OpenAPI Contract Definition  
**Product:** SupeRR Intelligence  
**Author:** Antigravity Engineering  
**Version:** 1.0.0

---

## 1. Global Standards

- Base URL: `/api/v1`
- Content Type: `application/json`
- Error Format: `{"detail": str, "code": str, "timestamp": str}`
- CORS: Local origins allowed (`http://localhost:3000`, `http://127.0.0.1:3000`)
- Currency: Indian Rupees (INR, ₹) in absolute units with human-formatted strings (e.g. `₹12.5 Cr`).

---

## 2. Core Endpoints

### 2.1 Metadata & Health
- `GET /api/v1/health`
  - Returns backend readiness, data ingestion status, database connection status, and model load flags.
- `GET /api/v1/meta/coverage`
  - Returns data scope: matches (853 primary scope), deliveries (194,014), season range (2022–2026), competitions included.
- `GET /api/v1/meta/model-status`
  - Returns loaded model versions, validation timestamps, RMSE, and Brier metrics.

### 2.2 Players & Scouting
- `GET /api/v1/players`
  - Query parameters: `role`, `format`, `min_matches`, `min_pressure_balls`, `sort_by`, `page`, `page_size`, `search`.
  - Returns paginated list of player summary cards with observed roles, pressure impact, reliability estimate, and confidence tiers.
- `GET /api/v1/players/{player_id}/profile`
  - Returns comprehensive profile: career stats, pressure breakdown, match timeline, phase splits, pace/spin splits, failure signatures, and recruitment recommendation.
- `POST /api/v1/players/compare`
  - Request body: `{"player_ids": [int, ...], "scenario": str, "format_filter": str}`
  - Returns side-by-side metric matrix, head-to-head radar dimensions, and uncertainty-aware "Winner by Scenario" verdict.

### 2.3 Discovery & Rankings
- `GET /api/v1/discovery/undervalued`
  - Returns players with highest positive Discovery Gap (high context-adjusted impact vs modest conventional average/SR).
- `GET /api/v1/rankings/batters`
  - Returns ranked list of batters by standardized pressure impact with configurable weights.
- `GET /api/v1/rankings/bowlers`
  - Returns ranked list of bowlers by standardized runs saved and wickets created.

### 2.4 Squad Architect & What-if
- `POST /api/v1/squads/optimise`
  - Request body: budget, squad size, overseas limits, mandatory/excluded players, role targets, risk appetite (`balanced`, `upside`, `risk_controlled`).
  - Returns three distinct squad strategies with cost breakdowns, role coverage matrices, and vulnerability reports.
- `POST /api/v1/squads/what-if`
  - Request body: modified scenario with player excluded, unavailable, or price changed.
  - Returns re-optimized squad, best replacements, utility delta, and released/consumed purse.

### 2.5 Auction Simulator
- `POST /api/v1/auction/simulate`
  - Request body: target players, user-defined price distributions (min, mode, max), budget cap, number of simulation runs.
  - Returns win probability distributions, budget exhaustion probabilities, and replacement priority trees.

### 2.6 Watchlist
- `GET /api/v1/watchlists` & `POST /api/v1/watchlists`
- `POST /api/v1/watchlists/{id}/players`
- `POST /api/v1/watchlists/{id}/notes`
  - Local SQLite persistence for scouting shortlists and qualitative evaluation notes.

### 2.7 Methodology & Evidence
- `GET /api/v1/methodology`
  - Returns documentation, mathematical formulas, scoring semantics mapping, and audit reports.
- `GET /api/v1/validation`
  - Returns model validation charts, calibration tables, and feature importances.
