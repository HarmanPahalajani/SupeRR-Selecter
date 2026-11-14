import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
import duckdb
from backend.analytics.pressure_performers.validation import run_comprehensive_validation

con = duckdb.connect()
df_del = con.execute("""
    SELECT * FROM read_parquet('data/processed/fact_delivery_scored.parquet')
    WHERE is_primary_scope = true
""").df()

print("Running comprehensive validation...")
results = run_comprehensive_validation(df_del)

v2025 = results["validation_fold_2025"]["all_primary"]
print("\nValidation Fold (Train <= 2024 -> Test 2025):")
print(f"Evaluated players: {v2025['evaluated_players']}")
print(f"Spearman CRAI (LCB): {v2025['spearman_lcb']['rho']:.4f} (95% CI: {v2025['spearman_lcb']['ci_95']})")
print(f"Spearman Baseline (Career SR): {v2025['spearman_baseline_career_sr']['rho']:.4f}")
print(f"Baseline Positive Prevalence: {v2025['baseline_positive_prevalence']*100:.1f}%")
print(f"Precision@10: {v2025['precision_at_10']*100:.1f}%, Lift@10: {v2025['lift_at_10']:.2f}x")
print(f"Precision@20: {v2025['precision_at_20']*100:.1f}%, Lift@20: {v2025['lift_at_20']:.2f}x")

with open("artifacts/reports/pressure_performer_validation_metrics.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("\nSaved metrics to artifacts/reports/pressure_performer_validation_metrics.json")
