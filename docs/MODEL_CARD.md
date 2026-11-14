# SupeRR Intelligence — Model Cards

**Document Type:** Formal Machine Learning Documentation & Evaluation Standards  
**Product:** SupeRR Intelligence  
**Author:** Antigravity Engineering  
**Version:** 1.0.0

---

## Model Card Summary

| Model | Task | Algorithm | Target Variable | Primary Metric | Baseline Comparison |
|---|---|---|---|---|---|
| **Model A: Expected Batter Runs** | Regression | CatBoostRegressor (CPU) | Batter runs on delivery (0-6) | RMSE / MAE | Cohort Over/Phase Mean |
| **Model B: Expected Bowler Runs** | Regression | CatBoostRegressor (CPU) | Bowler-conceded runs | RMSE / MAE | Over/Phase Phase Mean |
| **Model C: Wicket Probability** | Classification | CatBoostClassifier (CPU) | Bowler-credited wicket (0/1) | Brier Score / Log Loss | Match Phase Base Rate |
| **Model D: Win Probability** | Classification | Calibrated CatBoostClassifier | Chase Win Indicator (0/1) | Brier Score / Log Loss | Historical Target Logistic |

---

## 1. Intended Use & Boundaries

- **Intended Use:** Evaluate contextual run-production, run-prevention, and wicket-creation ability on ball-by-ball T20 and IPL data to inform talent scouting, comparison, and auction planning.
- **Out of Scope:** Predicting individual player career trajectories over decades, real-time betting, predicting injury susceptibility, or predicting unobserved auction hammer prices.

## 2. Validation Protocol & Non-Leakage Guarantee

- **Temporal Holdout:**
  - **Train Set:** Seasons 2022 to 2024 (earliest temporal window).
  - **Validation Set:** Season 2025 (hyperparameter tuning & calibration).
  - **Test Set:** Season 2026 (final out-of-sample evaluation).
- **Grouped Integrity:** Validation is strictly grouped by `match_id`. No deliveries from the same match appear across both train and test splits.
- **Strict Pre-Delivery Features:** Input vectors contain only information knowable *before* the bowler releases the ball. No post-delivery score, final match outcome, or dismissal variables are permitted as predictors.

## 3. Metrics & Calibration Standards

- **Calibration Curve:** All probability outputs are evaluated using Reliability Diagrams (binned observed frequency vs. predicted probability).
- **Brier Score:** $\text{Brier} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$. A lower score indicates superior calibration and sharpness.
- **Feature Importance:** Permutation importance on the held-out validation set to guarantee that features contribute generalizeable signal without overfitting.
