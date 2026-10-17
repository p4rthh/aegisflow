"""Unit tests for Baselines & Simulator Harness.

See PROJECT_ROADMAP.md Task 3 & §0.5.
"""

import pytest
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.baseline0_cash import Baseline0Cash
from aegisflow.strategies.baseline1_greedy import Baseline1Greedy
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.sim.engine import run_simulation


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_baseline0_cash(dataset):
    b0 = Baseline0Cash()
    res = run_simulation(b0, dataset, aum0=3_000_000_000.0)

    # Baseline 0 must produce exactly $0 PnL, $0 haircuts, 0 overdraft draws at AUM0 = $3B
    assert pytest.approx(res.metrics["net_pnl"], abs=1e-3) == 0.0
    assert res.metrics["haircuts"]["total"] == 0.0
    assert res.metrics["overdraft"]["draws"] == 0
    assert res.metrics["overdraft"]["hours"] == 0


def test_baseline1_greedy_carnage(dataset):
    b1 = Baseline1Greedy()
    res = run_simulation(b1, dataset, aum0=3_000_000_000.0)

    # Baseline 1 chases maximum yield into equities, getting crushed by the -36% crash
    # and paying massive 15% liquidation haircuts (> $1B lost)
    assert res.metrics["net_pnl"] < -1_000_000_000.0
    assert res.metrics["haircuts"]["total"] > 500_000_000.0


def test_baseline2_static(dataset):
    b2 = Baseline2Static()
    res = run_simulation(b2, dataset, aum0=3_000_000_000.0)

    # Baseline 2 suffers from fixed equity allocation and liquidity haircuts (~ -$195M)
    assert res.metrics["net_pnl"] < -100_000_000.0
    assert res.metrics["haircuts"]["total"] > 20_000_000.0
