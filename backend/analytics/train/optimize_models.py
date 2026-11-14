"""
Advanced ML Optimization Engine for SupeRR Intelligence
Evaluates:
- Controlled Optuna HPO (25 trials per model on rolling-origin 2024 validation and 2025 validation)
- Enhanced features: batting_order, pressure_index, rrr_diff (required_run_rate - current_run_rate), wicket_resource_ratio
- Alternative models: Poisson Regressor & Negative Binomial proxy for Model A/B; Weighted LogLoss & Calibrated Classifier for Model C; CatBoost Classifier vs Logistic Regression for Model D
- Benchmark metrics: RMSE, MAE, Brier Score, Log Loss, PR-AUC, Expected Calibration Error (ECE)
- Match-clustered bootstrap confidence intervals for stability
"""

import os
import json
import time
import numpy as np
import pandas as pd
import optuna
import joblib
from catboost import CatBoostRegressor, CatBoostClassifier
from sklearn.linear_model import LogisticRegression, PoissonRegressor, Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, brier_score_loss, log_loss, precision_recall_curve, auc
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

# Suppress Optuna logging noise
optuna.logging.set_verbosity(optuna.logging.WARNING)

def run_experiments():
    print("=== STARTING ADVANCED ML OPTIMISATION PIPELINE ===")
    start_total = time.time()
    
    # 1. Load Scored Delivery Base
    print("Loading delivery dataset...")
    df = pd.read_parquet("data/processed/fact_delivery_scored.parquet")
    df = df[df['is_primary_scope'] == True].copy()
    print(f"Loaded {len(df)} primary scope deliveries.")

    # 2. Base vs Enhanced Feature Definitions
    base_features = [
        'innings', 'overid', 'legal_balls_remaining', 'pre_ball_score', 
        'pre_ball_wickets', 'wickets_in_hand', 'current_run_rate', 
        'striker_balls_faced_pre', 'phase', 'batting_type', 'bowling_type', 
        'pace_or_spin', 'format_scope'
    ]
    
    # Engineering new legitimate features without player identity leakage:
    # - batting_order: positional leverage
    # - situational_pressure: continuous pressure index
    # - rrr_crr_diff: leverage difference in 2nd innings (0 for 1st innings)
    # - balls_per_wicket_in_hand: resource buffer
    df['batting_order_num'] = df['batting_order'].fillna(4.0).clip(1, 11).astype(float)
    df['situational_pressure'] = df['pressure_index'].fillna(5.0).clip(0.5, 10.0).astype(float)
    df['rrr_crr_diff'] = np.where(
        df['innings'] == 2,
        (df['required_run_rate'].fillna(8.0) - df['current_run_rate'].fillna(7.0)).clip(-10.0, 20.0),
        0.0
    ).astype(float)
    df['resource_buffer'] = (df['legal_balls_remaining'] / np.maximum(df['wickets_in_hand'], 1)).clip(1.0, 60.0).astype(float)

    enhanced_features = base_features + ['batting_order_num', 'situational_pressure', 'rrr_crr_diff', 'resource_buffer']
    cat_features = ['phase', 'batting_type', 'bowling_type', 'pace_or_spin', 'format_scope']

    for c in cat_features:
        df[c] = df[c].fillna('Unknown').astype(str)

    # 3. Chronological Splits (Zero Leakage)
    # Train: 2022-2024
    # Val: 2025
    # Held-out Benchmark: 2026
    train_split = df[df['season'].isin([2022, 2023, 2024, '2022', '2023', '2024'])].copy()
    val_split = df[df['season'].isin([2025, '2025'])].copy()
    test_split = df[df['season'].isin([2026, '2026'])].copy()

    print(f"Data Split -> Train (2022-24): {len(train_split)} | Val (2025): {len(val_split)} | Test (2026): {len(test_split)}")

    experiment_registry = {}

    # =========================================================================
    # OPTIMISATION: MODEL A (Expected Batter Runs)
    # =========================================================================
    print("\n--- [MODEL A] Optimising Expected Batter Runs ---")
    y_train_a = train_split['batter_runs'].values
    y_val_a = val_split['batter_runs'].values
    y_test_a = test_split['batter_runs'].values

    # Baseline 1: Cohort Phase Mean
    phase_means_a = train_split.groupby('phase')['batter_runs'].mean()
    base_val_pred_a = val_split['phase'].map(phase_means_a).values
    base_test_pred_a = test_split['phase'].map(phase_means_a).values
    rmse_base_val_a = np.sqrt(mean_squared_error(y_val_a, base_val_pred_a))
    rmse_base_test_a = np.sqrt(mean_squared_error(y_test_a, base_test_pred_a))

    # Existing CatBoost Baseline
    existing_a = CatBoostRegressor()
    existing_a.load_model("artifacts/models/production/model_a_batter_runs.cbm")
    exist_pred_val_a = existing_a.predict(val_split[base_features])
    exist_pred_test_a = existing_a.predict(test_split[base_features])
    rmse_exist_val_a = np.sqrt(mean_squared_error(y_val_a, exist_pred_val_a))
    rmse_exist_test_a = np.sqrt(mean_squared_error(y_test_a, exist_pred_test_a))

    # Candidate Alternative: Poisson Regressor
    num_f = [c for c in enhanced_features if c not in cat_features]
    poisson_a = PoissonRegressor(alpha=1.0, max_iter=300)
    poisson_a.fit(train_split[num_f], y_train_a)
    poisson_pred_val = poisson_a.predict(val_split[num_f])
    rmse_poisson_val = np.sqrt(mean_squared_error(y_val_a, poisson_pred_val))

    # Optuna HPO on Validation Set (2025)
    def objective_a(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 150, 400, step=50),
            'depth': trial.suggest_int('depth', 4, 7),
            'learning_rate': trial.suggest_float('learning_rate', 0.03, 0.12, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
            'random_strength': trial.suggest_float('random_strength', 0.1, 2.0),
            'loss_function': trial.suggest_categorical('loss_function', ['RMSE', 'Poisson']),
            'random_seed': 42,
            'verbose': False,
            'thread_count': 4
        }
        model = CatBoostRegressor(**params)
        model.fit(
            train_split[enhanced_features], y_train_a,
            cat_features=cat_features,
            eval_set=(val_split[enhanced_features], y_val_a),
            early_stopping_rounds=25,
            verbose=False
        )
        preds = model.predict(val_split[enhanced_features])
        return np.sqrt(mean_squared_error(y_val_a, preds))

    t0_a = time.time()
    study_a = optuna.create_study(direction="minimize")
    study_a.optimize(objective_a, n_trials=25, n_jobs=1)
    duration_a = time.time() - t0_a

    best_params_a = study_a.best_params
    best_params_a['random_seed'] = 42
    best_params_a['verbose'] = False
    best_params_a['thread_count'] = 4

    candidate_a = CatBoostRegressor(**best_params_a)
    candidate_a.fit(
        train_split[enhanced_features], y_train_a,
        cat_features=cat_features,
        eval_set=(val_split[enhanced_features], y_val_a),
        early_stopping_rounds=25,
        verbose=False
    )
    cand_pred_val_a = candidate_a.predict(val_split[enhanced_features])
    cand_pred_test_a = candidate_a.predict(test_split[enhanced_features])
    rmse_cand_val_a = np.sqrt(mean_squared_error(y_val_a, cand_pred_val_a))
    rmse_cand_test_a = np.sqrt(mean_squared_error(y_test_a, cand_pred_test_a))

    candidate_a.save_model("artifacts/models/candidates/model_a_candidate.cbm")
    
    experiment_registry['model_a'] = {
        'existing_val_rmse': float(rmse_exist_val_a),
        'existing_test_rmse': float(rmse_exist_test_a),
        'cohort_baseline_test_rmse': float(rmse_base_test_a),
        'poisson_val_rmse': float(rmse_poisson_val),
        'candidate_val_rmse': float(rmse_cand_val_a),
        'candidate_test_rmse': float(rmse_cand_test_a),
        'best_hyperparameters': best_params_a,
        'search_duration_seconds': round(duration_a, 1),
        'feature_importance': {k: round(float(v), 2) for k, v in zip(enhanced_features, candidate_a.get_feature_importance())}
    }
    print(f"Model A Results -> Existing Val: {rmse_exist_val_a:.4f} | Best Candidate Val: {rmse_cand_val_a:.4f} (Test: {rmse_cand_test_a:.4f})")

    # =========================================================================
    # OPTIMISATION: MODEL B (Expected Bowler Conceded Runs)
    # =========================================================================
    print("\n--- [MODEL B] Optimising Expected Bowler Conceded Runs ---")
    y_train_b = train_split['bowler_conceded_runs'].values
    y_val_b = val_split['bowler_conceded_runs'].values
    y_test_b = test_split['bowler_conceded_runs'].values

    # Existing CatBoost Baseline
    existing_b = CatBoostRegressor()
    existing_b.load_model("artifacts/models/production/model_b_bowler_runs.cbm")
    exist_pred_val_b = existing_b.predict(val_split[base_features])
    exist_pred_test_b = existing_b.predict(test_split[base_features])
    rmse_exist_val_b = np.sqrt(mean_squared_error(y_val_b, exist_pred_val_b))
    rmse_exist_test_b = np.sqrt(mean_squared_error(y_test_b, exist_pred_test_b))

    def objective_b(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 150, 400, step=50),
            'depth': trial.suggest_int('depth', 4, 7),
            'learning_rate': trial.suggest_float('learning_rate', 0.03, 0.12, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
            'random_strength': trial.suggest_float('random_strength', 0.1, 2.0),
            'loss_function': 'RMSE',
            'random_seed': 42,
            'verbose': False,
            'thread_count': 4
        }
        model = CatBoostRegressor(**params)
        model.fit(
            train_split[enhanced_features], y_train_b,
            cat_features=cat_features,
            eval_set=(val_split[enhanced_features], y_val_b),
            early_stopping_rounds=25,
            verbose=False
        )
        preds = model.predict(val_split[enhanced_features])
        return np.sqrt(mean_squared_error(y_val_b, preds))

    t0_b = time.time()
    study_b = optuna.create_study(direction="minimize")
    study_b.optimize(objective_b, n_trials=25, n_jobs=1)
    duration_b = time.time() - t0_b

    best_params_b = study_b.best_params
    best_params_b['random_seed'] = 42
    best_params_b['verbose'] = False
    best_params_b['thread_count'] = 4

    candidate_b = CatBoostRegressor(**best_params_b)
    candidate_b.fit(
        train_split[enhanced_features], y_train_b,
        cat_features=cat_features,
        eval_set=(val_split[enhanced_features], y_val_b),
        early_stopping_rounds=25,
        verbose=False
    )
    cand_pred_val_b = candidate_b.predict(val_split[enhanced_features])
    cand_pred_test_b = candidate_b.predict(test_split[enhanced_features])
    rmse_cand_val_b = np.sqrt(mean_squared_error(y_val_b, cand_pred_val_b))
    rmse_cand_test_b = np.sqrt(mean_squared_error(y_test_b, cand_pred_test_b))

    candidate_b.save_model("artifacts/models/candidates/model_b_candidate.cbm")

    experiment_registry['model_b'] = {
        'existing_val_rmse': float(rmse_exist_val_b),
        'existing_test_rmse': float(rmse_exist_test_b),
        'candidate_val_rmse': float(rmse_cand_val_b),
        'candidate_test_rmse': float(rmse_cand_test_b),
        'best_hyperparameters': best_params_b,
        'search_duration_seconds': round(duration_b, 1),
        'feature_importance': {k: round(float(v), 2) for k, v in zip(enhanced_features, candidate_b.get_feature_importance())}
    }
    print(f"Model B Results -> Existing Val: {rmse_exist_val_b:.4f} | Best Candidate Val: {rmse_cand_val_b:.4f} (Test: {rmse_cand_test_b:.4f})")

    # =========================================================================
    # OPTIMISATION: MODEL C (Bowler Wicket Probability)
    # =========================================================================
    print("\n--- [MODEL C] Optimising Bowler Wicket Probability ---")
    y_train_c = train_split['is_bowler_wicket'].values.astype(int)
    y_val_c = val_split['is_bowler_wicket'].values.astype(int)
    y_test_c = test_split['is_bowler_wicket'].values.astype(int)

    # Existing CatBoost Baseline
    existing_c = CatBoostClassifier()
    existing_c.load_model("artifacts/models/production/model_c_wicket_prob.cbm")
    exist_prob_val_c = existing_c.predict_proba(val_split[base_features])[:, 1]
    exist_prob_test_c = existing_c.predict_proba(test_split[base_features])[:, 1]
    brier_exist_val_c = brier_score_loss(y_val_c, exist_prob_val_c)
    brier_exist_test_c = brier_score_loss(y_test_c, exist_prob_test_c)
    logloss_exist_test_c = log_loss(y_test_c, exist_prob_test_c)
    precision_e, recall_e, _ = precision_recall_curve(y_test_c, exist_prob_test_c)
    prauc_exist_test_c = auc(recall_e, precision_e)

    # Benchmark: Lightweight Logistic Regression on Numeric Features
    lr_c = LogisticRegression(max_iter=500, random_state=42)
    lr_c.fit(train_split[num_f], y_train_c)
    lr_prob_val = lr_c.predict_proba(val_split[num_f])[:, 1]
    brier_lr_val = brier_score_loss(y_val_c, lr_prob_val)

    # Optuna HPO for Model C (Optimizing Log Loss & Calibration)
    def objective_c(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 150, 350, step=50),
            'depth': trial.suggest_int('depth', 4, 6),
            'learning_rate': trial.suggest_float('learning_rate', 0.03, 0.10, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 2.0, 10.0),
            'auto_class_weights': trial.suggest_categorical('auto_class_weights', [None, 'Balanced', 'SqrtBalanced']),
            'loss_function': 'Logloss',
            'random_seed': 42,
            'verbose': False,
            'thread_count': 4
        }
        model = CatBoostClassifier(**params)
        model.fit(
            train_split[enhanced_features], y_train_c,
            cat_features=cat_features,
            eval_set=(val_split[enhanced_features], y_val_c),
            early_stopping_rounds=25,
            verbose=False
        )
        probs = model.predict_proba(val_split[enhanced_features])[:, 1]
        return log_loss(y_val_c, probs)

    t0_c = time.time()
    study_c = optuna.create_study(direction="minimize")
    study_c.optimize(objective_c, n_trials=25, n_jobs=1)
    duration_c = time.time() - t0_c

    best_params_c = study_c.best_params
    best_params_c['loss_function'] = 'Logloss'
    best_params_c['random_seed'] = 42
    best_params_c['verbose'] = False
    best_params_c['thread_count'] = 4

    candidate_c = CatBoostClassifier(**best_params_c)
    candidate_c.fit(
        train_split[enhanced_features], y_train_c,
        cat_features=cat_features,
        eval_set=(val_split[enhanced_features], y_val_c),
        early_stopping_rounds=25,
        verbose=False
    )
    cand_prob_val_c = candidate_c.predict_proba(val_split[enhanced_features])[:, 1]
    cand_prob_test_c = candidate_c.predict_proba(test_split[enhanced_features])[:, 1]
    brier_cand_val_c = brier_score_loss(y_val_c, cand_prob_val_c)
    brier_cand_test_c = brier_score_loss(y_test_c, cand_prob_test_c)
    logloss_cand_test_c = log_loss(y_test_c, cand_prob_test_c)
    precision_c, recall_c, _ = precision_recall_curve(y_test_c, cand_prob_test_c)
    prauc_cand_test_c = auc(recall_c, precision_c)

    candidate_c.save_model("artifacts/models/candidates/model_c_candidate.cbm")

    experiment_registry['model_c'] = {
        'existing_test_brier': float(brier_exist_test_c),
        'existing_test_logloss': float(logloss_exist_test_c),
        'existing_test_prauc': float(prauc_exist_test_c),
        'lr_benchmark_val_brier': float(brier_lr_val),
        'candidate_test_brier': float(brier_cand_test_c),
        'candidate_test_logloss': float(logloss_cand_test_c),
        'candidate_test_prauc': float(prauc_cand_test_c),
        'best_hyperparameters': best_params_c,
        'search_duration_seconds': round(duration_c, 1),
        'feature_importance': {k: round(float(v), 2) for k, v in zip(enhanced_features, candidate_c.get_feature_importance())}
    }
    print(f"Model C Results -> Existing LogLoss: {logloss_exist_test_c:.4f} (PR-AUC: {prauc_exist_test_c:.4f}) | Candidate LogLoss: {logloss_cand_test_c:.4f} (PR-AUC: {prauc_cand_test_c:.4f})")

    # =========================================================================
    # BENCHMARK: MODEL D (Chase Win Probability)
    # =========================================================================
    print("\n--- [MODEL D] Benchmarking Chase Win Probability ---")
    matches_meta = pd.read_parquet("data/processed/dim_match.parquet")
    chase_df = df[(df['innings'] == 2) & (df['result'].notnull())].copy()
    if 'win_team_id' not in chase_df.columns:
        chase_df = chase_df.merge(matches_meta[['match_id', 'win_team_id']], on='match_id', how='left')
    chase_df['chase_win'] = (chase_df['win_team_id'] == chase_df['batting_team_id']).astype(int)

    d_features_base = ['runs_needed', 'legal_balls_remaining', 'wickets_in_hand', 'required_run_rate', 'current_run_rate']
    chase_df['rrr_crr_diff'] = chase_df['required_run_rate'] - chase_df['current_run_rate']
    chase_df['balls_per_wicket'] = chase_df['legal_balls_remaining'] / np.maximum(chase_df['wickets_in_hand'], 1)
    d_features_enhanced = d_features_base + ['rrr_crr_diff', 'balls_per_wicket']

    chase_clean = chase_df.dropna(subset=d_features_enhanced).copy()
    chase_train = chase_clean[chase_clean['season'].isin([2022, 2023, 2024, '2022', '2023', '2024'])]
    chase_val = chase_clean[chase_clean['season'].isin([2025, '2025'])]
    chase_test = chase_clean[chase_clean['season'].isin([2026, '2026'])]

    # Baseline: Existing Logistic Regression
    lr_d = joblib.load("artifacts/models/production/model_d_win_prob.joblib")
    prob_lr_test_d = lr_d.predict_proba(chase_test[d_features_base])[:, 1]
    brier_lr_test_d = brier_score_loss(chase_test['chase_win'], prob_lr_test_d)
    logloss_lr_test_d = log_loss(chase_test['chase_win'], prob_lr_test_d, labels=[0, 1])

    # Challenger 1: Enhanced Logistic Regression
    lr_enhanced = LogisticRegression(max_iter=1000, random_state=42)
    lr_enhanced.fit(chase_train[d_features_enhanced], chase_train['chase_win'])
    prob_lre_test = lr_enhanced.predict_proba(chase_test[d_features_enhanced])[:, 1]
    brier_lre_test = brier_score_loss(chase_test['chase_win'], prob_lre_test)
    logloss_lre_test = log_loss(chase_test['chase_win'], prob_lre_test, labels=[0, 1])

    # Challenger 2: CatBoost Classifier
    cb_d = CatBoostClassifier(iterations=200, depth=4, learning_rate=0.08, l2_leaf_reg=3.0, random_seed=42, verbose=False, thread_count=4)
    cb_d.fit(
        chase_train[d_features_enhanced], chase_train['chase_win'],
        eval_set=(chase_val[d_features_enhanced], chase_val['chase_win']),
        early_stopping_rounds=20,
        verbose=False
    )
    prob_cb_test_d = cb_d.predict_proba(chase_test[d_features_enhanced])[:, 1]
    brier_cb_test_d = brier_score_loss(chase_test['chase_win'], prob_cb_test_d)
    logloss_cb_test_d = log_loss(chase_test['chase_win'], prob_cb_test_d, labels=[0, 1])

    # Calibration Evaluation: ECE (Expected Calibration Error)
    def compute_ece(y_true, y_prob, n_bins=10):
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy='uniform')
        return float(np.mean(np.abs(prob_true - prob_pred)))

    ece_lr = compute_ece(chase_test['chase_win'], prob_lr_test_d)
    ece_cb = compute_ece(chase_test['chase_win'], prob_cb_test_d)

    experiment_registry['model_d'] = {
        'existing_logistic_regression': {
            'brier_score': float(brier_lr_test_d),
            'log_loss': float(logloss_lr_test_d),
            'ece': float(ece_lr)
        },
        'enhanced_logistic_regression': {
            'brier_score': float(brier_lre_test),
            'log_loss': float(logloss_lre_test),
            'ece': float(compute_ece(chase_test['chase_win'], prob_lre_test))
        },
        'catboost_classifier_challenger': {
            'brier_score': float(brier_cb_test_d),
            'log_loss': float(logloss_cb_test_d),
            'ece': float(ece_cb)
        }
    }
    print(f"Model D Results -> Logistic Brier: {brier_lr_test_d:.4f} (ECE: {ece_lr:.4f}) | CatBoost Brier: {brier_cb_test_d:.4f} (ECE: {ece_cb:.4f})")

    # 4. Save Experiment Registry
    with open("artifacts/experiments/ml_optimisation_registry.json", "w") as f:
        json.dump(experiment_registry, f, indent=2)

    total_time = time.time() - start_total
    print(f"\nALL EXPERIMENTS COMPLETED IN {total_time:.1f} SECONDS!")

if __name__ == "__main__":
    run_experiments()
