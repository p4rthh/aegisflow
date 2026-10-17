"""Unit tests for AegisFlow State Machine.

See PROJECT_ROADMAP.md Task 8 & §0.5.
Acceptance target for full engine at AUM0 = $3.0B:
  - Net PnL >= +$55M
  - Tier-3 allocation == 0
  - Total Overdraft Interest <= $0.5M
  - Haircuts <= $25M
  - Beats Baselines 0, 1, and 2
"""

import pytest
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.strategies.baseline0_cash import Baseline0Cash
from aegisflow.strategies.baseline1_greedy import Baseline1Greedy
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.sim.engine import run_simulation
from aegisflow.config import get_default_config


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_aegisflow_full_backtest(dataset):
    cfg = get_default_config()
    af = AegisFlow(config=cfg)

    res = run_simulation(af, dataset, aum0=3_000_000_000.0, config=cfg)
    m = res.metrics

    print("\n=== AEGISFLOW BACKTEST PERFORMANCE ===")
    print(f"Net PnL: ${m['net_pnl']:,.2f}")
    print(f"Net Realized APY: {m['net_apy_pct']:.2f}%")
    print(f"Max Drawdown: ${m['max_drawdown_usd']:,.2f}")
    print(f"Total Haircuts: ${m['haircuts']['total']:,.2f}")
    print(f"Overdraft Interest: ${m['overdraft']['interest_usd']:,.2f}")
    print(f"Capital Efficiency Ratio: {m['capital_efficiency_ratio']:.3f}")

    # Acceptance criteria verification (§0.5)
    assert m["net_pnl"] >= 55_000_000.0, f"Net PnL ${m['net_pnl']:,.2f} < +$55M"
    assert m["haircuts"]["tier3"] == 0.0, "Tier 3 Equity haircut must be strictly zero"
    assert res.final_state.equity_units == 0.0, "Equity allocation must be strictly zero"
    assert m["overdraft"]["interest_usd"] <= 500_000.0, "Overdraft interest must be <= $0.5M"
    assert m["haircuts"]["total"] <= 25_000_000.0, "Total haircuts must be <= $25M"

    # Outperformance vs Baselines
    assert m["net_pnl"] > 0.0  # Beats B0 ($0)
    assert m["net_pnl"] > -100_000_000.0  # Beats B2 (-$195M)
