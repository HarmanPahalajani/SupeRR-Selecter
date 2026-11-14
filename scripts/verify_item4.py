import pandas as pd
import numpy as np

def verify_item4():
    df = pd.read_parquet("data/processed/fact_delivery_scored.parquet")
    
    # Filter to high pressure deliveries with extras
    # Innings 1 >= 5.83 or Innings 2 >= 8.60
    hp_cond = ((df["innings"] == 1) & (df["pressure_index"] >= 5.83)) | ((df["innings"] == 2) & (df["pressure_index"] >= 8.60))
    extras_cond = (df["extras_wide_runs"] > 0) | (df["extras_noball_runs"] > 0) | (df["extras_bye_legbye_runs"] > 0)
    
    sample = df[hp_cond & extras_cond].head(10)
    
    print("=" * 80)
    print("ITEM 4: DELIVERY-LEVEL BATTING RAE AUDIT (EXTRAS vs BATTER RUNS)")
    print("=" * 80)
    
    records = []
    for i, (_, r) in enumerate(sample.iterrows()):
        diff = abs(r["rae"] - (r["batter_runs"] - r["expected_batter_runs"]))
        is_exact = diff < 1e-6
        rec = {
            "Match ID": r["match_id"],
            "Innings": r["innings"],
            "Over.Ball": f"{r['overid']}.{r['over_ball_num']}",
            "Striker": r["striker_name"],
            "Batter Runs": int(r["batter_runs"]),
            "Wide Runs": int(r["extras_wide_runs"]),
            "NoBall Runs": int(r["extras_noball_runs"]),
            "Bye/LegBye Runs": int(r["extras_bye_legbye_runs"]),
            "Total Delivery Runs": int(r["total_delivery_runs"]),
            "Expected Batter Runs": round(float(r["expected_batter_runs"]), 4),
            "Expected Bowler Conceded": round(float(r["expected_bowler_conceded_runs"]), 4),
            "Batting RAE": round(float(r["rae"]), 4),
            "Formula Validated": is_exact,
            "Pressure Index": round(float(r["pressure_index"]), 2)
        }
        records.append(rec)
        
    df_rec = pd.DataFrame(records)
    print(df_rec.to_string(index=False))
    
    # Statistical check across ALL high pressure deliveries
    hp_all = df[hp_cond].copy()
    hp_all["expected_diff"] = (hp_all["batter_runs"] - hp_all["expected_batter_runs"]) - hp_all["rae"]
    max_err = hp_all["expected_diff"].abs().max()
    print(f"\nAcross all {len(hp_all)} high-pressure deliveries:")
    print(f"Maximum absolute discrepancy between (batter_runs - expected_batter_runs) and rae: {max_err:.2e}")
    
    # Check that extras are NEVER included in batter_runs
    extras_in_batter_runs = hp_all[(hp_all["batter_runs"] > 0) & (hp_all["extras_bye_legbye_runs"] > 0) & (hp_all["runs"] == hp_all["extras_bye_legbye_runs"])]
    print(f"Deliveries where bye/legbye was mistakenly counted in batter_runs: {len(extras_in_batter_runs)} (Must be 0)")
    
    # Check wides excluded from legal balls
    wides = hp_all[hp_all["extras_wide_runs"] > 0]
    legal_wides = wides[wides["is_legal_ball"] == True]
    print(f"High-pressure wides mistakenly marked as legal ball faced: {len(legal_wides)} (Must be 0)")

if __name__ == "__main__":
    verify_item4()
