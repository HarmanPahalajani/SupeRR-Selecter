import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import joblib
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression

class WinProbabilityService:
    """
    Production Win Probability Service:
    - Primary Model: Promoted CatBoost Classifier (Model D Challenger)
    - Fallback / Benchmark Model: Calibrated Baseline Logistic Regression
    """
    _cb_model: Optional[CatBoostClassifier] = None
    _lr_model: Optional[LogisticRegression] = None
    _meta: Optional[Dict[str, Any]] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, models_dir: str = "artifacts/models/production"):
        m_path = Path(models_dir)
        cb_path = m_path / "model_d_win_prob.cbm"
        lr_path = m_path / "model_d_win_prob.joblib"
        meta_path = m_path / "model_d_win_prob_meta.json"

        if cb_path.exists():
            cls._cb_model = CatBoostClassifier()
            cls._cb_model.load_model(str(cb_path))

        if lr_path.exists():
            cls._lr_model = joblib.load(str(lr_path))

        if meta_path.exists():
            with open(meta_path) as f:
                cls._meta = json.load(f)

        cls._initialized = True

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        if not cls._initialized:
            cls.initialize()
        return {
            "service": "Chase Win Probability Service",
            "active_primary_model": "CatBoost Classifier (Promoted Candidate)",
            "primary_model_loaded": cls._cb_model is not None,
            "fallback_benchmark_model": "Logistic Regression (Calibrated Benchmark)",
            "fallback_model_loaded": cls._lr_model is not None,
            "primary_features": ['runs_needed', 'legal_balls_remaining', 'wickets_in_hand', 'required_run_rate', 'current_run_rate', 'rrr_crr_diff', 'balls_per_wicket'],
            "benchmark_features": ['runs_needed', 'legal_balls_remaining', 'wickets_in_hand', 'required_run_rate', 'current_run_rate'],
            "metrics_comparison": {
                "catboost_primary": {"brier_score": 0.1356, "log_loss": 0.4112, "ece": 0.0925},
                "logistic_regression_benchmark": {"brier_score": 0.1386, "log_loss": 0.4225, "ece": 0.1131}
            }
        }

    @classmethod
    def predict_chase_win_prob(
        cls,
        runs_needed: float,
        legal_balls_remaining: float,
        wickets_in_hand: float,
        required_run_rate: float,
        current_run_rate: float,
        model_type: str = "catboost"
    ) -> Dict[str, Any]:
        if not cls._initialized:
            cls.initialize()

        rrr_crr_diff = float(required_run_rate - current_run_rate)
        balls_per_wicket = float(legal_balls_remaining / max(wickets_in_hand, 1))

        if model_type == "catboost" and cls._cb_model is not None:
            features = pd.DataFrame([{
                'runs_needed': runs_needed,
                'legal_balls_remaining': legal_balls_remaining,
                'wickets_in_hand': wickets_in_hand,
                'required_run_rate': required_run_rate,
                'current_run_rate': current_run_rate,
                'rrr_crr_diff': rrr_crr_diff,
                'balls_per_wicket': balls_per_wicket
            }])
            prob = float(cls._cb_model.predict_proba(features)[0, 1])
            model_used = "CatBoostClassifier (Promoted Model D)"
        elif cls._lr_model is not None:
            features = pd.DataFrame([{
                'runs_needed': runs_needed,
                'legal_balls_remaining': legal_balls_remaining,
                'wickets_in_hand': wickets_in_hand,
                'required_run_rate': required_run_rate,
                'current_run_rate': current_run_rate
            }])
            prob = float(cls._lr_model.predict_proba(features)[0, 1])
            model_used = "LogisticRegression (Benchmark Model D)"
        else:
            raise RuntimeError("No win probability model loaded.")

        return {
            "chase_win_probability": round(prob, 4),
            "model_used": model_used,
            "inputs": {
                "runs_needed": runs_needed,
                "legal_balls_remaining": legal_balls_remaining,
                "wickets_in_hand": wickets_in_hand,
                "required_run_rate": required_run_rate,
                "current_run_rate": current_run_rate
            }
        }
