import json
from pathlib import Path
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.strategies.baseline0_cash import Baseline0Cash
from aegisflow.strategies.baseline1_greedy import Baseline1Greedy
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.sim.engine import run_simulation
from aegisflow.config import get_default_config

df = load_dataset()
cfg = get_default_config()

print("Running simulation benchmarks for all 4 strategies...")
res_af = run_simulation(AegisFlow(config=cfg), df, aum0=3e9, config=cfg)
res_b0 = run_simulation(Baseline0Cash(), df, aum0=3e9, config=cfg)
res_b1 = run_simulation(Baseline1Greedy(), df, aum0=3e9, config=cfg)
res_b2 = run_simulation(Baseline2Static(), df, aum0=3e9, config=cfg)

# Save ticks
res_af.ticks_df.to_parquet("artifacts/ticks_aegisflow.parquet")
res_b0.ticks_df.to_parquet("artifacts/ticks_baseline0_cash.parquet")
res_b1.ticks_df.to_parquet("artifacts/ticks_baseline1_greedy.parquet")
res_b2.ticks_df.to_parquet("artifacts/ticks_baseline2_static.parquet")

results = {
    "aegisflow": res_af.metrics,
    "baseline0_cash": res_b0.metrics,
    "baseline1_greedy": res_b1.metrics,
    "baseline2_static": res_b2.metrics,
}

print("\n=== FINAL TREASURY FINANCIAL BENCHMARKS ===")
for name, m in results.items():
    print(f"[{name.upper()}]")
    print(f"  Final NAV: ${m.get('final_nav', 0):,.2f}")
    print(f"  Net PnL: ${m.get('net_pnl', 0):,.2f}")
    print(f"  Realized APY: {m.get('net_apy_pct', 0):.2f}%")
    print(f"  Sharpe Ratio: {m.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {m.get('max_drawdown_pct', 0):.2f}%")
    od = m.get("overdraft", {})
    print(f"  Overdraft Hours: {od.get('hours', 0)} hrs (${od.get('interest_usd', 0):,.2f} interest)")
    hc = m.get("haircuts", {})
    print(f"  Total Haircuts / Liquidation Loss: ${hc.get('total', 0):,.2f}")
    print()

with open("artifacts/benchmarks_summary.json", "w") as f:
    json.dump(results, f, indent=2)
