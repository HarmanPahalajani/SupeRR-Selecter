# SupeRR Intelligence — Analytics Methodology & Mathematical Formulation

**Document Type:** Formal Mathematical Formulation & Statistical Methodology  
**Product:** SupeRR Intelligence  
**Author:** Antigravity Engineering  
**Version:** 1.0.0

---

## 1. Principles of Context-Adjusted Cricket Intelligence

Traditional metrics (Batting Average, Strike Rate, Bowling Average, Economy Rate) conflate individual skill with match situation. A batter facing low-risk deliveries in a dead rubber with 8 wickets in hand is rewarded identically to a finisher hitting 14 off 5 balls against elite death bowling.

SupeRR Intelligence decouples performance into six distinct pillars:
1. **Pressure Intensity $P(t)$:** How demanding the state is before the delivery.
2. **Match Leverage $L(t)$:** Potential swing in win probability on the next event.
3. **Player Impact (RAE/Runs Saved/WAE):** Value delivered relative to a contextual neutral baseline.
4. **Reliability & Bayesian Shrinkage:** Repeatability across matches and shrinkage of small-sample outliers.
5. **Sample Size & Confidence:** Explicit uncertainty bounds (Bootstrap CIs).
6. **Role Suitability & Complementarity:** Phase-specific capability and tactical balance.

---

## 2. Pressure Formulation

### 2.1 Chase Pressure Index (Mallawa Arachchi, Manage & Scariano 2024)
For the team batting second, pressure before delivery $t$ is calculated dynamically:

$$P(t) = \frac{10}{1 + \left(\frac{10}{P(1)} - 1\right) \cdot \exp\left(-10 \cdot k \cdot \sum_{s=1}^{t-1} \Delta C(s) \cdot \Delta R(s)\right)}$$

Where:
- $C(t)$: Required run rate before delivery $t$, defined as:
  $$C(t) = \frac{\text{Runs Required}(t)}{\text{Remaining Legal Balls}(t) / 6}$$
- $R(t)$: Proportion of total innings resources consumed before delivery $t \in [0, 1]$.
  We formulate an empirical resource proxy combining balls bowled and wickets lost:
  $$R(t) = w_b \cdot \left(\frac{\text{Balls Bowled}(t)}{\text{Max Legal Balls}}\right) + w_w \cdot \left(\frac{\text{Wickets Lost}(t)}{10}\right)$$
  Calibrated empirically to mirror the expected run output capacity of remaining wickets and balls.
- $P(1)$: Initial pressure at the start of the chase based on initial target rate:
  $$P(1) = 10 \cdot \frac{C(1)}{C_{\max}}$$
  Where $C_{\max}$ is the empirical 99th-percentile initial required rate in T20 chases (e.g. 13.5 RPO).
- $k$: Sensitivity parameter fitted on training match progressions to minimize loss against match outcome volatility ($k \approx 0.045$).
- $\Delta C(s) = C(s) - C(s-1)$, $\Delta R(s) = R(s) - R(s-1)$.

### 2.2 Defensive Pressure (Bowling Perspective)
Defending a total in the 2nd innings poses inverted risk:
$$P_{\text{def}}(t) = 10 \cdot \left(1 - \text{WinProb}_{\text{chase}}(t)\right) \cdot \left(1 + \frac{\text{Wickets in Hand}}{10}\right)^{-0.5}$$
When the batting side is close to target with many wickets in hand, defensive pressure spikes towards 10.

### 2.3 First-Innings Acceleration Pressure
Because no chase target exists in innings 1, acceleration pressure is measured against venue/season par score $T_{\text{par}}$:
$$P_{\text{inn1}}(t) = 5.0 + 5.0 \cdot \tanh\left(\frac{T_{\text{proj}}(t) - T_{\text{par}}}{25.0}\right)$$
Where $T_{\text{proj}}(t) = \text{Current Score}(t) + \mathbb{E}[\text{Remaining Runs} \mid \text{Balls Rem}, \text{Wickets Lost}]$.

---

## 3. Tabular Expected-Performance Models

All predictions are formed using strictly pre-delivery state features $\mathbf{x}_t$.

### 3.1 Model A: Expected Batter Runs $\mathbb{E}[Y_{\text{bat}} \mid \mathbf{x}_t]$
- **Target:** Verified batter runs $Y_{\text{bat}} \in \{0, 1, 2, 3, 4, 5, 6\}$.
- **Features $\mathbf{x}_t$:** Legal balls remaining, wickets lost, required run rate, match phase (powerplay/middle/death), striker batting position, striker hand (LHB/RHB), bowler style, pace/spin, balls faced by striker in innings.
- **Model:** `CatBoostRegressor` (RMSE objective, depth 6, l2_leaf_reg 3.0).
- **Residual:** $\text{RAE}_t = Y_{\text{bat}, t} - \hat{Y}_{\text{bat}, t}$.

### 3.2 Model B: Expected Bowler Runs Conceded $\mathbb{E}[Y_{\text{bowl}} \mid \mathbf{x}_t]$
- **Target:** Bowler-conceded runs (batter runs + wides + oversteps).
- **Residual:** $\text{Runs Saved}_t = \hat{Y}_{\text{bowl}, t} - Y_{\text{bowl}, t}$.

### 3.3 Model C: Expected Bowler-Credited Wicket $\mathbb{P}(W_{\text{bowl}} = 1 \mid \mathbf{x}_t]$
- **Target:** Binary indicator of dismissal credited to bowler (excluding run outs, retired out, etc.).
- **Model:** `CatBoostClassifier` evaluated via Brier Score and log loss.
- **Residual:** $\text{WAE}_t = W_{\text{bowl}, t} - \hat{p}_{\text{wicket}, t}$.

---

## 4. Empirical Bayes Reliability & Shrinkage

Raw averages over small samples are notoriously noisy. We apply Normal-Normal Empirical Bayes shrinkage within role cohorts $c$:

For player $i$ with $n_i$ match performances $y_{i1}, \dots, y_{in_i}$:
- Sample mean: $\bar{y}_i = \frac{1}{n_i} \sum_{j=1}^{n_i} y_{ij}$
- Within-player variance: $\sigma_i^2 = \text{Var}(y_{ij})$
- Cohort prior mean: $\mu_0 = \frac{1}{M} \sum_{i \in c} \bar{y}_i$
- Cohort between-player variance: $\tau^2 = \max\left(0, \text{Var}_c(\bar{y}_i) - \frac{1}{|c|} \sum_{i \in c} \frac{\sigma_i^2}{n_i}\right)$

The posterior mean (Empirical Bayes estimate) is:
$$\hat{\theta}_i = B_i \mu_0 + (1 - B_i) \bar{y}_i$$
Where the shrinkage factor is:
$$B_i = \frac{\sigma_i^2 / n_i}{\tau^2 + \sigma_i^2 / n_i}$$
As sample size $n_i \to \infty$, $B_i \to 0$ and $\hat{\theta}_i \to \bar{y}_i$. For small sample sizes, the estimate shrinks safely to the cohort baseline $\mu_0$.

---

## 5. Undervalued Talent Detector ("Discovery Gap")

We define the **Discovery Gap** $\Delta_{\text{disc}}$ for player $i$ as:

$$\Delta_{\text{disc}}(i) = \text{Percentile}(\text{Adjusted Pressure Impact}_i) - \text{Percentile}(\text{Conventional Metric}_i)$$

Where:
- Conventional metric for batters = Strike Rate $\times$ Batting Average
- Conventional metric for bowlers = Economy Rate$^{-1} \times$ Bowling Strike Rate$^{-1}$

A player with high adjusted pressure impact (e.g. 88th percentile) whose conventional numbers appear mediocre (e.g. 42nd percentile due to entering in difficult collapses or unselfish death-hitting) exhibits a positive Discovery Gap (+46 percentile points), indicating statistically overlooked value.
