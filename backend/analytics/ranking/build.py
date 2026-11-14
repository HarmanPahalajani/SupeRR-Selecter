import json
from pathlib import Path
import pandas as pd
from backend.analytics.ranking.build_ratings import compute_evidence_based_ratings

def build_player_metrics(processed_dir: str = "data/processed", reports_dir: str = "artifacts/reports"):
    proc_path = Path(processed_dir)
    rep_path = Path(reports_dir)
    rep_path.mkdir(parents=True, exist_ok=True)

    print("Building evidence-based player metrics and rankings...")
    metrics = compute_evidence_based_ratings(proc_path=proc_path)

    out_file = proc_path / "fact_player_metrics.parquet"
    metrics.to_parquet(out_file, index=False)
    print(f"Saved refined fact_player_metrics to {out_file} ({len(metrics)} players, {len(metrics.columns)} columns)!")

    report = {
        "status": "PASS",
        "total_players_evaluated": len(metrics),
        "batting_eligible_players": int(metrics['batting_ranking_eligible'].sum()),
        "bowling_eligible_players": int(metrics['bowling_ranking_eligible'].sum()),
        "both_eligible_players": int((metrics['batting_ranking_eligible'] & metrics['bowling_ranking_eligible']).sum()),
        "undervalued_talents_flagged": int(metrics['is_undervalued_talent'].sum()),
        "cross_format_qualified_players": int(metrics['has_both_formats'].sum()),
        "output_path": str(out_file)
    }
    with open(rep_path / "player_metrics_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    build_player_metrics()
