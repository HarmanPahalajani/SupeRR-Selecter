"""
Wicket Valuation and State-Transition Analysis Module
Part of SupeRR Intelligence — Bowling Under Pressure Intelligence

Estimates the marginal expected future-run value of capturing a wicket from the match state,
investigating whether a combined run-equivalent composite can be statistically defended.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


class EmpiricalWicketValuationModel:
    def __init__(self):
        # State value lookup table: (over_bucket, wickets_in_hand) -> mean remaining runs
        self.state_values: Dict[Tuple[int, int], float] = {}
        self.marginal_wicket_values: Dict[Tuple[int, int], float] = {}
        self.mean_marginal_wicket_value: float = 7.96

    def fit_from_deliveries(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Estimates the empirical expected remaining innings runs as a function of
        balls remaining bucket and wickets in hand across historical 1st innings data.
        """
        inn1 = df[df["innings"] == 1].copy()
        if inn1.empty:
            return {"mean_wicket_value": 7.96, "status": "DEFAULT"}

        # Calculate actual remaining runs from pre-ball state to innings end
        if "inn1_total_runs" in inn1.columns:
            inn1["runs_remaining"] = inn1["inn1_total_runs"] - inn1["pre_ball_score"]
        else:
            match_totals = inn1.groupby("match_id")["total_delivery_runs"].sum().rename("match_total")
            inn1 = inn1.merge(match_totals, on="match_id")
            inn1["runs_remaining"] = inn1["match_total"] - inn1["pre_ball_score"]

        # 2-over buckets (0..9)
        inn1["over_bucket"] = (inn1["pre_ball_legal_balls"] // 12).clip(0, 9).astype(int)
        inn1["w_hand"] = inn1["wickets_in_hand"].clip(1, 10).astype(int)

        grid = inn1.groupby(["over_bucket", "w_hand"])["runs_remaining"].mean().to_dict()
        self.state_values = grid

        # Compute marginal value: V(bucket, w) - V(bucket, w-1)
        marginal_values = []
        for (bucket, w), val in grid.items():
            if w > 1 and (bucket, w - 1) in grid:
                marginal_drop = val - grid[(bucket, w - 1)]
                self.marginal_wicket_values[(bucket, w)] = float(marginal_drop)
                marginal_values.append(marginal_drop)

        if marginal_values:
            self.mean_marginal_wicket_value = float(np.mean(marginal_values))

        return {
            "mean_marginal_wicket_value": self.mean_marginal_wicket_value,
            "grid_size": len(self.state_values),
            "status": "FITTED"
        }

    def get_wicket_run_value(self, legal_balls_remaining: float, wickets_in_hand: float) -> float:
        """
        Returns the marginal expected run value saved by taking a wicket at this match state.
        Early overs: ~15-20 runs. Middle overs: ~8-12 runs. Death overs: ~2-5 runs.
        """
        bucket = int(np.clip((120.0 - legal_balls_remaining) // 12, 0, 9))
        w = int(np.clip(wickets_in_hand, 1, 10))
        
        if (bucket, w) in self.marginal_wicket_values:
            return max(0.5, self.marginal_wicket_values[(bucket, w)])
        elif (bucket, w - 1) in self.marginal_wicket_values:
            return max(0.5, self.marginal_wicket_values[(bucket, w - 1)])
        else:
            # Dynamic decay model from 18.0 down to 3.0
            return float(np.clip(3.0 + 15.0 * (legal_balls_remaining / 120.0), 1.0, 22.0))
