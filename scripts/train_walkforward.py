"""Script to execute walk-forward model training and generate evaluation report.

See PROJECT_ROADMAP.md Task 5.
"""

import json
from pathlib import Path
from aegisflow.data.loader import load_dataset
from aegisflow.forecast.walkforward import run_walkforward_forecast


def main():
    print("Loading dataset...")
    df = load_dataset()
    print(f"Dataset loaded: {len(df)} rows.")

    print("Running walk-forward model training and predictions...")
    preds_df, report = run_walkforward_forecast(df)

    if report:
        print("\n=== WALK-FORWARD FORECAST PERFORMANCE REPORT ===")
        print(f"Pinball Loss Q50: {report['pinball_loss_q50']:,.2f} vs Naive: {report['pinball_loss_naive_q50']:,.2f}")
        print(f"Pinball Loss Q90: {report['pinball_loss_q90']:,.2f}")
        print(f"Pinball Loss Q99: {report['pinball_loss_q99']:,.2f}")
        print(f"Empirical Coverage Q50: {report['empirical_coverage_q50']*100:.1f}% (target ~50%)")
        print(f"Empirical Coverage Q90: {report['empirical_coverage_q90']*100:.1f}% (target ~90%)")
        print(f"Empirical Coverage Q99: {report['empirical_coverage_q99']*100:.1f}% (target ~99%)")

        report_file = Path("artifacts/forecast_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to {report_file}")
    else:
        print("Loaded predictions from cache.")


if __name__ == "__main__":
    main()
