import pandas as pd
import numpy as np

def run_test():
    df = pd.read_parquet('data/processed/fact_player_metrics.parquet')

    # Batting Eligibility: at least 60 balls faced, 5 matches batted, 15 pressure balls faced
    bat_qual = (df['balls_faced'] >= 60) & (df['matches_batted'] >= 5) & (df['pressure_balls_faced'] >= 15)
    mu_bat = df.loc[bat_qual, 'pressure_rae_per_ball'].mean()
    tau2_bat = max(0.01, df.loc[bat_qual, 'pressure_rae_per_ball'].var())

    v_bat = 1.2
    n_bat = np.maximum(df['pressure_balls_faced'].values, 1)
    sigma2_bat = v_bat / n_bat
    b_bat = sigma2_bat / (tau2_bat + sigma2_bat)
    shrunk_bat = (1.0 - b_bat) * df['pressure_rae_per_ball'].values + b_bat * mu_bat
    unc_bat = np.sqrt(1.0 / (1.0/tau2_bat + 1.0/sigma2_bat))

    lcb_bat = shrunk_bat - 0.5 * unc_bat
    bat_rating = np.where(bat_qual, np.clip(50.0 + shrunk_bat * 35.0, 15.0, 99.0), np.nan)

    # Bowling Eligibility: at least 60 legal balls bowled (10 overs), 5 matches bowled, 15 pressure balls bowled
    bowl_qual = (df['legal_balls_bowled'] >= 60) & (df['matches_bowled'] >= 5) & (df['pressure_balls_bowled'] >= 15)
    mu_bowl = df.loc[bowl_qual, 'pressure_runs_saved_per_ball'].mean()
    tau2_bowl = max(0.01, df.loc[bowl_qual, 'pressure_runs_saved_per_ball'].var())

    v_bowl = 1.0
    n_bowl = np.maximum(df['pressure_balls_bowled'].values, 1)
    sigma2_bowl = v_bowl / n_bowl
    b_bowl = sigma2_bowl / (tau2_bowl + sigma2_bowl)
    shrunk_bowl = (1.0 - b_bowl) * df['pressure_runs_saved_per_ball'].values + b_bowl * mu_bowl
    unc_bowl = np.sqrt(1.0 / (1.0/tau2_bowl + 1.0/sigma2_bowl))

    wkts_per_match = df['bowler_wickets'].values / np.maximum(1, df['matches_bowled'].values)
    lcb_bowl = shrunk_bowl - 0.5 * unc_bowl + 0.1 * np.minimum(2.0, wkts_per_match)
    bowl_rating = np.where(bowl_qual, np.clip(50.0 + shrunk_bowl * 40.0 + 5.0 * np.minimum(2.0, wkts_per_match), 15.0, 99.0), np.nan)

    df['bat_rating'] = bat_rating
    df['lcb_bat'] = lcb_bat
    df['bowl_rating'] = bowl_rating
    df['lcb_bowl'] = lcb_bowl
    df['bat_qual'] = bat_qual
    df['bowl_qual'] = bowl_qual

    print("=== TOP 20 OFFICIALLY RANKED BATTERS ===")
    top_bat = df[df['bat_qual']].sort_values(by='lcb_bat', ascending=False).head(20)
    for idx, (_, r) in enumerate(top_bat.iterrows(), 1):
        pname = r['player_name']
        prole = r['primary_role']
        br = r['bat_rating']
        lcb = r['lcb_bat']
        bf = r['balls_faced']
        pbf = r['pressure_balls_faced']
        print(f"#{idx:2d} {pname:25} | {prole:12} | Rating: {br:5.1f} | LCB: {lcb:+.3f} | BF: {bf:4.0f} | pBF: {pbf:3.0f}")

    print("\n=== TOP 20 OFFICIALLY RANKED BOWLERS ===")
    top_bowl = df[df['bowl_qual']].sort_values(by='lcb_bowl', ascending=False).head(20)
    for idx, (_, r) in enumerate(top_bowl.iterrows(), 1):
        pname = r['player_name']
        prole = r['primary_role']
        bor = r['bowl_rating']
        lcb = r['lcb_bowl']
        bb = r['legal_balls_bowled']
        pbb = r['pressure_balls_bowled']
        print(f"#{idx:2d} {pname:25} | {prole:12} | Rating: {bor:5.1f} | LCB: {lcb:+.3f} | BB: {bb:4.0f} | pBB: {pbb:3.0f}")

if __name__ == '__main__':
    run_test()
