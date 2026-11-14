import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from backend.analytics.pressure.engine import DynamicPressureEngine

df = pd.read_parquet('data/processed/fact_delivery_states.parquet')
matches = pd.read_parquet('data/processed/dim_match.parquet')
df = df.merge(matches[['match_id', 'venue_id']], on='match_id', how='left')
inn1 = df[(df['innings'] == 1) & (df['is_primary_scope'] == True)].copy()

engine = DynamicPressureEngine()
engine.load_data()
engine.train_expected_score_model(df)
feat_df = engine.attach_features(inn1)
exp_scores = engine.cb_model.predict(feat_df[engine.feature_cols])
venue_par = feat_df['venue_par_score'].values
shortfall = (venue_par - exp_scores) / max(engine.par_std, 25.0)

# Pure Shortfall Model:
# Calibrate so shortfall of +2.0 (e.g. 75 runs below par) maps to 8.8, and -2.0 (75 runs above par) maps to 1.2
p_pure = 10.0 / (1.0 + np.exp(-1.05 * shortfall))
print(f"Ball 1: Venue Par={venue_par[0]:.1f}, Exp={exp_scores[0]:.1f}, Shortfall={shortfall[0]:.3f}, P_pure={p_pure[0]:.2f}")

print("\n--- Match 13511 (Collapse, Final 103) ---")
m1_idx = inn1[inn1['match_id'] == 13511].index
for b in [0, 20, 40, 60, 80, 100, 120]:
    if b < len(m1_idx):
        idx = m1_idx[b]
        r = inn1.loc[idx]
        loc = inn1.index.get_loc(idx)
        print(f"Over {int(r['overid']):2d} | Score: {int(r['pre_ball_score']):3d}/{int(r['pre_ball_wickets'])} | Exp: {exp_scores[loc]:5.1f} | Shortfall: {shortfall[loc]:5.2f} | P_pure: {p_pure[loc]:4.2f}")

print("\n--- Match 13513 (Flourish, Final 223) ---")
m2_idx = inn1[inn1['match_id'] == 13513].index
for b in [0, 20, 40, 60, 80, 100, 120]:
    if b < len(m2_idx):
        idx = m2_idx[b]
        r = inn1.loc[idx]
        loc = inn1.index.get_loc(idx)
        print(f"Over {int(r['overid']):2d} | Score: {int(r['pre_ball_score']):3d}/{int(r['pre_ball_wickets'])} | Exp: {exp_scores[loc]:5.1f} | Shortfall: {shortfall[loc]:5.2f} | P_pure: {p_pure[loc]:4.2f}")
