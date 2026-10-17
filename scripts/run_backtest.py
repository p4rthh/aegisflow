"""Run comprehensive comparative backtest, ablations, and sensitivity.

See PROJECT_ROADMAP.md Task 9.
"""

from aegisflow.data.loader import load_dataset
from aegisflow.sim.backtester import run_comparative_backtest
from aegisflow.sim.ablations import run_ablations
from aegisflow.sim.frontier import run_price_of_safety_frontier
from aegisflow.sim.benchmarks import run_aum_sensitivity


def main():
    print("Loading treasury dataset (8,760 hours)...")
    df = load_dataset()

    print("\n[1/4] Running Comparative Backtest (B0, B1, B2, AegisFlow)...")
    res = run_comparative_backtest(df, aum0=3_000_000_000.0, save_artifacts=True)

    print("\n" + "=" * 80)
    print("                    INSTITUTIONAL BENCHMARK COMPARISON TABLE")
    print("=" * 80)
    print(f"{'Strategy':<20} | {'Net PnL ($)':<16} | {'Net APY':<8} | {'Max DD ($)':<14} | {'Haircuts ($)':<12}")
    print("-" * 80)

    for s_id, m in res["strategies"].items():
        name = s_id.replace("_", " ").title()
        pnl = f"${m['net_pnl']:,.0f}"
        apy = f"{m['net_apy_pct']:.2f}%"
        dd = f"${m['max_drawdown_usd']:,.0f}"
        hc = f"${m['haircuts']['total']:,.0f}"
        print(f"{name:<20} | {pnl:>16} | {apy:>8} | {dd:>14} | {hc:>12}")

    print("-" * 80)
    print(f"Alpha vs Baseline 0 (100% Cash):    +${res['alpha_vs']['baseline0_cash']:,.2f}")
    print(f"Alpha vs Baseline 1 (Naive Greedy): +${res['alpha_vs']['baseline1_greedy']:,.2f}")
    print(f"Alpha vs Baseline 2 (Static Inst):  +${res['alpha_vs']['baseline2_static']:,.2f}")
    print("=" * 80)

    print("\n[2/4] Running Ablation Ladder...")
    abl = run_ablations(df, aum0=3_000_000_000.0, save_artifacts=True)
    print("\n" + "-" * 80)
    print(f"{'Ablation Variant':<42} | {'Net PnL ($)':<16} | {'Delta ($)':<14}")
    print("-" * 80)
    for a in abl:
        print(f"{a['variant']:<42} | ${a['net_pnl']:>15,.0f} | ${a['delta_vs_aegisflow']:>13,.0f}")
    print("-" * 80)

    print("\n[3/4] Running Price-of-Safety Frontier...")
    frontier = run_price_of_safety_frontier(df, aum0=3_000_000_000.0, save_artifacts=True)
    print(f"Frontier calculated: {len(frontier)} policy points.")

    print("\n[4/4] Running AUM Sensitivity ($2B, $3B, $5B, $10B)...")
    sens = run_aum_sensitivity(df, save_artifacts=True)
    print("Sensitivity calculated.")
    print("\nAll backtest artifacts successfully saved to artifacts/")


if __name__ == "__main__":
    main()
