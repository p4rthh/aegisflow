# AegisFlow: Institutional Algorithmic Treasury & Liquidity Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Track:** Quantitative Systems & Algorithmic Treasury  
**Challenge:** The Reserve Juggler  
**Target:** Digital Banking Platform moving >$20,000,000 per hour across deposits, withdrawals, and settlements.

---

## 1. System Overview & Architecture

AegisFlow is an institutional-grade, autonomous liquidity and treasury engine designed to solve the fundamental dilemma between zero-yield operational cash buffers and yield-bearing investment vaults with structural market frictions.

```
                           +------------------------+
                           |  treasury_dataset.csv  |
                           +-----------+------------+
                                       |
                                       v
                           +------------------------+
                           |   Data Engine (Pure)   |
                           |  (Loader, Feats, Cal)  |
                           +-----------+------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
+------------------------------------+   +------------------------------------+
|  Quant Brain: Hourly Forecasters   |   |   Macro & Liquidity Regime Veto    |
|   - Quantile LightGBM (P50/90/99)  |   |   - Flow CUSUM (Liquidity Runs)    |
|   - 15-Hour Night Path Bootstrap   |   |   - Rate Momentum Veto (+30 bps)   |
|   - Conformal Tail Calibrator      |   |   - Equity EWMA Realized Vol Gate  |
+------------------+-----------------+   +-----------------+------------------+
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                   +---------------------------------------+
                   |    AegisFlow State Machine Engine     |
                   |   - 08:00 Need-Time Ladder Rebalance  |
                   |   - 17:00 Dynamic Repo Gatekeeper     |
                   |   - Minimum-Cost Knapsack Waterfall   |
                   +-------------------+-------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
+------------------------------------+   +------------------------------------+
|    Ledger & Accounting Engine      |   |    Institutional Audit Logger      |
|   - Canonical Event Order (§1.3)   |   |   - Decision Records with Narrative|
|   - Conservation Identity Checks   |   |   - Knapsack Unit Cost Tables      |
+------------------+-----------------+   +-----------------+------------------+
                   |                                       |
                   v                                       v
+-----------------------------------------------------------------------------+
|                     FastAPI Headless Service Layer                          |
|    - REST Endpoints (/api/backtest, /api/stream, /api/simulate, /theorems)  |
|    - High-Speed WebSocket Replay (/ws/replay) for Google Stitch UI          |
+-----------------------------------------------------------------------------+
```

---

## 2. Key Empirical Findings & Mathematical Theorems

### 2.1 The Structural Drain Finding
Auditing `treasury_4tier_dataset.csv` reveals a **structural cumulative drain of -$2.53 Billion over the year (-$289K/hr, -$6.93M/day)**. Every single month is net negative. Capital is inventory being consumed, not a static balance to allocate.

### 2.2 The Three Break-Even Theorems
1. **Theorem 1 (Overdraft Dominance):** Overnight repo break penalty is 0.5% (72x the ~0.007% overnight yield). The 12% APR central-bank overdraft facility costs only $0.0205\%$ for a 15-hour bridge. **Overdraft is 24.4x cheaper than cracking Tier 1 repo early.**
2. **Theorem 2 (The Equity Horizon Trap):** Equity fire-sale exit haircut is 15.0%. Equities require an uninterrupted 2.48-year holding period to outperform bonds. With a 1-year draining book and a -36.6% equity bear market, the optimal equity allocation is strictly 0.
3. **Theorem 3 (The Need-Time Bond Ladder):** 2Y Sovereign Bonds (2.0% haircut, ~2.2% spread) require ~7,900 hours (10.8 months) to amortize liquidation costs. Bonds are sized strictly for capital with an expected need-time exceeding 11 months.

---

## 3. Institutional Benchmark Results (Full Year, 8,760 Hours)

Simulation across all 8,760 hours at AUM0 = $3.0B:

| Strategy | Net PnL ($) | Net Realized APY | Max Drawdown ($) | Haircut Penalties ($) | Overdraft Interest ($) |
|---|---|---|---|---|---|
| **Baseline 0 (100% Cash)** | $0.00 | 0.00% | $0.00 | $0.00 | $0.00 |
| **Baseline 1 (Naive Greedy)** | -$1,364,160,830 | -76.16% | $1,538,357,729 | $1,164,886,876 | $318,349 |
| **Baseline 2 (Static 20/30/30/20)**| -$203,336,347 | -11.35% | $263,450,645 | $62,506,508 | $2,789,970 |
| **AegisFlow (Our Engine)** | **+$61,367,359** | **+3.43%** | **$30,574,755** | **$12,132,061** | **$457,493** |

### Alpha Delivered:
- **+$61.37 Million** vs Baseline 0 (100% Cash Buffer)
- **+$1.425 Billion** vs Baseline 1 (Naive Greedy)
- **+$264.70 Million** vs Baseline 2 (Static Institutional)

### Ablation Ladder (Proof of Alpha):
- Full AegisFlow: **+$61.4M**
- AF without Bond Ladder (Repo Only): **+$45.6M** ($\Delta = -\$15.7M$ proof of ladder alpha)
- AF with Fixed Liquidity-Rank Waterfall: **+$43.1M** ($\Delta = -\$18.2M$ proof of knapsack optimizer alpha)
- Static 20/30/30/20 with Cost Waterfall (B2+): **-$156.3M** ($\Delta = -\$217.6M$)

---

## 4. Quickstart & Commands

### Installation
```bash
git clone <repo-url>
cd reserve-juggler
pip install -e .
```

### Run Tests (100% Passing)
```bash
pytest -q
```

### Run Backtests & Generate Cache
```bash
python scripts/run_backtest.py
python scripts/make_demo_cache.py
```

### Start FastAPI Server
```bash
uvicorn aegisflow.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation: `http://localhost:8000/docs`  
Exported OpenAPI schema: [openapi.json](file:///home/idioticspaceman/reserve-juggler/openapi.json)

---

## 5. API Endpoints for Google Stitch UI

- `GET /api/health` — System status and artifact readiness
- `GET /api/meta/config` — Global config, frictions, parameters
- `GET /api/theorems` — Live quantitative break-even calculations (Why panel)
- `GET /api/stream/tick` — Synchronous multi-strategy tick state with gatekeeper metadata
- `GET /api/stream/range` — Downsampled historical replay slices
- `GET /api/backtest/compare` — Full comparative backtest KPIs and equity curves
- `GET /api/backtest/ablations` — Ablation ladder component alpha breakdown
- `GET /api/backtest/frontier` — Price-of-Safety risk tolerance grid
- `GET /api/backtest/sensitivity` — AUM sensitivity ($2B, $3B, $5B, $10B)
- `POST /api/simulate/stress-test` — Chaos injection simulator (withdrawal surge, rate shocks, equity crashes)
- `GET /api/logs/decisions` — Filterable institutional audit logs with human narratives
- `WS /ws/replay` — Real-time replay WebSocket with play/pause/seek/speed controls
