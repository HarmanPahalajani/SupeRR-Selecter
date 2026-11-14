import os
import json
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, CatBoostClassifier
from sklearn.metrics import mean_squared_error, brier_score_loss, log_loss

print("--- 1. Checking ML Artifact Files ---")
models = {
    "Model A": "artifacts/models/model_a_batter_runs.cbm",
    "Model B": "artifacts/models/model_b_bowler_runs.cbm",
    "Model C": "artifacts/models/model_c_wicket_prob.cbm",
    "Model Evaluation": "artifacts/metrics/model_evaluation.json",
}

for name, path in models.items():
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"  {name}: {path} -> Exists: {exists}, Size: {size} bytes")
    assert exists, f"Missing model file: {path}"

print("\n--- 2. Loading Saved Models & Running Inference ---")
model_a = CatBoostRegressor()
model_a.load_model(models["Model A"])
print("  Loaded Model A successfully.")

model_b = CatBoostRegressor()
model_b.load_model(models["Model B"])
print("  Loaded Model B successfully.")

model_c = CatBoostClassifier()
model_c.load_model(models["Model C"])
print("  Loaded Model C successfully.")

with open(models["Model Evaluation"], "r") as f:
    eval_meta = json.load(f)
print(f"  Loaded Model D meta successfully: {eval_meta['model_d_win_prob']}")

print("\n--- 3. Testing Real Processed Records for Inference, NaNs, Infs ---")
scored_path = "data/processed/fact_delivery_scored.parquet"
assert os.path.exists(scored_path)
df_scored = pd.read_parquet(scored_path)
print(f"  Loaded fact_delivery_scored: {len(df_scored)} records.")

test_2026 = df_scored[df_scored["season"] == "2026"].copy()
if len(test_2026) == 0:
    test_2026 = df_scored[df_scored["season"] == 2026].copy()
print(f"  Year 2026 test deliveries count: {len(test_2026)}")
assert len(test_2026) > 0, "No 2026 test records found!"

# Verify no NaNs or infs in expectations
for col in ["expected_batter_runs", "expected_bowler_conceded_runs", "expected_wicket_prob"]:
    n_nans = test_2026[col].isna().sum()
    n_infs = np.isinf(test_2026[col]).sum()
    print(f"  Check {col}: NaNs = {n_nans}, Infs = {n_infs}")
    assert n_nans == 0, f"Found NaNs in {col}"
    assert n_infs == 0, f"Found Infs in {col}"

# Test inference using model_a on 100 sample records
feature_cols = list(model_a.feature_names_)
cat_features = ['phase', 'batting_type', 'bowling_type', 'pace_or_spin', 'format_scope']
# Compute enhanced features if missing from slice
test_2026_feat = test_2026.copy()
if 'batting_order_num' not in test_2026_feat.columns:
    test_2026_feat['batting_order_num'] = test_2026_feat['batting_order'].fillna(4.0).clip(1, 11).astype(float)
if 'situational_pressure' not in test_2026_feat.columns:
    test_2026_feat['situational_pressure'] = test_2026_feat['pressure_index'].fillna(5.0).clip(0.5, 10.0).astype(float)
if 'rrr_crr_diff' not in test_2026_feat.columns:
    test_2026_feat['rrr_crr_diff'] = np.where(
        test_2026_feat['innings'] == 2,
        (test_2026_feat['required_run_rate'].fillna(8.0) - test_2026_feat['current_run_rate'].fillna(7.0)).clip(-10.0, 20.0),
        0.0
    ).astype(float)
if 'resource_buffer' not in test_2026_feat.columns:
    test_2026_feat['resource_buffer'] = (test_2026_feat['legal_balls_remaining'] / np.maximum(test_2026_feat['wickets_in_hand'], 1)).clip(1.0, 60.0).astype(float)

sample_batch = test_2026_feat[feature_cols].iloc[:100].copy()
for col in cat_features:
    if col in sample_batch.columns:
        sample_batch[col] = sample_batch[col].fillna('Unknown').astype(str)
for col in [c for c in feature_cols if c not in cat_features]:
    sample_batch[col] = sample_batch[col].fillna(0.0).astype(float)

preds_a = model_a.predict(sample_batch)
assert len(preds_a) == 100
assert not np.isnan(preds_a).any()
assert not np.isinf(preds_a).any()
print("  Inference test on Model A passed cleanly.")

print("\n--- 4. Reproducing 2026 Metrics & Evaluating Improvements ---")
# Model A RMSE
y_true_a = test_2026["batter_runs"].values
rmse_catboost_a = np.sqrt(mean_squared_error(y_true_a, test_2026["expected_batter_runs"]))
phase_means_a = df_scored[df_scored["season"].isin(["2022", "2023", "2024", 2022, 2023, 2024])].groupby('phase')['batter_runs'].mean()
baseline_pred_test_a = test_2026['phase'].map(phase_means_a).fillna(df_scored[df_scored["season"].isin(["2022", "2023", "2024", 2022, 2023, 2024])]['batter_runs'].mean()).values
rmse_baseline_a = np.sqrt(mean_squared_error(y_true_a, baseline_pred_test_a))
print(f"  Model A 2026 RMSE: CatBoost = {rmse_catboost_a:.4f} | Baseline = {rmse_baseline_a:.4f}")

# Model B RMSE
y_true_b = test_2026["bowler_conceded_runs"].values
rmse_catboost_b = np.sqrt(mean_squared_error(y_true_b, test_2026["expected_bowler_conceded_runs"]))
phase_means_b = df_scored[df_scored["season"].isin(["2022", "2023", "2024", 2022, 2023, 2024])].groupby('phase')['bowler_conceded_runs'].mean()
baseline_pred_test_b = test_2026['phase'].map(phase_means_b).fillna(df_scored[df_scored["season"].isin(["2022", "2023", "2024", 2022, 2023, 2024])]['bowler_conceded_runs'].mean()).values
rmse_baseline_b = np.sqrt(mean_squared_error(y_true_b, baseline_pred_test_b))
print(f"  Model B 2026 RMSE: CatBoost = {rmse_catboost_b:.4f} | Baseline = {rmse_baseline_b:.4f}")

# Model C Brier & Calibration
y_true_c = test_2026["is_bowler_wicket"].values
brier_catboost_c = brier_score_loss(y_true_c, test_2026["expected_wicket_prob"])
logloss_c = log_loss(y_true_c, test_2026["expected_wicket_prob"])
print(f"  Model C 2026 Brier Score: {brier_catboost_c:.4f} | Log Loss: {logloss_c:.4f}")
print(f"  Observed wicket rate: {y_true_c.mean():.4f} | Mean predicted prob: {test_2026['expected_wicket_prob'].mean():.4f}")

# Probability Calibration Check
from sklearn.calibration import calibration_curve
prob_true, prob_pred = calibration_curve(y_true_c, test_2026["expected_wicket_prob"], n_bins=5)
print(f"  Calibration curve (pred -> true): {list(zip(np.round(prob_pred, 4), np.round(prob_true, 4)))}")

print("\n--- 5. Player Ranking Stability Across Percentiles (70th, 75th, 80th, 85th) ---")
fact_player = pd.read_parquet("data/processed/fact_player_metrics.parquet")
print(f"  Total players in metric store: {len(fact_player)}")

qualified_batters = fact_player[fact_player["balls_faced"] >= 60].copy()
print(f"  Qualified batters (>=60 balls): {len(qualified_batters)}")

# Calculate stability of Top 10 rankings under different sample thresholds / percentiles
p70 = qualified_batters["balls_faced"].quantile(0.70)
p75 = qualified_batters["balls_faced"].quantile(0.75)
p80 = qualified_batters["balls_faced"].quantile(0.80)
p85 = qualified_batters["balls_faced"].quantile(0.85)

top10_p70 = set(qualified_batters[qualified_batters["balls_faced"] >= p70].sort_values("eb_batting_impact", ascending=False).head(10)["player_id"])
top10_p75 = set(qualified_batters[qualified_batters["balls_faced"] >= p75].sort_values("eb_batting_impact", ascending=False).head(10)["player_id"])
top10_p80 = set(qualified_batters[qualified_batters["balls_faced"] >= p80].sort_values("eb_batting_impact", ascending=False).head(10)["player_id"])
top10_p85 = set(qualified_batters[qualified_batters["balls_faced"] >= p85].sort_values("eb_batting_impact", ascending=False).head(10)["player_id"])

overlap_70_75 = len(top10_p70.intersection(top10_p75)) / 10.0
overlap_75_80 = len(top10_p75.intersection(top10_p80)) / 10.0
overlap_80_85 = len(top10_p80.intersection(top10_p85)) / 10.0
print(f"  Top 10 Batter Stability: 70th vs 75th = {overlap_70_75*100}%, 75th vs 80th = {overlap_75_80*100}%, 80th vs 85th = {overlap_80_85*100}%")

print("\n--- 6. Auditing Extras_Type in Raw Ingestion ---")
raw_bbb = pd.read_csv("data/raw/ball_by_ball.csv")
illegal_extras = ['wide', 'Overstep', 'other']
known_extras = set(illegal_extras + ['byes', 'legbyes', 'Penalty'])
observed_extras = set(raw_bbb['extras_type'].dropna().unique())
unknown_extras = observed_extras - known_extras
print(f"  Observed extras_type values: {observed_extras}")
print(f"  Audit result: Unknown extras count = {len(unknown_extras)}")
assert len(unknown_extras) == 0, f"Found unknown extras: {unknown_extras}"

print("\nALL ML VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")
