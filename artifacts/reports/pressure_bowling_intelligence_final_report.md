# BOWLING UNDER PRESSURE — UNIFIED BOWLER LEADERBOARD
## Complete Implementation, Mathematical Verification & Analytical Validation Report | SupeRR Intelligence (Rajasthan Royals)

> **Document Type:** Production Engineering, Mathematical Verification & Empirical Validation Report  
> **Platform Version:** SupeRR Intelligence vNext  
> **Target Scope:** Rajasthan Royals Cricket Strategy & Recruitment Intelligence  
> **Dataset Version:** Full Production Dataset (200,999 Total Deliveries; 193,988 Primary Regular Balls, 6,973 Emerging Regular Balls, 38 Super Overs Excluded)  
> **Reconciled Master Population:** 1,217 Unique Master Identities Reconciled Across All Scopes  
> **Backend Test Suite Status:** 106/106 Tests Passed (100% Passing in 11.93s)  

---

## 1. Executive Summary & Core Analytical Answers

This analytical capability answers the primary defensive question:
**"Which bowlers consistently prevent runs and take important wickets when their team is under pressure?"**

### Key Analytical Conclusions across the Assessed Primary Cohort

1. **Jasprit Bumrah ranks #1 in defensive run prevention across the assessed primary IPL/T20I cohort:**
   - Saved **+129.5 runs** above expected in high-pressure match situations across **78.7 pressure overs** in 38 distinct crisis matches.
   - Saves **+1.65 runs per 6 balls** (+1.38 posterior mean).
   - Achieves a **71.1% positive match impact rate** (27 out of 38 matches positive).
   - Conservative Risk-Adjusted Impact (CRAI) of **+1.22 runs/6b**, leading all assessed bowlers with a 95% bootstrap confidence interval of `[+0.86, +1.89]`.
   - Concedes an economy of just **7.97 rpo** in scenarios where expected par economy exceeds **9.62 rpo**.

2. **Haris Rauf ranks #1 in pressure wicket creation across the assessed primary IPL/T20I cohort:**
   - Takes **+13.23 Wickets Above Expected (WAE)** under pressure, ranking **#1 in Wicket Creation**.
   - Captured **31 pressure wickets** in 50.8 pressure overs.
   - Saves **+43.2 runs** (+0.85 runs/6b, CRAI +0.39), placing **#5 overall on the Unified Leaderboard**.
   - Demonstrates that aggressive wicket-taking at the death directly damages opposition win probability.

3. **Nathan Ellis ranks #2 in defensive run prevention across the assessed primary IPL/T20I cohort:**
   - Saved **+45.9 runs** (+1.31 runs/6b, CRAI +0.62) and captured **+2.40 WAE** (15 wickets).
   - Delivers a **68.4% positive match impact rate** across 35.2 pressure overs.

4. **Blessing Muzarabani ranks #3 in defensive run prevention across the assessed primary IPL/T20I cohort:**
   - Saved **+49.9 runs** (+1.08 runs/6b, CRAI +0.55, 63.6% positive match rate across 46.2 overs).
   - Demonstrates elite execution in international cricket that conventional scouting often overlooks.

5. **Wicket Creation and Run Prevention Are Evaluated as Independent Sortable Dimensions:**
   - Taking a pressure wicket has an empirical average value of **7.96 runs prevented** across match states.
   - Rather than enforcing an arbitrary fixed multiplier, the platform delivers **ONE unified leaderboard** with independent sortability by Run Prevention (CRAI Rank) and Wicket Creation (WAE Rank).

---

## 2. Mathematical Formulation of Defensive Bowling Pressure

Active match pressure during play is strictly bounded by $[0.5, 9.8]$, while $0.0$ represents an explicitly handled concluded match state (when the target is reached, $R_{rem} \le 0$, match pressure drops to $0.0$).

### 2.1 First Innings: Surge Containment & Death Tension

In the first innings, the bowling team's objective is restricting opposition acceleration below venue par:

$$\text{Surge}(t) = \frac{\hat{S}_{final}(t) - \text{venue\_par}}{\sigma_{par}}$$

$$\text{DeathChallenge}(t) = \min\left(1.0, \max\left(0.0, \frac{30 - B_{rem}}{30}\right)\right) \times \left(\frac{W_{hand}}{10.0}\right)$$

$$z_1 = 1.15 \times \text{Surge}(t) + 0.90 \times \text{DeathChallenge}(t)$$

$$P_{def, 1st} = \operatorname{clip}\left(\frac{10.0}{1.0 + \exp(-1.10 \times z_1)}, 0.5, 9.8\right)$$

Where:
- $\hat{S}_{final}(t)$: Pre-delivery expected final total predicted by the Primary Ridge model (`expected_score_ridge.joblib`, $R^2 = 0.6974$, alpha=100.0).
- $\text{venue\_par}$: Ground baseline par total (mean: 174.25 runs, $\sigma_{par} = 32.0$).
- $B_{rem}$: Legal balls remaining in the innings (0 to 120).
- $W_{hand}$: Batting team wickets in hand (0 to 10).
- Bounding: Active play pressure is strictly clipped to $[0.5, 9.8]$. When opposition surges above par with wickets in hand near the death, $z_1 > 0 \implies P_{def, 1st} \to 9.8$. When opposition collapses (e.g. 50/5 in 10 overs), $z_1 < 0 \implies P_{def, 1st} \to 0.5$.

### 2.2 Second Innings: Target Defense & Threat Ratio

In the second innings, the bowling team defends a target. The critical defensive metric is the **Threat Ratio ($TR$)**:

$$W_{cap}(W_{hand}) = 6.0 + 0.55 \times W_{hand}$$

$$TR = \frac{W_{cap}(W_{hand})}{\max(RRR, 1.0)}$$

$$T_{progress} = \frac{B_{max} - B_{rem}}{B_{max}}$$

$$S_{margin} = \exp\left(-\frac{R_{rem}}{16.0}\right) \times \mathbf{1}_{B_{rem} \le 18} \times \left(\frac{W_{hand}}{10.0}\right)$$

The combined defensive latent stress $z_2$ is:
$$z_2 = 1.85 \times (TR - 1.0) + 1.50 \times S_{margin} + 0.75 \times T_{progress} \times \mathbf{1}_{TR > 0.80}$$

And the calibrated defensive pressure is:
$$P_{def, 2nd} = \operatorname{clip}\left(\frac{10.0}{1.0 + \exp(-1.20 \times z_2)}, 0.5, 9.8\right)$$

*Concluded Match State (Boundary Distinction):*
- During all active deliveries, defensive pressure is bounded strictly within $[0.5, 9.8]$.
- If the match is concluded or won by the batting team ($R_{rem} \le 0$), the terminal condition sets pressure to $0.0$. Thus, $0.0$ strictly represents a concluded match state, not an active in-play pressure level.

---

## 3. Benchmark Pressure Scenarios & Mathematical Proof

### 3.1 First-Innings Mathematical Reconciliation

#### Resolution of the Documentation Discrepancy:
In an earlier preliminary report draft, the first-innings benchmark row listed $\hat{S}_{final} = 195.0$ and $z_1 = 1.2852$ as approximate mental placeholders. In the actual production engine (`backend/analytics/pressure_bowlers/pressure_engine.py`), expected final score $\hat{S}_{final}$ is evaluated dynamically by `expected_score_ridge.joblib` using the pre-delivery feature vector:
$$\text{Features} = [\text{balls}=60, \text{balls\_rem}=60, \text{score}=110, \text{wkts}=1, \text{wkts\_in\_hand}=9, \text{CRR}=11.0, \text{resource}=0.30, \text{par}=170]$$
The Ridge model evaluates these inputs to $\hat{S}_{final} = \mathbf{211.96}$ runs.

Evaluating the exact production formula with the true Ridge prediction yields:
1. $\text{Surge} = \frac{211.9621 - 170.0}{32.0} = \mathbf{+1.3113}$
2. $\text{DeathChallenge} = \min\left(1.0, \max\left(0, \frac{30 - 60}{30}\right)\right) \times \frac{9}{10} = \mathbf{0.00}$ (middle overs, $B_{rem} \ge 30$)
3. $z_1 = 1.15 \times 1.3113 + 0.90 \times 0.00 = \mathbf{+1.5080}$
4. $P_{def, 1st} = \frac{10.0}{1.0 + \exp(-1.10 \times 1.5080)} = \frac{10.0}{1.0 + \exp(-1.6588)} = \frac{10.0}{1.0 + 0.19036} = \mathbf{8.4008} \to \mathbf{8.40}$

The production code and independent mathematical evaluation are in exact agreement ($8.4008 \text{ vs } 8.4008$).

#### Multi-Scenario First-Innings Validation Table:

The table below evaluates five representative match states plus boundary clipping conditions, comparing raw independent mathematical calculations against the production `DefensiveBowlingPressureEngine`:

| Match State Scenario | Explicit Inputs ($B_{rem}, W_{hand}, \text{Par}$) | Ridge $\hat{S}_{final}$ | Surge | Death Challenge | Latent $z_1$ | Independent Calc | Production Engine | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Middle Overs Surge** (110/1 in 10 ov) | $B=60, W=9, \text{Par}=170$ | 211.96 | +1.311 | 0.00 | +1.508 | **8.40** | **8.40** | **EXACT MATCH** |
| **Early Powerplay Pace** (45/1 in 6 ov) | $B=84, W=9, \text{Par}=170$ | 173.23 | +0.101 | 0.00 | +0.116 | **5.32** | **5.32** | **EXACT MATCH** |
| **Middle Overs Collapse** (50/5 in 10 ov) | $B=60, W=5, \text{Par}=170$ | 128.51 | -1.296 | 0.00 | -1.491 | **1.62** | **1.62** | **EXACT MATCH** |
| **Death Overs Acceleration** (175/2 in 18 ov) | $B=12, W=8, \text{Par}=170$ | 213.28 | +1.353 | 0.48 | +1.988 | **8.99** | **8.99** | **EXACT MATCH** |
| **Death Overs Containment** (140/7 in 18 ov) | $B=12, W=3, \text{Par}=170$ | 153.34 | -0.520 | 0.18 | -0.437 | **3.82** | **3.82** | **EXACT MATCH** |
| **Explicit Par Baseline** (Hypothetical Par) | $B=84, W=9, \text{Par}=170$ | 170.00 | 0.000 | 0.00 | 0.000 | **5.00** | **5.00** | **EXACT MATCH** |
| **Extreme Runaway Surge** (Ceiling Clip) | $B=0, W=10, \text{Par}=170$ | 260.00 | +2.812 | 1.00 | +4.134 | **9.80** | **9.80** | **EXACT MATCH** |
| **Extreme Collapse Floor** (Floor Clip) | $B=60, W=1, \text{Par}=170$ | 80.00 | -2.812 | 0.00 | -3.234 | **0.50** | **0.50** | **EXACT MATCH** |

#### First-Innings Monotonicity Properties:
1. $\frac{\partial P_{def, 1st}}{\partial \hat{S}_{final}} \ge 0$: As expected final score increases, pressure increases monotonically up to the 9.80 ceiling.
2. $\frac{\partial P_{def, 1st}}{\partial W_{hand}} \ge 0$ (during death overs, $B_{rem} < 30$): More wickets in hand during the death overs directly magnifies defensive threat.

---

### 3.2 Second-Innings Target Defense Benchmarks

| Scenario | Match State Inputs ($R_{rem}, B_{rem}, W_{hand}, RRR$) | Threat Ratio ($TR$) | Margin Stress ($S_{margin}$) | Progress ($T_{progress}$) | Latent $z_2$ | Independent Calc | Production Engine | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Situation 1A** (Crisis: 8 off 6, 10 wkts) | $R=8, B=6, W=10, RRR=8.0$ | 1.4375 | 0.6065 | 0.9500 | +2.4317 | **9.49** | **9.49** | **EXACT MATCH** |
| **Situation 1B** (Crisis: 8 off 6, 5 wkts) | $R=8, B=6, W=5, RRR=8.0$ | 1.0938 | 0.3033 | 0.9500 | +1.3408 | **8.33** | **8.33** | **EXACT MATCH** |
| **Situation 1C** (Crisis: 8 off 6, 4 wkts) | $R=8, B=6, W=4, RRR=8.0$ | 1.0250 | 0.2426 | 0.9500 | +1.1227 | **7.94** | **7.94** | **EXACT MATCH** |
| **Situation 2A** (Comfort: 35 off 6, 10 wkts) | $R=35, B=6, W=10, RRR=35.0$ | 0.3286 | 0.1122 | 0.9500 | -1.0738 | **2.16** | **2.16** | **EXACT MATCH** |
| **Situation 2B** (Comfort: 35 off 6, 5 wkts) | $R=35, B=6, W=5, RRR=35.0$ | 0.2500 | 0.0561 | 0.9500 | -1.3034 | **1.73** | **1.73** | **EXACT MATCH** |
| **Situation 3** (Advantage: 40 off 24, 9 wkts) | $R=40, B=24, W=9, RRR=10.0$ | 1.0950 | 0.0000 | 0.8000 | +0.7758 | **7.17** | **7.17** | **EXACT MATCH** |

#### Second-Innings Monotonicity & Behavior Analysis:
1. **Non-Increasing as RRR Increases ($\frac{\Delta P_{def, 2nd}}{\Delta RRR} \le 0$):**
   Holding target progress and wickets in hand constant, second-innings defensive pressure **is non-increasing as RRR increases**:
   - As RRR increases (e.g. from 8.0 to 35.0), Threat Ratio $TR = \frac{W_{cap}(W_{hand})}{\max(RRR, 1.0)}$ decreases (from $1.44 \to 0.33$), which drives latent defensive stress $z_2$ downward.
   - **Clipping Saturation:** Output clipping to $[0.5, 9.8]$ creates flat saturation plateaus where the local derivative is zero ($\frac{\partial P_{def}}{\partial RRR} = 0$) during extreme crisis ($9.80$) or runaway cushions ($0.50$).
   - **ThreatRatio Step Transition:** The progress term $0.75 \times T_{progress} \times \mathbf{1}_{TR > 0.80}$ incorporates an indicator at $TR = 0.80$. When $RRR \ge \frac{W_{cap}}{0.80}$, the indicator steps from $1 \to 0$, producing a discrete downward transition in $z_2$ that reinforces the non-increasing property.
   - Outside of clipping saturation plateaus and across the step transition, $P_{def, 2nd}$ strictly decreases with increasing RRR.
2. **Non-Decreasing in Wickets in Hand ($\frac{\Delta P_{def, 2nd}}{\Delta W_{hand}} \ge 0$):**
   As batting wickets fall (opposition diminished), batting capability $W_{cap}(W_{hand})$ drops, reducing defensive threat.

---

## 4. CRAI Uncertainty Penalty Sensitivity Analysis ($k \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$)

The Conservative Risk-Adjusted Impact (CRAI) for bowlers is:
$$\text{CRAI}(k) = \mu_{post, j} - k \times SE_{post, j}$$
where $\mu_{post, j}$ is the Empirical Bayes posterior mean runs saved per 6 balls and $SE_{post, j}$ is the posterior standard error.

We evaluated five penalty values across the qualified primary bowling cohort (`IPL_T20I`, **$N = 36$ qualified ranked primary bowlers** facing $\ge 4.0$ pressure overs, $\ge 3$ pressure matches, and $\mu_{post} > 0.0$):

### 4.1 Top 10 Bowler Leaderboard across Multipliers $k$

| Rank | $k = 0.00$ (Posterior Mean) | $k = 0.25$ | $k = 0.50$ (Production Compromise) | $k = 0.75$ | $k = 1.00$ (One-Sigma LCB) |
|:---:|---|---|---|---|---|
| **#1** | Jasprit Bumrah (+1.38) | Jasprit Bumrah (+1.30) | **Jasprit Bumrah (+1.22)** | Jasprit Bumrah (+1.14) | Jasprit Bumrah (+1.07) |
| **#2** | Nathan Ellis (+0.84) | Nathan Ellis (+0.73) | **Nathan Ellis (+0.62)** | Nathan Ellis (+0.51) | Nathan Ellis (+0.40) |
| **#3** | Imad Wasim (+0.81) | Blessing Muzarabani (+0.65) | **Blessing Muzarabani (+0.55)** | Blessing Muzarabani (+0.45) | Blessing Muzarabani (+0.35) |
| **#4** | Blessing Muzarabani (+0.75) | Imad Wasim (+0.65) | **Imad Wasim (+0.48)** | Imad Wasim (+0.32) | Haris Rauf (+0.20) |
| **#5** | CB Sole (+0.63) | Haris Rauf (+0.48) | **Haris Rauf (+0.39)** | Haris Rauf (+0.29) | Sunil Narine (+0.18) |
| **#6** | Harry Tector (+0.59) | CB Sole (+0.45) | **Sunil Narine (+0.34)** | Sunil Narine (+0.26) | Imad Wasim (+0.16) |
| **#7** | Haris Rauf (+0.58) | Harry Tector (+0.44) | **Harry Tector (+0.29)** | Harry Tector (+0.14) | Harry Tector (+0.00) |
| **#8** | Sunil Narine (+0.51) | Sunil Narine (+0.43) | **CB Sole (+0.28)** | CB Sole (+0.10) | Eshan Malinga (-0.03) |
| **#9** | Matthew Humphreys (+0.33) | Eshan Malinga (+0.24) | **Eshan Malinga (+0.15)** | Eshan Malinga (+0.06) | Noor Ahmad (-0.07) |
| **#10** | Eshan Malinga (+0.33) | Matthew Humphreys (+0.19) | **Noor Ahmad (+0.10)** | Noor Ahmad (+0.00) | CB Sole (-0.08) |

### 4.2 Cohort Stability & Overlap vs Production ($k = 0.50$)

| Multiplier $k$ | Top 10 Overlap with $k=0.50$ | Top 25 Overlap with $k=0.50$ | Spearman $\rho$ vs $k=0.50$ | Kendall $\tau$ vs $k=0.50$ |
|:---:|:---:|:---:|:---:|:---:|
| **$k = 0.00$** | 9 / 10 (90.0%) | 22 / 25 (88.0%) | 0.9277 | 0.7841 |
| **$k = 0.25$** | 9 / 10 (90.0%) | 24 / 25 (96.0%) | 0.9856 | 0.9175 |
| **$k = 0.50$ (Production)** | **10 / 10 (100.0%)** | **25 / 25 (100.0%)** | **1.0000** | **1.0000** |
| **$k = 0.75$** | 10 / 10 (100.0%) | 24 / 25 (96.0%) | 0.9902 | 0.9397 |
| **$k = 1.00$** | 10 / 10 (100.0%) | 24 / 25 (96.0%) | 0.9732 | 0.8825 |

### 4.3 Production Interpretation: $k = 0.50$ as a Calibrated Trade-Off

Rather than asserting that $k = 0.50$ is uniquely mathematically optimal, **$k = 0.50$ is selected as a principled production compromise** across the 36 qualified primary bowlers:
1. **Pillar Stability:** The elite podium (**Jasprit Bumrah #1, Nathan Ellis #2, Blessing Muzarabani #3**) is 100% stable across all $k \ge 0.25$.
2. **Mitigation of Small-Sample Spikes:** At $k=0.00$ (no uncertainty penalty), small-sample bowlers like CB Sole (7.8 overs) and Matthew Humphreys (17.6 overs) displace established high-volume anchors like Sunil Narine and Noor Ahmad purely on sample noise. A half-sigma penalty ($k=0.50$) properly anchors high-volume repeatability.
3. **Prevention of Excessive Sampling Penalties:** At $k=1.00$, bowlers with 45–60 pressure overs who performed solidly (e.g. Noor Ahmad, Eshan Malinga) receive negative CRAI scores solely due to sampling penalty, distorting genuine positive contributions.
4. **Summary:** $k=0.50$ is an operational compromise balancing sample variance control with fair credit for proven contributors.

---

## 5. Comprehensive Chronological Predictive Validation

To evaluate future performance prediction, a chronological out-of-sample forward evaluation was executed:
- **Historical Basis:** Matches played $\le 2024$.
- **Forward Horizon:** Matches played in calendar year **2025**.
- **Forward Evaluation Cohort:** All bowlers delivering $\ge 2.0$ pressure overs in 2025 ($N = 275$ qualifying bowlers).

> [!WARNING]
> **Predictive Interpretation Caveats & Strict Qualification:**
> The chronological validation across the cohort of 275 bowlers does **not** establish proven predictive skill:
> - **Opportunity-Adjusted Wicket-Taking Skill (Future WAE):** Out-of-sample Spearman rank correlation is essentially zero ($\rho = +0.0323, p = 0.6504, 95\%\text{ CI } [-0.1072, +0.1708]$). Future WAE Precision@20 is **50.0% (10 / 20)** against a **49.1% (135 / 275)** baseline prevalence—yielding negligible predictive lift (+0.9 percentage points) over random chance.
> - **Raw Crisis Wickets vs Opportunity-Adjusted Skill:** The observed 95.0% (19 / 20) Precision@20 for capturing $\ge 2$ future crisis wickets represents **preliminary selection evidence** that is heavily influenced by **future pressure-over exposure and tactical assignment** (bowlers trusted in crisis overs in 2024 are systematically assigned crisis overs again in 2025, accumulating raw counts through volume) rather than proven out-of-sample opportunity-adjusted skill.
> - **Run Prevention (Runs Saved):** Spearman rank correlation across seasons is essentially zero ($\rho = -0.0063, p = 0.9292$).
> - Consequently, this platform **does not describe defensive bowling ratings as proven predictive skill**, but rather as robust, risk-adjusted retrospective measures of historical crisis execution.

### 5.1 Out-of-Sample Predictive Results

| Predictive Target | Exact Ranking Metric Used for Top-K | Success Definition | Out-of-Sample Spearman $\rho$ | 95% Fisher $z$ CI | $p$-value | Top 10 Precision (Wilson 95% CI) | Top 20 Precision (Wilson 95% CI) | Baseline Prevalence (Wilson 95% CI) | Top 20 Lift over Baseline |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Future Crisis Wickets (Raw Count)** | Historical Pressure Wickets / Match | $\ge 2$ crisis wickets captured in 2025 | **+0.0438** | `[-0.0958, +0.1818]` | 0.5387 | **9 / 10 (90.0%)** `[59.6%, 98.2%]` | **19 / 20 (95.0%)** `[76.4%, 99.1%]` | 181 / 275 (65.8%) `[60.0%, 71.2%]` | **+29.2 percentage points** |
| **Future WAE (Skill)** | Historical WAE per 6 balls | Positive future WAE ($> 0.00$) | **+0.0323** | `[-0.1072, +0.1708]` | 0.6504 | **6 / 10 (60.0%)** `[31.3%, 83.2%]` | **10 / 20 (50.0%)** `[29.9%, 70.1%]` | 135 / 275 (49.1%) `[43.2%, 55.0%]` | **+0.9 percentage points** |
| **Future Run Saving** | Historical CRAI ($k=0.50$) | Positive future runs saved ($> 0.00$) | **-0.0063** | `[-0.1453, +0.1329]` | 0.9292 | **4 / 10 (40.0%)** `[16.8%, 68.7%]` | **4 / 20 (20.0%)** `[8.1%, 41.6%]` | 76 / 275 (27.6%) `[22.7%, 33.2%]` | **-7.6 percentage points** |
| **Naive Benchmark** | Career Economy Rate | Positive future runs saved ($> 0.00$) | **+0.0864** | `[-0.0531, +0.2223]` | 0.2250 | **3 / 10 (30.0%)** `[10.8%, 60.3%]` | **5 / 20 (25.0%)** `[11.2%, 46.9%]` | 76 / 275 (27.6%) `[22.7%, 33.2%]` | **-2.6 percentage points** |

*(Note on Lift Metrics: Top-10 selection lift for crisis wicket-taking is $90.0\% - 65.8\% = \mathbf{+24.2\text{ percentage points}}$. Top-20 selection lift is $95.0\% - 65.8\% = \mathbf{+29.2\text{ percentage points}}$.)*

### 5.2 Deep Analytical Interpretation for Cricket Strategy:

1. **Distinguishing Raw Crisis-Wicket Accumulation from Opportunity-Adjusted Wicket Skill:**
   - **Raw Crisis Wicket Accumulation:** Top 20 historical crisis wicket-takers achieved an out-of-sample success rate of **19 / 20 (95.0%, 95% CI: `[76.4%, 99.1%]`)** in capturing at least two crisis wickets in 2025, compared to a baseline prevalence of **181 / 275 (65.8%, 95% CI: `[60.0%, 71.2%]`)**, representing a **+29.2 percentage-point lift**. However, this result is **strictly preliminary** and is heavily confounded by **opportunity exposure**: teams entrust death overs to established frontline death bowlers, granting them repeated high-pressure volume to accumulate raw wickets.
   - **Opportunity-Adjusted Skill (Future WAE):** When evaluating genuine underlying efficiency per opportunity via Future WAE (Wickets Above Expected per 6 balls), the Top 20 historical bowlers achieve a success rate of only **10 / 20 (50.0%, 95% CI: `[29.9%, 70.1%]`)**, which is statistically indistinguishable from the population baseline of **135 / 275 (49.1%, 95% CI: `[43.2%, 55.0%]`)** (lift: **+0.9 percentage points**), with a non-significant Spearman correlation of **+0.0323** ($p = 0.6504$).
   - **Conclusion on Predictive Claims:** We explicitly **do not describe bowling pressure metrics as proven predictive skill**. They capture reliable, risk-adjusted retrospective performance under past pressure, not guaranteed forward-looking forecasting.
2. **High Sample Variance in Seasonal Bowling Economy:**
   Run prevention under defensive pressure exhibits near-zero rank correlation across seasons ($\rho = -0.0063$). In modern T20 cricket, high-pressure defensive bowling samples are inherently small: even frontline death bowlers typically deliver only 4 to 8 defensive pressure overs per season. At the death, single execution edges (e.g., a ball flying off an outside edge over third man vs being caught at deep point) swing an over's economy from 6.0 to 10.0, introducing substantial stochastic noise that degrades full-spectrum rank persistence.
3. **Dual-Ranking Design Vindicated:**
   Because run-saving economy is noisy while wicket-taking capacity shows practical selection utility in the upper tail, SupeRR Intelligence refuses to collapse bowling into an arbitrary single composite score. Instead, it provides **independent sortability by Run Prevention (CRAI) and Wicket Creation (WAE)**.

---

## 6. Population Accounting & Precise Terminology Reconciliation

The master player population in `data/processed/dim_player.parquet` (1,217 players) reconciles with 100% mathematical precision:

```
Total Master Player Identities: 1,217
├── Primary Competition Participants (IPL & T20I Regular Matches): 891
│   ├── Primary-Scope Bowlers (bowled >= 1 delivery in IPL/T20I): 596
│   │   ├── Primary Bowlers with High-Pressure Exposure (hp_overs > 0): 511
│   │   └── Primary Bowlers without High-Pressure Exposure (hp_overs == 0): 85
│   └── Primary-Scope Pure Batters (faced >= 1 delivery in IPL/T20I, 0 balls bowled): 295
│   Check: 596 primary bowlers + 295 primary pure batters = 891 primary participants
├── Emerging-Only Competition Participants (0 primary-scope deliveries): 67
│   ├── Emerging-Only Bowlers (bowled >= 1 ball in Emerging comps): 31
│   └── Emerging-Only Pure Batters (faced >= 1 ball in Emerging comps, 0 balls bowled): 36
│   Check: 31 emerging bowlers + 36 emerging pure batters = 67 emerging participants
└── Squad Reserves / Zero Tracked Delivery Identities: 259
Grand Total Arithmetic Check: 891 + 67 + 259 = 1,217 Unique Master Identities (100.0% Reconciled)
```

### Complete Definitions & Product Terminology:

| Population Group | Exact Count | Formal Product Definition |
|---|:---:|---|
| **Master Identities** | **1,217** | Complete roster of tracked players in `dim_player.parquet` across primary, emerging, and squad reserve roles. |
| **Primary Competition Participants** | **891** | Players who participated in at least one regulation delivery (batting or bowling) in IPL or T20I matches. |
| **Primary-Scope Bowlers** | **596** | Players who bowled at least one regular delivery in IPL or T20I matches. |
| **Primary Bowlers with High-Pressure Exposure** | **511** | Primary-scope bowlers who faced at least one qualifying defensive high-pressure delivery ($\text{hp\_overs} > 0$). |
| **Primary Bowlers without High-Pressure Exposure** | **85** | Primary-scope bowlers who bowled only in low- or medium-pressure match phases ($\text{hp\_overs} = 0$). |
| **Primary-Scope Pure Batters** | **295** | Primary-scope participants who batted in IPL/T20I but never bowled a delivery ($891 - 596 = 295$). |
| **Emerging-Only Participants** | **67** | Players who competed strictly in Emerging tournaments with zero regular deliveries in IPL/T20I matches (31 bowlers, 36 pure batters). |
| **Reserves / Zero Tracked Deliveries** | **259** | Squad members or historical identities with no tracked regulation delivery involvement. |

*(Resolution of Terminology Ambiguity: Previous preliminary drafts occasionally referred to the 511 assessed bowlers as "total primary bowlers." This report establishes the exact distinction: there are 596 total primary bowlers, of whom 511 had high-pressure exposure and 85 had no high-pressure exposure.)*

---

## 7. Dual-Tier Ranking Eligibility & Clean Cricket Scoring

### 7.1 Qualification Rules

Qualification rules are explicitly configured in [ranking.py#L27](file:///c:/Users/Win11%20Pro/Desktop/Rajasthan%20Royals%20Competition/backend/analytics/pressure_bowlers/ranking.py#L27):

| Competition Scope | Minimum Pressure Overs | Minimum Pressure Matches | Posterior Mean Condition | Qualified & Ranked Bowlers |
|---|:---:|:---:|:---:|:---:|
| **Primary Scope (`IPL_T20I`)** | $\ge 4.0$ overs (24 balls) | $\ge 3$ distinct matches | $\mu_{post} > 0.0$ | **36 Ranked** |
| **IPL Only** | $\ge 4.0$ overs (24 balls) | $\ge 3$ distinct matches | $\mu_{post} > 0.0$ | **14 Ranked** |
| **T20I Only** | $\ge 4.0$ overs (24 balls) | $\ge 3$ distinct matches | $\mu_{post} > 0.0$ | **41 Ranked** |
| **Emerging Scope (`EMERGING`)** | $\ge 2.0$ overs (12 balls) | $\ge 2$ distinct matches | $\mu_{post} > 0.0$ | **20 Ranked** |

### 7.2 Clean Cricket Scoring Verification

Across all **31,442 defensive high-pressure deliveries** in `fact_delivery_scored.parquet`:
1. **Bowler Conceded Runs ($c_i$):** Strictly includes batter runs, wides, and no-ball extras ($\text{bowler\_conceded\_runs} = \text{batter\_runs} + \text{extras\_wide\_runs} + \text{extras\_noball\_runs}$). Strictly excludes byes, leg-byes, and penalty runs.
2. **Legal Deliveries Faced:** Wides and no-balls do not count as legal balls. Economy rates are strictly computed per 6 legal balls.
3. **Wicket Attribution:** Non-bowler dismissals (run-outs, retired out, timed out) are strictly excluded from $w_i$ and WAE.
4. **Zero-Ball Bowlers:** Non-bowlers receive `None` for economy rate, never an erroneous `0.00`.

---

## 8. Full-Dataset Batting Wide-Ball Audit Evidence

To ensure complete empirical closure beyond isolated unit tests, the full production dataset (`data/processed/fact_delivery_scored.parquet`) was audited and the production batting pressure pipeline was re-executed.

### 8.1 Delivery-Level Verification Across the Full Dataset

| Metric / Audit Parameter | Full Dataset Count | Analytical Interpretation | Status |
|---|:---:|---|:---:|
| **Total Canonical Deliveries** | **200,961** | Full regulation delivery corpus (excluding 38 Super Overs). | **VERIFIED** |
| **Total Wide Deliveries** | **7,710** | Complete dataset wides (`extras_wide_runs > 0`). | **VERIFIED** |
| **Total High-Pressure Deliveries** | **49,679** | Qualified under DynamicPressureEngine (47,935 Primary, 1,744 Emerging). | **VERIFIED** |
| **Total High-Pressure Wide Deliveries** | **2,021** | Qualified pressure wides (1,967 Primary, 54 Emerging). | **VERIFIED** |
| **HP Wides Contributing to Batting $\mathbb{E}$ or RAE BEFORE Fix** | **2,021 (100.0%)** | All pressure wides were previously docked with negative RAE. | **DEFECT IDENTIFIED** |
| **HP Wides Contributing to Batting $\mathbb{E}$ or RAE AFTER Fix** | **0 (0.00%)** | Wides strictly contribute 0 expected runs and 0 RAE to batters. | **CORRECTED & VERIFIED** |
| **High-Pressure Legal Byes & Leg-Byes** | **784** | 100% legal balls faced (`is_legal_ball = True`), 0 batter runs, valid negative RAE. | **PRESERVED** |
| **Bowler-Conceded Runs Inclusion** | **7,710 (100.0%)** | All wides remain fully counted in bowler-conceded runs in bowling pipeline. | **PRESERVED** |

### 8.2 Production Leaderboard Recomputation Results

- **Recomputed Tables**: All 5,034 metrics records in `fact_player_pressure_metrics.parquet` and 21,004 match evidence records in `fact_player_pressure_matches.parquet` were completely re-aggregated and synchronized to DuckDB (`data/app/analytics.duckdb`).
- **Batters Affected**: Across the 124 evaluated Primary batters, **112 batters** gained back legitimate credit previously docked for opposition wides (average gain: **+10.516 runs**).
- **Major Gained Credit**: Namboori Tilak Varma (+66.225 runs), Tim David (+37.871 runs), Shivam Dube (+36.036 runs), Abhishek Sharma (+23.628 runs), Suryakumar Yadav (+22.287 runs), Jason Holder (+17.086 runs), Dhruv Jurel (+16.492 runs), Ashutosh Sharma (+13.940 runs), Sunil Narine (+12.811 runs), Travis Head (+9.602 runs).
- **Balls Faced Invariance**: Total balls faced (`hp_balls`) remained strictly unchanged ($\Delta = 0.00$) across all players because wides were already excluded from `is_legal_ball`.

---

## 9. Verification & Backend Test Suite Status (106/106 Passing)

The full platform test suite passes with 100% compliance:
- `backend/tests/test_defensive_pressure_independent_verification.py`: **5 passed** (Independent formula verification across Situation 1A/B/C, 2A/B, 3, all five first-innings match states, clipping ceiling/floor, and monotonicity).
- `backend/tests/test_pressure_bowlers.py`: **16 passed** (Scoring rules, WAE, shrinkage, endpoints).
- `backend/tests/test_batting_wide_rae_attribution.py`: **5 passed** (Batting wide RAE zeroing, ball faced exclusion, bye/leg-bye preservation, bowler wide inclusion).
- Full regression suite: **106 passed in 11.93s** (`python -m pytest backend/tests/ -q`).

---

## 10. Final Analytical Sign-Off

This sign-off certifies the defensive bowling analytics across four independent dimensions:

1. **Mathematical Correctness: CERTIFIED**
   - The production defensive bowling pressure engine in `backend/analytics/pressure_bowlers/pressure_engine.py` implements the validated logistic activation formula across both innings.
   - First-innings defensive pressure evaluates opposition surge above par and death-phase acceleration, matching independent calculations to exact machine precision ($8.4008 \text{ vs } 8.4008$) across all representative match states.
   - Second-innings defensive pressure is non-increasing as RRR increases across all regions (saturation plateaus, ThreatRatio indicator step at $TR=0.80$, and active gradient intervals).
   - Independent formula calculations agree with the production engine across all benchmark scenarios at exact machine precision.
2. **Data Integrity & Cricket Scoring: CERTIFIED**
   - Bowler conceded runs strictly incorporate wide and no-ball extras while excluding byes, leg-byes, and penalties.
   - Non-bowler dismissals (run-outs) are excluded from bowler wicket credit.
   - Zero-ball bowlers receive null economy rates, never an erroneous 0.00.
   - Master population accounting reconciles all 1,217 identities with zero leakage: 891 primary (596 bowlers: 511 HP, 85 non-HP; 295 pure batters) + 67 Emerging-only + 259 squad reserves.
   - Scope partition is strictly unified across all 200,961 regular deliveries: Primary (193,988 deliveries) and Emerging (6,973 deliveries across the 30 ACC tournament matches).
   - Batting wide-ball audit confirmed across all 200,961 deliveries: 2,021 high-pressure wides zeroed in batting RAE, 784 legal byes/leg-byes preserved, and full leaderboard recomputed.
3. **Historical Ranking Stability: CERTIFIED**
   - Podium order (#1 Bumrah, #2 Ellis, #3 Muzarabani) is 100% stable across $k \in [0.25, 1.00]$.
   - $k = 0.50$ is confirmed as a robust production compromise across the 36 qualified primary bowlers, balancing sample shrinkage against unpenalized noise.
4. **Predictive Validity: LIMITATIONS DOCUMENTED — PREDICTIVE SKILL NOT ESTABLISHED**
   - Chronological validation does not establish strong rank predictability for bowling economy (Spearman $\rho = -0.0063, p = 0.9292$), reflecting death-bowling sample sparsity and single-ball boundary execution variance.
   - For wicket creation, Future WAE (opportunity-adjusted skill) yields Spearman $\rho = +0.0323$ ($p = 0.6504$) and Precision@20 of **50.0% (10 / 20)** vs a **49.1% (135 / 275)** baseline (+0.9 percentage points lift), confirming no statistically significant rank-predictive signal for underlying skill.
   - The observed 95.0% (19/20) Precision@20 for capturing $\ge 2$ future crisis wickets represents preliminary selection evidence that is substantially confounded by tactical role persistence and death-over exposure rather than proven predictive skill.
   - Ratings are certified as risk-adjusted retrospective evaluations, not forward-looking predictive guarantees. Do not describe this as proven predictive skill.
