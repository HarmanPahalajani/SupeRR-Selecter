import pandas as pd

df = pd.read_parquet('data/processed/fact_delivery_scored.parquet')
wides = df[df['extras_wide_runs'] > 0]
print(f'Total wide deliveries in fact_delivery_scored: {len(wides)}')
print(f'Wides where expected_batter_runs > 0: {(wides["expected_batter_runs"] > 0).sum()}')
print(f'Wides where rae != 0: {(wides["rae"] != 0).sum()}')
print('Sample wide rows in fact_delivery_scored:')
cols = ['match_id', 'innings', 'overid', 'over_ball_num', 'striker_name', 'batter_runs', 'extras_wide_runs', 'is_legal_ball', 'expected_batter_runs', 'rae']
print(wides[cols].head(5).to_string(index=False))

# Check high pressure wides
hp_cond = ((df["innings"] == 1) & (df["pressure_index"] >= 5.83)) | ((df["innings"] == 2) & (df["pressure_index"] >= 8.60))
hp_wides = df[hp_cond & (df['extras_wide_runs'] > 0)]
print(f'\nTotal high-pressure wides: {len(hp_wides)}')
print(f'High-pressure wides where rae != 0: {(hp_wides["rae"] != 0).sum()}')
print(f'High-pressure wides where expected_batter_runs > 0: {(hp_wides["expected_batter_runs"] > 0).sum()}')
print('Sample HP wide rows:')
print(hp_wides[cols].head(5).to_string(index=False))
