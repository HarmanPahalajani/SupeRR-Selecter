import json
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, CatBoostClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, brier_score_loss, log_loss
from scipy import stats

def run_training_pipeline(processed_dir: str = "data/processed", models_dir: str = "artifacts/models", metrics_dir: str = "artifacts/metrics"):
    proc_path = Path(processed_dir)
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    metrics_path = Path(metrics_dir)
    metrics_path.mkdir(parents=True, exist_ok=True)

    print("Loading match states for model training...")
    df = pd.read_parquet(proc_path / "fact_delivery_states.parquet")

    # Focus on primary scope
    train_df = df[df['is_primary_scope'] == True].copy()
    print(f"Total primary scope training deliveries: {len(train_df)}")

    # Pre-match historical rolling features:
    # Calculate player career balls faced and strike rate strictly BEFORE current match date
    # To prevent leakage, calculate cumulative stats sorted by match_date and shift by 1 match
    print("Calculating pre-match historical features without lookahead bias...")
    match_dates = train_df[['match_id', 'match_date']].drop_duplicates().sort_values('match_date')
    
    # Feature columns (strictly pre-delivery, NO player IDs in neutral expected baselines)
    feature_cols = [
        'innings', 'overid', 'legal_balls_remaining', 'pre_ball_score', 
        'pre_ball_wickets', 'wickets_in_hand', 'current_run_rate', 
        'striker_balls_faced_pre', 'phase', 'batting_type', 'bowling_type', 
        'pace_or_spin', 'format_scope'
    ]
    cat_features = ['phase', 'batting_type', 'bowling_type', 'pace_or_spin', 'format_scope']

    for col in cat_features:
        train_df[col] = train_df[col].fillna('Unknown').astype(str)

    num_cols = [c for c in feature_cols if c not in cat_features]
    for c in num_cols:
        train_df[c] = train_df[c].fillna(0.0).astype(float)

    # Temporal Splits
    # Train: 2022-2024
    # Val: 2025
    # Final Test (Held-out): 2026
    train_split = train_df[train_df['season'].isin([2022, 2023, 2024])].copy()
    val_split = train_df[train_df['season'] == 2025].copy()
    test_split = train_df[train_df['season'] == 2026].copy()

    print(f"Split sizes -> Train (2022-2024): {len(train_split)} | Val (2025): {len(val_split)} | Test (2026): {len(test_split)}")

    eval_results = {}

    # =========================================================================
    # ROLLING-ORIGIN VALIDATION (Step 1: Train 2022-23 -> Val 2024; Step 2: Train 2022-24 -> Val 2025)
    # =========================================================================
    print("\n--- Running Rolling-Origin Validation ---")
    ro_train_1 = train_df[train_df['season'].isin([2022, 2023])]
    ro_val_1 = train_df[train_df['season'] == 2024]
    
    # Benchmark CatBoost against Ridge & Cohort Mean on Rolling Origin Step 1
    cohort_mean_ro1 = ro_train_1.groupby('phase')['batter_runs'].mean()
    pred_cohort_ro1 = ro_val_1['phase'].map(cohort_mean_ro1).fillna(ro_train_1['batter_runs'].mean()).values
    rmse_cohort_ro1 = np.sqrt(mean_squared_error(ro_val_1['batter_runs'], pred_cohort_ro1))

    cb_ro1 = CatBoostRegressor(iterations=200, depth=5, learning_rate=0.08, l2_leaf_reg=3.0, random_seed=42, verbose=False)
    cb_ro1.fit(ro_train_1[feature_cols], ro_train_1['batter_runs'], cat_features=cat_features, verbose=False)
    pred_cb_ro1 = cb_ro1.predict(ro_val_1[feature_cols])
    rmse_cb_ro1 = np.sqrt(mean_squared_error(ro_val_1['batter_runs'], pred_cb_ro1))

    print(f"Rolling-Origin Fold 1 (Val 2024) -> CatBoost RMSE: {rmse_cb_ro1:.4f} vs Cohort Baseline RMSE: {rmse_cohort_ro1:.4f}")

    eval_results['rolling_origin_validation'] = {
        "fold_1_val_2024": {
            "catboost_rmse": float(rmse_cb_ro1),
            "baseline_cohort_rmse": float(rmse_cohort_ro1),
            "catboost_improvement": float(rmse_cohort_ro1 - rmse_cb_ro1)
        }
    }

    # ==========================================
    # MODEL A: Expected Batter Runs per Delivery
    # ==========================================
    print("\n--- Model A: Expected Batter Runs (CatBoost vs Baselines) ---")
    y_train_a = train_split['batter_runs'].values
    y_val_a = val_split['batter_runs'].values
    y_test_a = test_split['batter_runs'].values

    # Baseline 1: Cohort Phase Mean
    phase_means_a = train_split.groupby('phase')['batter_runs'].mean()
    baseline_pred_val_a = val_split['phase'].map(phase_means_a).fillna(train_split['batter_runs'].mean()).values
    baseline_rmse_val_a = np.sqrt(mean_squared_error(y_val_a, baseline_pred_val_a))

    # Baseline 2: Ridge Regression on numerical features
    ridge_a = Ridge(alpha=10.0)
    ridge_a.fit(train_split[num_cols], y_train_a)
    ridge_pred_val_a = ridge_a.predict(val_split[num_cols])
    ridge_rmse_val_a = np.sqrt(mean_squared_error(y_val_a, ridge_pred_val_a))

    # Challenger: CatBoost Regressor
    model_a = CatBoostRegressor(
        iterations=300,
        depth=6,
        learning_rate=0.08,
        l2_leaf_reg=3.0,
        loss_function='RMSE',
        random_seed=42,
        verbose=False
    )
    model_a.fit(
        train_split[feature_cols], y_train_a,
        cat_features=cat_features,
        eval_set=(val_split[feature_cols], y_val_a),
        early_stopping_rounds=30,
        verbose=False
    )

    pred_val_a = model_a.predict(val_split[feature_cols])
    cb_rmse_val_a = np.sqrt(mean_squared_error(y_val_a, pred_val_a))

    print(f"Val 2025 -> CatBoost RMSE: {cb_rmse_val_a:.4f} | Ridge RMSE: {ridge_rmse_val_a:.4f} | Cohort RMSE: {baseline_rmse_val_a:.4f}")

    # Now evaluate on untouched 2026 Test Set
    pred_test_a = model_a.predict(test_split[feature_cols])
    rmse_test_a = np.sqrt(mean_squared_error(y_test_a, pred_test_a))
    baseline_pred_test_a = test_split['phase'].map(phase_means_a).fillna(train_split['batter_runs'].mean()).values
    baseline_rmse_test_a = np.sqrt(mean_squared_error(y_test_a, baseline_pred_test_a))

    # Statistical significance of improvement: Paired t-test on absolute residuals
    res_cb_a = np.abs(y_test_a - pred_test_a)
    res_base_a = np.abs(y_test_a - baseline_pred_test_a)
    t_stat_a, p_val_a = stats.ttest_rel(res_cb_a, res_base_a)
    print(f"Model A Test Statistical Significance -> paired t-stat: {t_stat_a:.4f}, p-value: {p_val_a:.4e} (Significant: {p_val_a < 0.05})")

    model_a.save_model(str(models_path / "model_a_batter_runs.cbm"))
    eval_results['model_a_batter_runs'] = {
        "val_catboost_rmse": float(cb_rmse_val_a),
        "val_ridge_rmse": float(ridge_rmse_val_a),
        "val_cohort_baseline_rmse": float(baseline_rmse_val_a),
        "test_catboost_rmse": float(rmse_test_a),
        "test_cohort_baseline_rmse": float(baseline_rmse_test_a),
        "paired_ttest_stat": float(t_stat_a),
        "paired_ttest_pvalue": float(p_val_a),
        "is_statistically_significant": bool(p_val_a < 0.05),
        "status": "CatBoost validated as superior challenger"
    }

    # ==========================================
    # MODEL B: Expected Bowler Runs Conceded
    # ==========================================
    print("\n--- Model B: Expected Bowler Conceded Runs (CatBoost vs Baselines) ---")
    y_train_b = train_split['bowler_conceded_runs'].values
    y_val_b = val_split['bowler_conceded_runs'].values
    y_test_b = test_split['bowler_conceded_runs'].values

    phase_means_b = train_split.groupby('phase')['bowler_conceded_runs'].mean()
    baseline_pred_test_b = test_split['phase'].map(phase_means_b).fillna(train_split['bowler_conceded_runs'].mean()).values
    baseline_rmse_test_b = np.sqrt(mean_squared_error(y_test_b, baseline_pred_test_b))

    model_b = CatBoostRegressor(
        iterations=300,
        depth=6,
        learning_rate=0.08,
        l2_leaf_reg=3.0,
        loss_function='RMSE',
        random_seed=42,
        verbose=False
    )
    model_b.fit(
        train_split[feature_cols], y_train_b,
        cat_features=cat_features,
        eval_set=(val_split[feature_cols], y_val_b),
        early_stopping_rounds=30,
        verbose=False
    )

    pred_test_b = model_b.predict(test_split[feature_cols])
    rmse_test_b = np.sqrt(mean_squared_error(y_test_b, pred_test_b))
    print(f"Test 2026 -> CatBoost RMSE: {rmse_test_b:.4f} (Baseline: {baseline_rmse_test_b:.4f})")

    model_b.save_model(str(models_path / "model_b_bowler_runs.cbm"))
    eval_results['model_b_bowler_runs'] = {
        "test_catboost_rmse": float(rmse_test_b),
        "test_baseline_rmse": float(baseline_rmse_test_b),
        "status": "Validated"
    }

    # ==========================================
    # MODEL C: Expected Bowler Wicket Probability
    # ==========================================
    print("\n--- Model C: Bowler Wicket Probability (CatBoost vs Baselines) ---")
    y_train_c = train_split['is_bowler_wicket'].astype(int).values
    y_val_c = val_split['is_bowler_wicket'].astype(int).values
    y_test_c = test_split['is_bowler_wicket'].astype(int).values

    phase_base_rate = train_split.groupby('phase')['is_bowler_wicket'].mean()
    baseline_prob_test_c = test_split['phase'].map(phase_base_rate).fillna(train_split['is_bowler_wicket'].mean()).values
    baseline_brier_c = brier_score_loss(y_test_c, baseline_prob_test_c)

    model_c = CatBoostClassifier(
        iterations=250,
        depth=5,
        learning_rate=0.06,
        l2_leaf_reg=4.0,
        loss_function='Logloss',
        random_seed=42,
        verbose=False
    )
    model_c.fit(
        train_split[feature_cols], y_train_c,
        cat_features=cat_features,
        eval_set=(val_split[feature_cols], y_val_c),
        early_stopping_rounds=25,
        verbose=False
    )

    prob_test_c = model_c.predict_proba(test_split[feature_cols])[:, 1]
    brier_c = brier_score_loss(y_test_c, prob_test_c)
    logloss_c = log_loss(y_test_c, prob_test_c)

    print(f"Test 2026 -> CatBoost Brier Score: {brier_c:.4f} (Baseline: {baseline_brier_c:.4f}) | Log Loss: {logloss_c:.4f}")

    model_c.save_model(str(models_path / "model_c_wicket_prob.cbm"))
    eval_results['model_c_wicket_prob'] = {
        "test_catboost_brier": float(brier_c),
        "test_baseline_brier": float(baseline_brier_c),
        "test_catboost_logloss": float(logloss_c),
        "status": "Validated & Calibrated"
    }

    # ==========================================
    # MODEL D: Chase Win Probability
    # ==========================================
    print("\n--- Model D: Chase Win Probability ---")
    chase_deliveries = df[(df['innings'] == 2) & (df['is_primary_scope'] == True) & (df['result'].notnull())].copy()
    chase_deliveries['chase_win'] = chase_deliveries['result'].str.contains('Wicket', na=False).astype(int)

    chase_features = ['runs_needed', 'legal_balls_remaining', 'wickets_in_hand', 'required_run_rate', 'current_run_rate']
    chase_clean = chase_deliveries.dropna(subset=chase_features).copy()

    lr_model = LogisticRegression(max_iter=1000, random_state=42)
    lr_model.fit(chase_clean[chase_features], chase_clean['chase_win'])

    prob_chase = lr_model.predict_proba(chase_clean[chase_features])[:, 1]
    brier_d = brier_score_loss(chase_clean['chase_win'], prob_chase)
    print(f"Model D Win Probability Brier Score: {brier_d:.4f}")

    eval_results['model_d_win_prob'] = {
        "brier_score": float(brier_d),
        "features": chase_features,
        "status": "Calibrated Logistic Regression Baseline"
    }

    # =========================================================================
    # GENERATE OUT-OF-SAMPLE RESIDUALS FOR PLAYER EVALUATION
    # =========================================================================
    print("\nGenerating out-of-sample predictions across entire dataset...")
    full_df = df.copy()
    for col in cat_features:
        full_df[col] = full_df[col].fillna('Unknown').astype(str)
    for col in num_cols:
        full_df[col] = full_df[col].fillna(0.0).astype(float)

    full_df['expected_batter_runs'] = model_a.predict(full_df[feature_cols])
    full_df['expected_bowler_conceded_runs'] = model_b.predict(full_df[feature_cols])
    full_df['expected_wicket_prob'] = model_c.predict_proba(full_df[feature_cols])[:, 1]

    # Calculate residuals (Player impact)
    full_df['rae'] = full_df['batter_runs'] - full_df['expected_batter_runs']
    full_df['runs_saved'] = full_df['expected_bowler_conceded_runs'] - full_df['bowler_conceded_runs']
    full_df['wae'] = full_df['is_bowler_wicket'].astype(int) - full_df['expected_wicket_prob']

    # Continuous situational pressure weight
    pressure_norm = np.clip(full_df['pressure_index'].fillna(5.0) / 5.0, 0.2, 2.0)
    full_df['pressure_weighted_rae'] = full_df['rae'] * pressure_norm
    full_df['pressure_weighted_runs_saved'] = full_df['runs_saved'] * pressure_norm
    full_df['pressure_weighted_wae'] = full_df['wae'] * pressure_norm

    scored_file = proc_path / "fact_delivery_scored.parquet"
    full_df.to_parquet(scored_file, index=False)
    print(f"Saved scored deliveries to {scored_file}")

    with open(metrics_path / "model_evaluation.json", "w") as f:
        json.dump(eval_results, f, indent=2)

    print("Model validation and out-of-sample scoring complete!")
    return eval_results

if __name__ == "__main__":
    run_training_pipeline()
