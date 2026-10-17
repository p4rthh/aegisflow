"""Precompute all artifacts for instant API responses and live demos.

See PROJECT_ROADMAP.md Task 13.
"""

from pathlib import Path
from aegisflow.data.loader import load_dataset
from aegisflow.forecast.walkforward import run_walkforward_forecast
from aegisflow.sim.backtester import run_comparative_backtest
from aegisflow.sim.ablations import run_ablations
from aegisflow.sim.frontier import run_price_of_safety_frontier
from aegisflow.sim.benchmarks import run_aum_sensitivity
from aegisflow.config import get_default_config


def main():
    print("=" * 70)
    print("       AEGISFLOW: PRECOMPUTING DEMO CACHE & ARTIFACTS")
    print("=" * 70)

    print("\n[1/5] Loading 8,760-hour treasury dataset...")
    df = load_dataset()

    print("\n[2/5] Precomputing Walk-Forward Quantile Forecasts...")
    preds_df, _ = run_walkforward_forecast(df)
    print(f"  Forecasts cached: {len(preds_df)} hourly predictions.")

    print("\n[3/5] Precomputing Institutional Comparative Backtests ($3B AUM)...")
    cfg = get_default_config()
    bt_res = run_comparative_backtest(df, aum0=3_000_000_000.0, config=cfg)
    print(f"  AegisFlow Net PnL: ${bt_res['strategies']['aegisflow']['net_pnl']:,.2f}")

    print("\n[4/5] Precomputing Ablation Ladder & Price-of-Safety Frontier...")
    abl = run_ablations(df, aum0=3_000_000_000.0, config=cfg)
    print(f"  Ablations cached: {len(abl)} variants.")
    frontier = run_price_of_safety_frontier(df, aum0=3_000_000_000.0, config=cfg)
    print(f"  Safety Frontier cached: {len(frontier)} points.")

    print("\n[5/5] Precomputing AUM Sensitivity Grid ($2B, $3B, $5B, $10B)...")
    sens = run_aum_sensitivity(df, config=cfg)
    print(f"  Sensitivity cached across {len(sens)} AUM levels.")

    print("\n" + "=" * 70)
    print(" DEMO CACHE READY: All artifacts saved to artifacts/")
    print(" API is primed for sub-millisecond response times.")
    print("=" * 70)


if __name__ == "__main__":
    main()
