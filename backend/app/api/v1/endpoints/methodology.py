import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/methodology", tags=["Methodology & Validation"])

@router.get("")
def get_methodology_summary():
    return {
        "title": "SupeRR Intelligence Analytics & Machine Learning Methodology",
        "version": "1.0.0",
        "pillars": [
            {
                "name": "Pressure Intensity P(t)",
                "formula": "P(t) = 10 / [1 + (10/P(1) - 1) * exp(-10 * k * sum(delta_C * delta_R))]",
                "reference": "Mallawa Arachchi, Manage & Scariano (2024)",
                "description": "Dynamic logistic chase pressure bounded strictly in [0, 10] computed prior to delivery."
            },
            {
                "name": "Runs Above Expected (RAE)",
                "formula": "RAE(t) = Actual_Runs(t) - E[Runs(t) | Pre-Delivery State]",
                "reference": "CatBoost Tabular Gradient Boosted Regression",
                "description": "Context-adjusted delivery residual evaluated against neutral baseline."
            },
            {
                "name": "Empirical Bayes Shrinkage & Uncertainty",
                "formula": "theta_i = (1 - B_i) * ybar_i + B_i * mu_0,  SE_i = sqrt(1 / (1/tau^2 + 1/sigma_i^2))",
                "reference": "Normal-Normal Bayesian Hierarchical Formulation",
                "description": "Independently shrinks small-sample noisy batting and bowling estimates toward discipline priors."
            },
            {
                "name": "Evidence-Based Discipline Ranking (LCB)",
                "formula": "Score_i = theta_i - 0.5 * SE_i  (Eligible only if Sample >= Threshold)",
                "reference": "Conservative Lower Confidence Bound Architecture",
                "description": "Requires verified sample size (High: 180+ balls / 12+ matches; Med: 60+ balls / 5+ matches). Ineligible players receive N/A and are excluded from official rankings."
            },
            {
                "name": "Discovery Gap (Undervalued Talent)",
                "formula": "DiscoveryGap = Percentile(Adjusted Impact) - Percentile(Conventional Avg*SR)",
                "reference": "SupeRR Intelligence Value Signal",
                "description": "Identifies players whose context-adjusted value significantly exceeds raw superficial statistics."
            }
        ]
    }

@router.get("/validation")
def get_validation_report():
    eval_file = Path("artifacts/metrics/model_evaluation.json")
    if eval_file.exists():
        with open(eval_file) as f:
            eval_data = json.load(f)
    else:
        eval_data = {}

    audit_file = Path("artifacts/reports/scoring_semantics_audit.json")
    if audit_file.exists():
        with open(audit_file) as f:
            audit_data = json.load(f)
    else:
        audit_data = {}

    return {
        "model_evaluations": eval_data,
        "scoring_audit": audit_data,
        "validation_protocol": {
            "temporal_split": "Train: 2022-2024 | Val: 2025 | Test: 2026",
            "grouping": "Strictly grouped by match_id to eliminate data leakage",
            "lookahead_bias": "Zero future information. Only pre-delivery state features permitted."
        }
    }
