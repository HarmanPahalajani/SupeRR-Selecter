import pandas as pd

df = pd.read_parquet('data/processed/fact_delivery_scored.parquet')

print("Delivery counts by extras and is_legal_ball:")
for wide_cond in [True, False]:
    for nb_cond in [True, False]:
        for bye_cond in [True, False]:
            sub = df[(df['extras_wide_runs'] > 0) == wide_cond]
            sub = sub[(sub['extras_noball_runs'] > 0) == nb_cond]
            sub = sub[(sub['extras_bye_legbye_runs'] > 0) == bye_cond]
            if len(sub) > 0:
                print(f"Wide={wide_cond}, NoBall={nb_cond}, Bye/LegBye={bye_cond}: Count={len(sub)}, is_legal_ball values={sub['is_legal_ball'].unique().tolist()}")
