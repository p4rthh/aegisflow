# PROJECT_ROADMAP.md — AegisFlow: Algorithmic Treasury & Liquidity Engine
**Challenge:** The Reserve Juggler (Quantitative Systems & Algorithmic Treasury)
**Scope:** Backend only — data, quant models, optimizer, state machine, simulator, FastAPI. No frontend code.
**Audience:** Antigravity coding agents + Flash 3.8. Every section is written to be executed without clarification.

---

## 0. READ THIS FIRST — Data Audit, Corrections, and Added Insights

I (the architect) audited `treasury_4tier_dataset.csv` and the judges' PDF before writing this plan. Several things in the original brief are confirmed, several need correction, and several findings **change the strategy**. Agents must treat this section as authoritative over any conflicting statement elsewhere.

### 0.1 Verified facts (safe to rely on)
| Check | Result |
|---|---|
| Shape / quality | 8,760 rows × 16 cols, zero NaN, strictly hourly, monotonic |
| Flags | `repo_sweep_window_open` True exactly 365× (hour 17), `repo_sweep_mature` True 365× (hour 8) |
| `net_flow_usd` | equals deposits − withdrawals (max abs diff $0.01) |
| Overnight window | 17:00→07:00 = **15 hourly rows**. Mean cumulative net flow −$5.72M (matches brief's −$5.73M) |
| "Extreme tail −$46.66M" | This is the **peak intra-night running drain** (min of the running cumulative sum), not the terminal sum (worst terminal = −$44.0M on 2026-07-03). **Sweep sizing must use the running-minimum path.** |
| Bond | $dP/P$ vs $dy$ regression slope = −1.918 (corr −0.9998) → $D_{mod}=1.92$ confirmed. `tier2_bond_price_index` is **clean** price ⇒ carry (coupon accrual) must be added separately |
| Equity | start 4988.59, peak 5470.67 (Jan 19), **trough 3470.95 (Dec 5)**, year-end 3550.04. Year-end return −28.8%, **peak-to-trough −36.6%** |
| Seasonality | Hourly mean net flow: +$1.80M @08:00, −$2.30M @17:00. Day-of-month 1st: +$3.57M/hr, 15th: +$3.19M/hr; 2nd,3rd,16th,17th: −$1.75…−2.13M/hr. Fri −$1.28M, Sat −$3.21M/hr |
| Persistence | Net-flow autocorrelation: lag1 0.695, lag2 0.62, lag3 0.53, lag24 0.17, lag168 0.37 ⇒ residual path structure matters |
| Extreme hours | Largest single-hour net outflow −$32.5M (2026-11-14 16:00), −$31.9M (11-13 12:00), −$27.1M (11-28 15:00) |
| Worst nights (terminal) | 07-03 (−44.0M), 08-29 (−40.9M), 01-16 (−36.4M), 12-25 (−35.6M), 02-07 (−35.5M) |

### 0.2 Corrections / traps in the data
1. **`tier3_stock_volatility_pct` is a constant 18.0 — it carries zero information.** Realized annualized vol computed from the price series is **≈25%**, realized drift ≈ −34%/yr. The equity risk filter MUST compute its own EWMA realized volatility from `tier3_stock_index_price`. Do not use the column as a feature.
2. `tier2_bond_mod_duration` is also constant (1.92). Use as a parameter only.
3. `tier1_repo_rate_apy` changes ~8,000 times a year (hourly noise around 3.73–4.37%). **Lock the rate observed at the 17:00 sweep row**; accrue overnight interest at that locked rate.
4. All haircut / penalty columns are constants. Read them from the CSV once into `FrictionConfig`; do not treat them as time series features.
5. The `tier2_bond_price_index` ends at 99.869 while yield ended at 4.868 (started 4.80). Clean-price drift is small; **carry (≈4.75%/yr) dominates the bond return**, with a Sept–Oct drawdown (yield 4.52% → 5.37%, price −2.3%).

### 0.3 The single most important finding: the book has a structural liquidity drain
Mean net flow is **−$289K per hour = −$6.93M/day = −$2.53 billion over the year.** Cumulative net flow bottoms at **−$2.589B on Dec 26**. Monthly net flow is negative in all 12 months (−$113M to −$312M).

Consequences (these drive the whole design):
* **The judges' materials never state starting capital.** A treasury with less than ≈$2.6B of liquid assets *cannot* survive the year without permanent overdraft. We therefore introduce an explicit parameter **`AUM0` (default $3.0B)** and run sensitivity at **$3B / $5B / $10B**. The demo must state this assumption out loud.
* Capital is **not** a static pool to "allocate" — it is **inventory that is consumed at ≈$6.9M/day**. The core question for every dollar is *"when will I need it?"*, not just *"which tier has the best yield?"*. This is the **Need-Time Ladder** (§2.5), our principal addition.
* Economic PnL must exclude customer principal flows: **PnL = ΔNAV − Σ net_flow** (§3.5).

### 0.4 Three break-even theorems (these overturn the naive reading of the brief)
Let $\;h_1=0.5\%,\;h_2=2\%,\;h_3=15\%,\;OD=12\%\text{ APR}$.

**Theorem 1 — Overdraft is the cheapest bridge for any shortfall that cures within 15 days.**
Overdraft cost per $ for $h$ hours: $OD\cdot h/8760$. Break-even duration against each penalty:
$$h^*_{repo}=\tfrac{0.005}{0.12}\cdot 8760=365\text{ h},\quad h^*_{bond}=1{,}460\text{ h},\quad h^*_{equity}=10{,}950\text{ h}.$$
A full-night overdraft (15 h) costs **0.0205%** vs 0.5% for cracking the repo — **24× cheaper**. Cracking Tier 1 early is *dominated* by overdraft whenever the shortfall will cure at the 08:00 maturity. The brief's "protect against early Repo breaks with a P99.5 buffer" is therefore **over-conservative from a pure cost view**; we implement it as a selectable *risk guardrail*, and show the *price of safety* (§2.3.4). This is a headline insight for judges.

**Theorem 2 — Tier 3 equities are structurally uneconomic for a draining book.**
Break-even holding period for equities vs bonds: $\tau_e=(h_3-h_2)/(\mu_3-y_2)=0.13/0.0525\approx 2.5$ years. The dataset is 1 year, the book drains $2.5B/yr, and the realized path is −29%. **At the default AUM the optimal Tier 3 allocation is 0.** Equities are admitted only for "permanent capital" (AUM beyond the 2.5-year need horizon) and only through the regime veto (§2.4). Agents must NOT force a nonzero equity allocation to "look balanced".

**Theorem 3 — Bonds pay only for dollars not needed for ≈11 months, and the repo is only 15/24 effective.**
Rolling repo yields only 15 hours of each day: effective liquid-pool yield $r_1\cdot15/24\approx2.53\%$. Idle cash 08:00→17:00 forgoes $r_1\cdot 9/8760$ per $/day (≈$41.7K/day per $1B). Bond spread over the pool ≈ $4.75\%-2.53\%=2.22\%$, so
$$\tau_b=\frac{h_2}{y_2-r_1\cdot15/24}\approx 0.90\text{ yr}\;(\approx 7{,}900\text{ h}).$$
Bonds are optimal only for the slice of AUM whose forecast *need-time* exceeds $\tau_b$. This is the Need-Time Ladder.

### 0.5 Reference prototype & expected results (calibration targets)
A 150-line rules-only prototype (`reference_prototype/`, delivered alongside this file) was run to validate the economics. Results at **AUM0 = $3.0B**, full 8,760 hours:

| Strategy | Net PnL | Haircuts | Notes |
|---|---:|---:|---|
| Baseline 0 — 100% cash | **$0** | $0 | No overdraft only because AUM0 ≥ $2.59B |
| Baseline 1 — Naive Greedy (all-in equities) | **≈ −$1,364M** | ≈ $1,165M (equity) | 1,441 overdraft draws, NAV collapses |
| Baseline 2 — Static 20/30/30/20 | **≈ −$195M** | ≈ $54M | Equity bear market + forced haircuts |
| Aegis-lite (repo only, no ladder) | ≈ +$45.7M | $0 | Proves Tier-1 daily roll alone is positive |
| Aegis-lite (repo + bond ladder + cost waterfall) | **≈ +$60.4M** | ≈ $19.2M | Tier 3 = 0; overdraft interest ≈ $0.08M total |
| Aegis-lite @ AUM0 $5B / $10B | ≈ +$176M / +$467M | ≈ $17M / $13M | Baseline 2: −$211M / −$403M |

Ablation signal: cost-aware waterfall vs fixed pecking order ≈ **+$4.6M**; bond ladder vs repo-only ≈ **+$15M** at $3B.
**Acceptance target for the full engine at AUM0=$3B: Net PnL ≥ +$55M, Tier-3 allocation = 0, total overdraft interest ≤ $0.5M, B1 < −$1.0B, B2 < −$100M.** (Prototype parameters were set from theory, not fitted — be ready to say so.)

### 0.6 Honest scale note (use in the demo)
The nightly buffer decision is worth far less than intuition suggests: in-sample, the cost-optimal overnight buffer is **≈$9.3M**, vs **≈$36.4M** (P98.6) or **≈$41.8M** (P99.5). The extra ≈$32M of idle buffer forgoes only ≈$2.3K/night ≈ **$0.8M/yr**. The money is in (1) never paying haircuts, (2) the daily repo roll, (3) the Need-Time bond ladder, (4) never owning equities into a bear market. Frame the pitch accordingly — judges respond to calibrated claims.

---

## 1. System Architecture & Modular Decomposition

### 1.1 Layered design
```
 CSV ─► [Data Engine] ─► [Quant Brain: Forecasters] ─► [Regime Detectors] ─┐
            │                      │                                       │
            ▼                      ▼                                       ▼
        [Ledger/Accounting] ◄─ [Optimization & Waterfall] ◄─ [AegisFlow State Machine]
            │                                                              │
            ▼                                                              ▼
   [Simulator/Backtester] ─► [Metrics/Benchmarks/Ablations] ─► [Audit Log] ─► [FastAPI + WS]
```

| Module | Responsibility | Purity |
|---|---|---|
| `data` | load, validate, calendar, feature frame, **stress transformer** | pure functions |
| `ledger` | state, instruments, canonical per-tick event order, accounting identities, metrics | deterministic, no I/O |
| `forecast` | hourly quantile models, 15-h night path engine, conformal calibration, cure-time function | walk-forward only, no look-ahead |
| `regime` | flow-shock CUSUM, rate momentum, equity trend/vol/drawdown veto | pure |
| `optimize` | repo sizing, waterfall (greedy + LP verifier), need-time ladder | pure |
| `strategies` | Baselines 0–2, AegisFlow state machine | stateful via ctx |
| `sim` | engine loop, benchmark orchestrator, ablations, safety frontier | deterministic, seedable |
| `audit` | decision records + templated narratives | append-only |
| `api` | REST + WebSocket, schemas, caching | thin; no business logic |

### 1.2 Repository layout (create exactly this)
```
aegisflow/
├── pyproject.toml               # python>=3.11; deps: pandas numpy scipy lightgbm scikit-learn fastapi uvicorn pydantic>=2 pyarrow pyyaml pytest hypothesis numba(optional) holidays
├── README.md  Makefile  .env.example
├── configs/
│   ├── default.yaml             # all tunables (see §1.3)
│   └── stress_presets.yaml
├── data/raw/treasury_4tier_dataset.csv
├── data/processed/              # parquet caches (git-ignored)
├── artifacts/                   # walk-forward predictions, backtest results (git-ignored)
├── reference_prototype/         # validated rules-only simulator (regression oracle)
├── src/aegisflow/
│   ├── __init__.py  config.py  constants.py  types.py
│   ├── data/      loader.py validator.py calendar.py features.py stress.py
│   ├── ledger/    state.py instruments.py engine_step.py accounting.py metrics.py
│   ├── forecast/  hourly_model.py night_paths.py conformal.py walkforward.py cure_time.py
│   ├── regime/    flow_regime.py rate_regime.py equity_regime.py
│   ├── optimize/  repo_sizing.py waterfall.py lp_verify.py ladder.py
│   ├── strategies/ base.py baseline0_cash.py baseline1_greedy.py baseline2_static.py aegisflow.py
│   ├── sim/       engine.py backtester.py benchmarks.py ablations.py frontier.py
│   ├── audit/     decision_log.py narrative.py
│   └── api/       main.py schemas.py deps.py routes_stream.py routes_backtest.py routes_stress.py routes_logs.py routes_meta.py ws.py
├── scripts/       train_walkforward.py run_backtest.py make_demo_cache.py export_openapi.py
└── tests/         unit/ property/ e2e/
```

### 1.3 Core conventions (global; every agent obeys)
* **Units:** USD as `float64`. Rates are **decimal fractions internally** (CSV `4.292` → `0.04292`). Hours are integers. `HOURS_PER_YEAR = 8760`.
* **Sign convention:** `net_flow` = deposits − withdrawals. **`outflow = −net_flow`** (positive = drain). Forecast models predict `outflow`. A "P99 outflow" is the *1st percentile of net flow*. Unit-test this.
* **Timing convention (canonical, never deviate):** Row `t` flows are credited *during* hour `t`. Decisions made in `pre()` at row `t` may use information **through row t−1 only** (never row-t flows, never any future row).
  * Sweep: executes in `pre()` of the row with `hour==17`, *before* that row's flow. Locked for rows 17,18,…,23,0,…,7 (**15 rows**).
  * Maturity: processed at the start of the row with `hour==8`, *before* that row's flow. Proceeds = principal × (1 + r_lock × 15/8760).
* **Canonical per-tick event order (identical for every strategy):**
  1. Repo maturity (if `repo_sweep_mature`) → cash
  2. Bond carry credited to cash: `U2·P2_t·y2_t/8760`
  3. Overdraft interest accrues: `O ← O·(1+OD/8760)`
  4. `strategy.pre()` actions (sells → repay OD → buys → sweep)
  5. Apply `net_flow_t` to cash
  6. If cash < 0: `strategy.resolve()` returns a source ordering; waterfall executes it; any remainder becomes overdraft
  7. If cash > 0 and O > 0: repay overdraft
  8. Mark to market at row-`t` prices; record NAV and state
  9. `strategy.post()` (update estimators with row-`t` data)
* **Purchases are frictionless** (the data specifies only liquidation haircuts). Expose `purchase_cost_bps` (default 0) in config.
* **Equity return = price return only** (no dividends in data); optional `equity_dividend_yield` default 0.
* **Determinism:** global `seed` in config; all Monte-Carlo uses `numpy.random.Generator(PCG64(seed))`.
* **Float tolerance:** accounting reconciliation within **$1.00** over the full year.

---

## 2. Quant & ML Modeling Strategy

### 2.1 Hourly Tactical Forecaster (Quantile GBM)
**Target:** `y_t = outflow_t = −net_flow_t`. Separate LightGBM models with `objective='quantile'`, `alpha ∈ {0.5, 0.9, 0.99}` (pinball loss $L_\alpha(y,\hat q)=\max(\alpha(y-\hat q),(\alpha-1)(y-\hat q))$). Plus one L2 "mean" model (used by the night path engine).

**Features** (all computed from rows ≤ t−1; enforce with a leakage test):
* Cyclical: `sin/cos` of hour (24), day-of-week (7), day-of-month (≈31), month-of-year.
* Calendar flags: `is_payday` (dom ∈ {1,15}), `post_payday_drain` (dom ∈ {2,3,16,17}), `is_fri`, `is_sat`, `is_month_end`, `days_since_payday`, `is_us_holiday`, `day_before_holiday` (Jul 3, Dec 25 produced top-5 worst nights).
* Lags of net flow, deposits, withdrawals: 1,2,3,6,12,24,48,168. Same-hour-yesterday / same-hour-last-week.
* Rolling momentum: mean & std over 6/24/168 h; EWMA(α=0.3); rolling 24-h min cumulative; `flow_zscore_6h`.
* **Exclude market columns** (rates, equity) from flow models — avoids spurious correlation.

**Validation (walk-forward, expanding window):** first model fit after 21 days; retrain every 7 days (`train_end < prediction_start`). Predictions cached to `artifacts/hourly_preds.parquet` with columns `q50,q90,q99,mean`. Post-process: enforce monotone quantiles (`q50 ≤ q90 ≤ q99`). Report: pinball loss per quantile vs seasonal-naive (same-hour-last-week), empirical coverage (target 50/90/99% ±3pp), PIT histogram.
**Burn-in rule:** until day 21, use the conservative prior (night buffer $50M, no bonds).

### 2.2 Cure-Time Function (new; feeds the waterfall)
For a shortfall of size $x$ at time $t$, define the **expected overdraft duration**
$$T_t(x)=\mathbb{E}\big[\min(\tau_x,\,H_{max})\big],\quad \tau_x=\min\{k:\ F_{t+1..t+k}+\text{Repo}_{mat}(k)\ \ge x\}$$
estimated from the path engine (§2.3.2). $H_{max}=1{,}460$ h (beyond that, a bond sale is cheaper than overdraft). Overdraft unit cost = $OD\cdot T_t(x)/8760$.
* If a repo maturity ≥ $x$ is pending: $\tau_x$ ≤ hours to 08:00.
* If no cure exists in the horizon (structural drain): $T=H_{max}$ ⇒ cost 2.0% ⇒ ties go to the bond sale (the structural part is funded by liquidation, the transient part by overdraft).

### 2.3 The 17:00 Repo Gatekeeper (15-hour horizon)

#### 2.3.1 Definitions
Let $F_k$ be net flow in the $k$-th overnight hour ($k=1..15$, rows 17…07), $S_k=\sum_{j\le k}F_j$ cumulative net flow, and
$$D=\max_{k}\big(-S_k\big)^+\quad(\text{peak intra-night drain}).$$
Keep **buffer $B$** in cash, sweep $S=\max(0,\;C_{17}-B)$ (cash after intraday ops, minus any outstanding overdraft).
Per-dollar overnight repo yield: $y_n=r\cdot15/8760$ (for $r=4.055\%$, $y_n=6.94\times10^{-5}$).

#### 2.3.2 Night path engine (primary)
1. Mean path from the L2 hourly model for rows 17…07 using only info through 16:00.
2. Residual vectors $\epsilon\in\mathbb{R}^{15}$ from past nights (walk-forward), **stratified by calendar class** (heavy = Fri/Sat or dom∈{1,2,3,15,16,17} or holiday-adjacent; normal otherwise). **Resample whole 15-vector nights** (night-block bootstrap) — this preserves the lag-1 autocorrelation (0.695) that an i.i.d. draw would destroy.
3. 10,000 simulated paths ⇒ distribution of $D$ and of crossing times.
4. **Rolling conformal calibration:** inflate residual scale by $\kappa_t$ so that empirical coverage of $P_{99.5}(D)$ over the trailing 60 nights ≥ 99.5% −tolerance. Fall back to empirical quantile of historical $D$ in the same class if <10 samples.
5. Optional: GPD tail fit (peaks-over-threshold) on $D$ for P99.9 stability.

#### 2.3.3 Derivation of the sweep sizing rules (three rules, one framework)
**Marginal condition.** Holding one extra dollar in cash (raising $B$ by $dB$) costs forgone repo yield $y_n\,dB$ and saves the penalty incurred if the night's drain exceeds $B$.

**Rule A — Break-only (the brief's framing).** If the only recourse to a shortfall is cracking the repo, the saving is $h_1\cdot P(D>B)\,dB$. Setting equal:
$$P(D>B^*)=\frac{y_n}{h_1}=\frac{r\cdot15/8760}{0.005}=\frac{6.94\times10^{-5}}{0.005}=1.39\%\;\Rightarrow\; B^*_A=Q_{98.61\%}(D).$$
Penalty-to-yield ratio = 72×, so critical fractile = $1-1/72$ = **98.61%** (≈$36.4M in-sample). The brief's P99.5 (≈$41.8M) is a stricter policy than Rule A requires.

**Rule B — Overdraft-optimal (our default, `risk_mode: cost_optimal`).** If overdraft is available, a shortfall that begins at hour $k_0$ is financed until maturity at 08:00, i.e. $h(B)=15-k_0$ hours at $OD/8760$ per $. Saving $=\tfrac{OD}{8760}\,\mathbb{E}[h(B)]\,dB$. Equating to $y_n dB$:
$$\boxed{\ \mathbb{E}\big[h(B^*)\big]=\frac{15\,r}{OD}\approx 5.07\text{ overdraft-hours at the margin}\ }$$
$\mathbb{E}[h(B)]$ is monotone decreasing in $B$ ⇒ solve by bisection on the simulated paths. In-sample $B^*_B\approx\$9.3M$ (P(D>B*)≈42% — crossings are frequent but each costs ≈$0.00002/$).

**Rule C — Guarded (`guarded` and `conservative` modes).** The overdraft facility is capped at $K$ and reputationally sensitive. Require $P(D>B+K)\le\epsilon$:
$$B_C=\max\big(B^*_B,\;Q_{1-\epsilon}(D)-K\big).$$
`conservative` = $K=0,\ \epsilon=0.5\%$ (the brief's P99.5 rule, ≈$41.8M). `guarded` default: $K=\$25M,\ \epsilon=0.5\%$. Config: `risk_mode ∈ {cost_optimal, guarded, conservative}`.

#### 2.3.4 Price-of-Safety Frontier (new, demo feature)
Backtest across $\epsilon\in\{50\%,10\%,5\%,1.39\%,0.5\%,0.1\%\}$ × $K\in\{0,10,25,50,\infty\}$. Output (expected overnight-buffer $, annual PnL, overdraft-hours, peak overdraft). Expected shape: PnL falls only ≈$0.8M/yr from cost-optimal to P99.5, while peak overdraft falls from ≈$37M to $0 — giving the judge a *dial*, not a dogma.

### 2.4 Macro Regime & Risk Filters

#### 2.4.1 Bonds (Tier 2) — duration-aware
* Price move: $\Delta P/P\approx-D_{mod}\,\Delta y$ (confirmed). Carry per week ≈ $y\cdot7/365\approx 9.1$ bp… i.e. $4.75\%\times 7/365=9.1\text{ bp}$.
* **Carry-vs-duration breakeven over horizon $T$ (years):** the yield rise that wipes carry is $\Delta y_{be}=y\,T/D$. For one week: $\approx4.7$ bp; for one month: $\approx20$ bp.
* **Rate momentum veto (purchases only):** $m_{168}=y_t-y_{t-168}$. If $m_{168}>+30\,$bp ⇒ no new bond purchases. (A +30 bp move ≈ −0.58% price.)
* **Never sell bonds on a regime signal.** Selling costs 2.0%; justifying it requires an expected rise of $\Delta y\ge h_2/D=104$ bp. Bonds are sold only to fund need (waterfall/refill). State this in the audit narrative.
* Optional z-score: $z=(y_t-\overline{y}_{30d})/\sigma_{30d}$; veto purchases if $z>2$.

#### 2.4.2 Equities (Tier 3) — one-way door
Because exit costs 15%, **entry gates are strict; exits happen only through need**.
* Eligibility (all required): (i) *Permanent-capital test:* `NAV − Need(2.5y) > 0` (Theorem 2); (ii) trend: price > SMA(30d) **and** SMA(30d) > SMA(90d); (iii) drawdown from 90-day high > −8% is *not* breached, i.e. `price/max90 − 1 ≥ −0.08`; (iv) EWMA realized vol (λ=0.97 hourly, annualized) ≤ 30%; (v) not in `STRESS_ELEVATED` flow state.
* Sizing: $w_{3}=\min\big(w_{cap},\ \tfrac{\text{NAV}_{perm}}{\text{NAV}},\ \tfrac{\sigma_{target}}{\hat\sigma}\cdot w_{base}\big)$, defaults $w_{cap}=15\%,\ \sigma_{target}=10\%$.
* **Drawdown circuit breaker:** if equity MV falls >12% from its post-purchase high, **freeze further buys for 30 days**. No forced sale (15% would lock in loss) unless the waterfall needs it.
* Expected result on this dataset: filters keep Tier 3 at 0 at AUM0 = $3B and at most a small, late sleeve at $10B.

#### 2.4.3 Flow-regime detector (liquidity runs)
* Standardized residual $z_t=(y_t-\hat q_{50,t})/\hat\sigma_t$, with $\hat\sigma_t$ from $(q_{90}-q_{50})/1.2816$.
* **CUSUM** $G_t=\max(0,G_{t-1}+z_t-k)$ with $k=0.5$; trigger `STRESS_ELEVATED` if $G_t>h=5$; exit when $G_t<1$ for 6 consecutive hours.
* Effect in STRESS: multiply residual scale by 1.5 in path engine, raise buffer by that amount, block bond purchases, switch to `guarded` mode at minimum.

### 2.5 Need-Time Ladder (strategic capital allocation) — our principal addition
**Idea:** sort the portfolio's dollars by *when they will be needed*; assign each slice to the tier that maximizes net value over that horizon.

**Need function:** $X(\tau)=\max(0,-\hat d)\cdot\tau\cdot(1+m)$ where $\hat d$ = mean hourly net flow estimated by expanding-then-60-day EWMA (**not before day 35** — the first payday cycle inflates early estimates; a 14-day estimate gave −$62K/h vs the true −$289K/h in our debugging), $m$=safety margin (default 10%).

**Tier assignment by need-time $\tau$:**
| Slice | Rule | Dynamic threshold |
|---|---|---|
| Liquid pool (cash+repo) | $\tau<\tau_b$ | $\tau_b=\dfrac{h_2}{\max(\varepsilon,\;y_{2,t}-r_{1,t}\cdot15/24)}\cdot 8760$ h; if spread ≤ 20 bp ⇒ $\tau_b=\infty$ |
| Bonds | $\tau_b\le\tau<\tau_e$ | $\tau_e=\dfrac{h_3-h_2}{\max(\varepsilon,\mu_3-y_2)}$ yr (≈2.5 yr); subject to §2.4.1 veto |
| Equities | $\tau\ge\tau_e$ | subject to §2.4.2 gates |

**Targets:** `bond_target = clamp(NAV − X(τ_b)(1+m) − equity_target, 0, bond_cap)`; `equity_target = clamp(NAV − X(τ_e)(1+m), 0, w_cap·NAV)` (zero unless gates pass).
**Pool refill rule (08:00, after maturity):** `pool_req = B_night + pool_days·24·max(0,−d̂)` (default `pool_days=3`). If `cash − OD < pool_req` sell bonds (cost 2%) just enough; else if `bond MV < bond_target` and veto clear, buy `min(bond_target − MV, cash − pool_req)`.

---

## 3. Optimization & Liquidity Waterfall Engine (Execution Core)

### 3.1 Deficit settlement — exact formulation
At end of hour $t$, shortfall $\Delta=\max(0,-C_t)$. Decision variables are **net dollars delivered** $x_s\ge0$:

| Source $s$ | Capacity | Unit cost $c_s$ (per net $) |
|---|---|---|
| OD: overdraft | $K-O_t$ ($K=\infty$ if uncapped) | $c_{OD}=\dfrac{OD\cdot T_t(x)}{8760}$ |
| T1: break repo | $R_t(1-h_1)$ | $\dfrac{h_1}{1-h_1}+\ell_1$ (forfeited accrued interest, ≈ $y_n\cdot\text{elapsed}/15$) |
| T2: sell bonds | $MV_2(1-h_2)$ | $\dfrac{h_2}{1-h_2}+\ell_2$, where $\ell_2$ = forgone carry vs best reinvestment of the proceeds' alternative = 0 (proceeds used immediately) |
| T3: sell equities | $MV_3(1-h_3)$ | $\dfrac{h_3}{1-h_3}$ (+ regime penalty if trend filter bullish) |

$$\min_{x}\ \sum_s c_s x_s\quad\text{s.t.}\quad\sum_s x_s=\Delta,\quad 0\le x_s\le\text{cap}_s.$$
This is a **fractional knapsack ⇒ greedy by ascending $c_s$ is the exact optimum.** `lp_verify.py` solves the same instance with `scipy.optimize.linprog(method='highs')` and must match to $10^{-6}$ on 10,000 random instances (property test).
**Cure-time subtlety:** $c_{OD}$ depends on $x$ (concave staircase: small amounts cure fast). Implement as piecewise segments: split $\Delta$ into 5 tranches $x_i$, each with its own $T_t(\cdot)$; the LP remains linear (each tranche is an OD source with its own cost and a nested-capacity constraint).
**Tie-break rule:** ties go to the *non-overdraft* source (stops accruing; stabilizes the book).
**Economic pecking order that emerges** (with typical numbers): overnight shortfall curing at 08:00 → OD (0.02%) < repo break (0.5%) < bond (2%) < equity (15%); structural/persistent shortfall → bond (2%) < OD(≥2% at 1,460 h) < equity.
**Overdraft cap policy:** `overdraft_cap` default `null` (unlimited) in `cost_optimal`, $25M in `guarded`; when the cap binds the next-cheapest source takes the remainder. Audit log must record the cap-binding event.

### 3.2 Excess-cash deployment (surplus side)
Executed at fixed decision points only (to avoid churn):
* **08:00** (post-maturity): refill / ladder purchase per §2.5.
* **17:00:** `sweep = max(0, C − O − B_night)` into Tier 1.
* **Any hour:** if overdraft > 0 and cash > 0, repay first (never deploy while indebted).
Purchases are executed after sells and OD repayment in the same `pre()`.

### 3.3 State machine (AegisFlow)
Hour-of-day driven primary states with overlay flags.

| State | Hours | Entry actions | Exit |
|---|---|---|---|
| `MORNING_REBALANCE` | 08 | Repo matured → cash; OD repay; pool refill / ladder buy | → `DAYTIME_MONITOR` |
| `DAYTIME_MONITOR` | 09–16 | Hourly waterfall on deficits; update estimators | at 17 → `SWEEP_DECISION` |
| `SWEEP_DECISION` | 17 | Run night path engine → $B$ → sweep | → `OVERNIGHT_LOCKED` |
| `OVERNIGHT_LOCKED` | 18–07 | Repo locked; shortfalls via cure-time waterfall (OD first) | at 08 → `MORNING_REBALANCE` |
| Overlay `STRESS_ELEVATED` | any | CUSUM trigger (§2.4.3): scale up buffer, block bond buys, `guarded` floor | CUSUM clears |
| Overlay `OD_RECOVERY` | any | OD>0: repay first; no purchases; no sweep beyond need | OD == 0 |

Every transition and every non-trivial action emits a **decision record** (§5.6).

### 3.4 Pseudocode (reference for `strategies/aegisflow.py`)
```python
def pre(self, t, S, ctx):                      # info through t-1 only
    acts = []
    if S.O > 0: acts.append(Repay(S.O))
    B = self.repo_sizing.buffer(t, ctx)        # Rule A/B/C by risk_mode
    if hour(t) == 8 and ctx.day >= 35:
        pool_req = B + ctx.pool_days*24*max(0, -ctx.d_hat)
        free = S.C - S.O
        if free < pool_req and S.bond_mv > 0:
            acts.append(SellBond((pool_req - free)/(1-H2)))
        else:
            tgt = self.ladder.bond_target(t, S, ctx)
            if tgt > S.bond_mv and self.rate_regime.ok(t):
                acts.append(BuyBond(min(tgt - S.bond_mv, max(0, free - pool_req))))
            eq_tgt = self.ladder.equity_target(t, S, ctx)       # 0 unless gates pass
            ...
    if hour(t) == 17:
        acts.append(Sweep(max(0.0, S.C - S.O - B)))
    return acts

def resolve(self, t, need, S, ctx):
    return self.waterfall.order(t, need, S, ctx)  # ascending unit cost; ties -> non-OD
```

### 3.5 Accounting equations (exact)
Let $C$ cash, $R$ repo principal, $r_{lock}$ locked rate, $\eta$ hours since sweep ($\eta=1..15$), $U_2,U_3$ units, $O$ overdraft.
* **Repo accrued (for NAV):** $A_1=R\cdot r_{lock}\cdot\eta/8760$.   **Maturity:** $C\mathrel{+}=R(1+r_{lock}\cdot15/8760)$.
* **Repo break of principal $a$:** proceeds $a(1-h_1)$; **fee** $=a h_1$; forfeits accrued interest on $a$.
* **Bonds:** buy $v$: $U_2\mathrel{+}=v/P_{2,t}$. $MV_2=U_2P_{2,t}$. Carry per hour credited to cash: $U_2P_{2,t}y_{2,t}/8760$. Sell notional $v$: proceeds $v(1-h_2)$, fee $vh_2$.
* **Equities:** $MV_3=U_3P_{3,t}$; sell notional $v$: proceeds $v(1-h_3)$, fee $vh_3$. No carry.
* **Overdraft:** $O\leftarrow O(1+OD/8760)$ hourly; interest expense $=O\cdot OD/8760$.
* **NAV:** $\text{NAV}_t=C_t+R_t+A_{1,t}+MV_{2,t}+MV_{3,t}-O_t$.
* **Float (customer-funded capital):** $\text{Float}_t=\text{AUM0}+\sum_{s\le t}F_s$ (strategy-independent).
* **Economic equity curve:** $E_t=\text{NAV}_t-\text{AUM0}-\sum_{s\le t}F_s$.  **Net PnL** $=E_T$.
* **PnL decomposition (must reconcile to $E_T$ within $1):**
$$E_T=\underbrace{\sum \text{RepoInt}}_{\text{Tier1}}+\underbrace{\sum\text{BondCarry}}_{\text{Tier2 carry}}+\underbrace{\Delta\text{MTM}_2+\Delta\text{MTM}_3}_{\text{capital PnL}}-\underbrace{\sum(\text{fee}_1+\text{fee}_2+\text{fee}_3)}_{\text{haircuts}}-\underbrace{\sum\text{ODint}}_{\text{overdraft}}-\text{purchase costs}.$$

---

## 4. Institutional Benchmarks & Comparative Backtesting Engine

### 4.1 Strategy definitions (all share the same ledger & event order)
| # | Name | Rules | Deficit resolution |
|---|---|---|---|
| B0 | 100% Cash | Never deploys | Cash only; overdraft if cash<0 |
| B1 | Naive Greedy | Everything into highest headline-yield asset (Equities) each hour; repay OD first | **Liquidity-rank order:** repo break → bonds → equities → overdraft (fixed, cost-blind) |
| B2 | Static Institutional | Target 20/30/30/20 (Cash/Repo/Bond/Equity); daily 17:00 repo top-up, 08:00 buy-only rebalancing (no sell-rebalance, haircuts would apply) | Same fixed liquidity-rank order |
| AF | AegisFlow | §2–3 | Min-cost waterfall + need-time ladder + regime |

**Fairness controls (required):** (a) identical `AUM0`, data, timing; (b) **Ablation ladder** proves alpha isn't just "a smarter waterfall": run **B2+ (static ratios with AegisFlow's waterfall)**, **AF−ladder (repo only)**, **AF−waterfall (fixed order)**, **AF−regime (no veto)**; (c) AUM0 sensitivity {3B, 5B, 10B}; (d) at AUM0 < $2.59B show unavoidable overdraft in Q4 for *all* strategies.

### 4.2 Metrics (exact definitions — `ledger/metrics.py`)
| Metric | Definition |
|---|---|
| Total Net PnL ($) | $E_T$ |
| Net Realized APY (%) | $100\cdot\dfrac{E_T}{\overline{\text{Float}}}\cdot\dfrac{8760}{N}$ (Float is strategy-independent ⇒ fair; do **not** divide by strategy NAV, which collapses for B1) |
| Max Drawdown | $\max_t(\max_{s\le t}E_s-E_t)$ in $ and as % of AUM0 |
| Overdraft count | number of distinct **episodes** (contiguous hours with $O>0$) and number of draws |
| Overdraft $ volume | $\sum$ new draws; also peak balance, overdraft-hours, interest paid |
| Total haircut penalties ($) | $\sum(\text{fee}_1+\text{fee}_2+\text{fee}_3)$ with per-tier split |
| Capital Efficiency Ratio | $\dfrac{E_T}{\sum_t \text{Float}_t\,y_{2,t}/8760}$ — share of the risk-free Tier-2 carry ceiling captured (can be negative) |
| Deployment ratio | time-avg $(R+MV_2+MV_3)/\text{NAV}$ |
| Friction drag | $(\text{haircuts}+\text{ODint})/\text{gross income}$ |
| Calmar | $E_T/\text{MDD}$ |
| Hourly Sharpe (ann.) | $\sqrt{8760}\cdot\text{mean}(\Delta E)/\text{std}(\Delta E)$ |

### 4.3 Performance requirements
* Full 4-strategy × 8,760-hour backtest **< 5 s** excluding model training (precompute forecasts to parquet; the sim loop does O(1) lookups; optional `numba`).
* Walk-forward training (LightGBM, ~50 weekly refits × 4 models) **< 120 s** on 4 CPU cores.
* Stress-test run (4 strategies, shocked data) **< 3 s** using cached model artifacts (models are *not* retrained on shocked data — they must react, that's the point).

### 4.4 Expected output artifacts
`artifacts/backtest_{AUM0}.json` (KPIs + downsampled equity curves), `artifacts/ticks_{strategy}.parquet` (8,760 rows of state), `artifacts/decisions.parquet`, `artifacts/ablations.json`, `artifacts/frontier.json`.

---

## 5. Headless API Specification (FastAPI)

**Base:** `/api`. JSON, UTF-8, ISO-8601 timestamps (`2026-03-15T17:00:00`). Money in USD floats. CORS open for the Stitch origin. All errors:
```json
{"error":{"code":"INVALID_RANGE","message":"from must be < to","details":{}}}
```
Codes: `INVALID_RANGE, UNKNOWN_STRATEGY, UNKNOWN_RUN, BAD_SHOCK_PARAM, NOT_READY`.
Strategy IDs: `baseline0_cash | baseline1_greedy | baseline2_static | aegisflow`.

### 5.1 `GET /api/health` · `GET /api/meta/config`
`/meta/config` returns config for the UI: `aum0`, `risk_mode`, frictions, dataset span (`start`,`end`,`n_hours`), strategy list with display names and colors-agnostic IDs, and the **assumption notes** (AUM0, timing convention).

### 5.2 Streaming replay
**`GET /api/stream/tick?index=1234&strategies=aegisflow,baseline2_static`** (also accepts `ts=`). Response:
```json
{
 "index": 1234, "timestamp": "2026-02-21T10:00:00",
 "market": {"repo_apy":0.0412,"bond_yield":0.0431,"bond_price":101.1,"equity_price":5033.2,
            "equity_vol_realized":0.241,"hour":10,"repo_window_open":false,"repo_mature":false},
 "flows": {"deposits":9.8e6,"withdrawals":10.4e6,"net":-6.0e5},
 "strategies": {
  "aegisflow": {
    "state":"DAYTIME_MONITOR","overlays":["NORMAL"],
    "balances":{"cash":4.1e6,"repo":0.0,"bond_mv":1.21e9,"equity_mv":0.0,"overdraft":0.0},
    "nav":2.71e9,"econ_pnl":1.92e7,"drawdown":0.0,
    "cum":{"repo_interest":1.1e6,"bond_carry":9.9e6,"capital_pnl":1.2e7,"haircuts":0.0,"od_interest":0.0},
    "action":{"type":"NONE","amount":0.0},
    "forecast":{"q50_outflow":-3.1e5,"q90_outflow":2.4e6,"q99_outflow":6.8e6},
    "gatekeeper":null
  }
 }
}
```
When `hour==17`, `gatekeeper` is non-null:
```json
{"risk_mode":"cost_optimal","buffer_usd":9.4e6,"sweep_usd":3.2e7,
 "night_drain_quantiles":{"p50":7.9e6,"p90":3.1e7,"p986":3.6e7,"p995":4.2e7},
 "expected_overdraft_hours_at_buffer":5.05,"target_overdraft_hours":5.07,
 "p_drain_exceeds_buffer":0.41,"regime":"NORMAL","calendar_class":"heavy"}
```
**`GET /api/stream/range?from=...&to=...&strategies=...&stride=1&fields=balances,nav`** → `{"stride":1,"count":N,"ticks":[ ...same tick objects, optionally field-filtered... ]}`. Max 8,760 ticks/response; `stride` downsamples (last value in bucket).
**`WS /ws/replay`** — client→server: `{"cmd":"play","speed":60,"from_index":0,"strategies":["aegisflow"]}`, `{"cmd":"pause"}`, `{"cmd":"seek","index":4000}`, `{"cmd":"speed","value":240}`. `speed` = ticks per second (1…2000). Server→client: `{"type":"tick", "payload":<tick object>}`, `{"type":"decision","payload":<decision record>}` for each decision emitted, `{"type":"eof"}`, `{"type":"error","error":{...}}`. Server batches ticks at ≤30 messages/s and sets `"batched":true` with `ticks:[…]` when speed exceeds that.

### 5.3 Backtest summary & comparison
**`GET /api/backtest/compare?aum0=3000000000&risk_mode=cost_optimal`** →
```json
{
 "run_id":"bt_3000000000_cost_optimal","aum0":3.0e9,"n_hours":8760,
 "strategies":{
  "aegisflow":{"net_pnl":6.0e7,"net_apy_pct":3.5,"max_drawdown_usd":4.3e7,"max_drawdown_pct_aum0":1.4,
    "overdraft":{"episodes":420,"draws":758,"volume_usd":9.4e8,"peak_usd":3.8e7,"hours":900,"interest_usd":8.0e4},
    "haircuts":{"total":1.9e7,"tier1":0,"tier2":1.9e7,"tier3":0},
    "capital_efficiency_ratio":0.62,"deployment_ratio":0.88,"friction_drag":0.18,"calmar":1.4,"sharpe":2.1,
    "pnl_decomposition":{"repo_interest":1.8e7,"bond_carry":5.2e7,"capital_pnl":-3.0e6,"haircuts":-1.9e7,"od_interest":-8.0e4}},
  "baseline0_cash":{...}, "baseline1_greedy":{...}, "baseline2_static":{...}
 },
 "equity_curves":{"stride":24,"timestamps":[...],"aegisflow":[...],"baseline0_cash":[...],"baseline1_greedy":[...],"baseline2_static":[...]},
 "alpha_vs":{"baseline0_cash":6.0e7,"baseline1_greedy":1.42e9,"baseline2_static":2.55e8}
}
```
(Numbers above are illustrative placeholders for schema only.)
`GET /api/backtest/ablations` → rows `{variant, net_pnl, delta_vs_aegisflow, haircuts, od_interest}`.
`GET /api/backtest/sensitivity` → AUM0 ∈ {3B,5B,10B} × strategies.
`GET /api/backtest/frontier` → price-of-safety grid (§2.3.4): `[{epsilon,K_usd,mean_buffer_usd,net_pnl,od_hours,peak_od_usd}]`.
`POST /api/backtest/run` body `{"aum0":..., "risk_mode":..., "seed":42}` → `{"run_id":"...","status":"ready"}` (synchronous; < 5 s with cache).

### 5.4 Stress-test / Chaos injection — `POST /api/simulate/stress-test`
Request:
```json
{
 "aum0": 3000000000, "seed": 42, "strategies": ["aegisflow","baseline2_static"],
 "shocks": {
  "withdrawal_multiplier": 1.5,
  "deposit_multiplier": 1.0,
  "window": {"start":"2026-06-01T00:00:00","end":"2026-06-30T23:00:00"},
  "run_event": {"start":"2026-07-14T09:00:00","duration_hours":12,"peak_multiplier":4.0,"decay":"exponential"},
  "rate_shock_bps": 150, "rate_shock_ramp_hours": 168, "rate_shock_start":"2026-05-01T00:00:00",
  "equity_crash_pct": -30, "equity_crash_start":"2026-03-01T00:00:00", "equity_crash_hours": 240
 }
}
```
Validation: `withdrawal_multiplier ∈ [0.5, 5]`, `|rate_shock_bps| ≤ 500`, `equity_crash_pct ∈ [-60, 0]`, windows within dataset.
**Shock transformer (`data/stress.py`, pure):**
* Withdrawals: $W'_t=W_t\cdot m(t)$ in window; run_event multiplier $m(t)=1+(M-1)e^{-(t-t_0)/\lambda}$ (or linear ramp); recompute `net_flow`.
* Rates: $\Delta y_t$ = parallel shift ramped linearly over `ramp_hours`; `bond_yield' = y+Δy`; **`bond_price' = bond_price·(1−D·Δy_t)`**; repo rate shifted by the same Δ (floored at 0).
* Equity: multiplicative path $P'_t=P_t\cdot(1+c\cdot s(t))$ with $c$=crash %, $s$ a smoothstep from 0→1 over `equity_crash_hours`, holding the crash level afterwards (no mean reversion unless `recovery_hours` given).
* Forecast models are **not retrained**; regime detectors must react live.
Response:
```json
{
 "run_id":"st_9f3a...","shocks_applied":{...},
 "baseline_run_id":"bt_3000000000_cost_optimal",
 "results":{"aegisflow":{"kpis":{...same as compare...},"delta_vs_unshocked":{"net_pnl":-1.2e7,"haircuts":3.0e6,"od_interest":4.1e5,"peak_overdraft":6.5e7}},
            "baseline2_static":{...}},
 "events":[{"timestamp":"2026-07-14T10:00:00","type":"STRESS_ELEVATED","strategy":"aegisflow"}],
 "equity_curves":{"stride":24,"timestamps":[...],"aegisflow":[...],"baseline2_static":[...]},
 "worst_nights":[{"date":"2026-07-14","drain_usd":9.1e7,"aegisflow_overdraft_peak":6.5e7}]
}
```
**Presets** (`GET /api/simulate/presets`): `payday_squeeze`, `holiday_rush`, `bank_run_12h`, `rate_shock_150bp`, `equity_crash_30`, `perfect_storm` (all combined).

### 5.5 Audit trail — `GET /api/logs/decisions`
Query: `strategy`, `from`, `to`, `type` (`SWEEP|REPO_BREAK|BOND_BUY|BOND_SELL|EQUITY_BUY|EQUITY_SELL|OVERDRAFT_DRAW|OVERDRAFT_REPAY|REGIME_CHANGE|VETO|NOOP_SAMPLE`), `min_amount`, `run_id`, `limit` (≤500), `cursor`. Response `{"items":[…],"next_cursor":"…","total":N}`.

### 5.6 Decision record schema (`audit/decision_log.py`)
```json
{
 "id":"dec_000812","run_id":"bt_...","timestamp":"2026-03-15T17:00:00","index":1721,
 "strategy":"aegisflow","state":"SWEEP_DECISION","overlays":["NORMAL"],
 "type":"SWEEP","amount_usd":3.2e7,
 "state_before":{"cash":4.1e7,"repo":0,"bond_mv":1.2e9,"equity_mv":0,"overdraft":0},
 "state_after":{"cash":9.4e6,"repo":3.2e7,"bond_mv":1.2e9,"equity_mv":0,"overdraft":0},
 "reason_codes":["RULE_B_COST_OPTIMAL","CALENDAR_HEAVY_DAY","FORECAST_P995_41.8M"],
 "cost_table":[{"source":"OD","unit_cost":2.05e-4,"capacity":1e18,"chosen":true},
               {"source":"T1_BREAK","unit_cost":5.03e-3,"capacity":3.2e7,"chosen":false},
               {"source":"T2_SELL","unit_cost":2.04e-2,"capacity":1.2e9,"chosen":false},
               {"source":"T3_SELL","unit_cost":1.76e-1,"capacity":0,"chosen":false}],
 "forecast":{"buffer_usd":9.4e6,"night_p995_usd":4.18e7,"target_od_hours":5.07,"expected_od_hours":5.04},
 "realized_cost_usd":0.0,
 "narrative":"17:00 sweep: kept $9.4M cash (cost-optimal: expected 5.0 overdraft-hours at the margin). Swept $32.0M to repo at 4.12% (≈$2.2K overnight yield). Friday heavy-drain night expected, P99.5 drain $41.8M covered by overdraft headroom."
}
```
Narratives are template-generated (no LLM at runtime) from reason codes + numbers. Log all non-NOOP decisions; plus 1 `NOOP_SAMPLE` per day at 12:00 to show the engine is "thinking".

### 5.7 Additional endpoints (cheap, high demo value)
* `GET /api/forecast/night?date=2026-07-03` → gatekeeper output + the 15-hour fan chart data (`p10,p50,p90,p99,actual`).
* `GET /api/ladder/state?index=...` → `{need_curve:[{tau_h,x_usd}], tau_b_h, tau_e_h, bond_target, equity_target, pool_req}`.
* `GET /api/theorems` → the three break-even calculations with current inputs (live numbers for the UI "Why" panel).

---

## 6. Agent-by-Agent Implementation Checklist (Antigravity & Flash 3.8)

### 6.0 Global preamble (paste at the top of **every** agent prompt)
```
You are implementing one module of AegisFlow, a backend-only algorithmic treasury engine.
Source of truth: PROJECT_ROADMAP.md (sections referenced below) and reference_prototype/.
RULES
1. Python >=3.11, type hints everywhere, pure functions where specified, no global mutable state.
2. NEVER write frontend code. NEVER read the CSV by hand in business logic; use data.loader.
3. Conventions in §1.3 (units, sign, timing, event order) are non-negotiable.
4. No look-ahead: decisions at row t may use rows <= t-1 only. A leakage test is mandatory for any model/feature.
5. Write tests FIRST for the stated acceptance criteria, then implement. Do not edit a test to make it pass;
   if you believe a test is wrong, stop and write the reasoning to NOTES.md.
6. Run `pytest -q` and report results. Do not proceed to the next task until all listed tests pass.
7. Keep functions small; docstrings must cite the roadmap section implemented.
8. Output: list files created/changed, test summary, and any assumptions.
```

### Task 0 — Scaffold & config
**Prompt:** *Create the repository layout in §1.2, `pyproject.toml`, Makefile (`make test`, `make backtest`, `make api`), and `configs/default.yaml` with: `aum0: 3.0e9, seed: 42, risk_mode: cost_optimal, overdraft_cap: null, guarded_cap: 25e6, epsilon: 0.005, safety_margin: 0.10, pool_days: 3, bond_burnin_days: 35, night_burnin_days: 14, night_prior_buffer: 50e6, bond_momentum_veto_bps: 30, purchase_cost_bps: 0, equity: {w_cap: 0.15, sigma_target: 0.10, gate_vol_max: 0.30, dd_gate: -0.08, breaker: 0.12, freeze_days: 30}`. Implement `config.py` (pydantic v2 models, YAML loader, env override) and `constants.py` (HOURS_PER_YEAR=8760, sweep hour 17, maturity hour 8, lock hours 15).*
**Tests:** config loads; invalid `risk_mode` raises; constants correct. **Done when:** `pytest` green, `python -c "import aegisflow"` works.

### Task 1 — Data Engine
**Prompt:** *Implement `data/loader.py` (returns a typed DataFrame, converts pct→fraction, bool flags, sets `hour`, `dow`, `dom`, `index`), `validator.py`, and `calendar.py` (heavy-day classifier: Fri/Sat or dom∈{1,2,3,15,16,17} or holiday-adjacent; US holidays 2026 incl. Jul 3 observed and Dec 25). Validator must assert: 8,760 rows, hourly contiguous, no NaN, flags only at hours 17/8 (365 each), `net == dep − wd` within $0.02, constants columns constant. Extract `FrictionConfig` (0.5/2/15 %, OD 12%) and `D_mod` from the CSV.*
**Tests:** shape/flags/net identity; first row values (deposits 6,660,184.94; repo 4.292%→0.04292); calendar class for 2026-07-03 is `heavy`; `outflow = −net`. **Done when:** validator prints the §0.1 table programmatically and matches.

### Task 2 — Ledger, Instruments & Accounting
**Prompt:** *Implement `ledger/state.py` (dataclass `PortfolioState` with C,R,r_lock,eta,U2,U3,O + cumulative counters for every PnL component), `instruments.py` (functions: `sweep`, `mature`, `break_repo`, `buy_bond`, `sell_bond`, `buy_equity`, `sell_equity`, `draw_overdraft`, `repay_overdraft`, `accrue_*`), and `engine_step.py` implementing the canonical event order of §1.3 exactly. `accounting.py` computes NAV, Float, E_t and the PnL decomposition (§3.5). Port the logic from `reference_prototype/proto.py` but structure it cleanly and make the loop numba-compatible (arrays in, arrays out).*
**Tests (hard numbers):** (a) $100M swept at 4.1% matures to $100,007,020.55 (±$0.01); (b) break $1,000,000 repo → proceeds $995,000, fee $5,000; (c) sell $1,000,000 bonds → $980,000; equities → $850,000; (d) $10M overdraft for 15 h accrues $2,054.79 (±$0.5); (e) +50 bp yield move ⇒ price index ≈ −0.96% ×100; (f) **conservation:** over 10,000 random-action steps `E_T == Σ components` within $1; (g) cash never negative after step; O ≥ 0. **Done when:** B0 backtest yields exactly $0 PnL.

### Task 3 — Baselines & Simulator Harness
**Prompt:** *Implement `strategies/base.py` (abstract `Strategy` with `init/pre/resolve/post`), the three baselines per §4.1, `sim/engine.py` (runs a Strategy over a DataFrame, returns tick arrays + counters), and `ledger/metrics.py` per §4.2 (overdraft **episodes** vs draws, Float-based APY, CER, MDD).*
**Tests:** B0 PnL = 0; with AUM0=3B results within ±5% of prototype: B1 ≈ −$1,364M, B2 ≈ −$195M; metrics unit tests on synthetic series (known MDD, known episodes). **Done when:** a table of B0/B1/B2 KPIs prints and matches the §0.5 targets.

### Task 4 — Waterfall Optimizer (+LP verifier)
**Prompt:** *Implement `optimize/waterfall.py`: given need Δ, state, and a cure-time callable $T(x)$, build the source list with unit costs and capacities (§3.1), return an ordered allocation (greedy ascending cost, ties → non-OD), supporting the overdraft cap and 5-tranche staircase for OD. Implement `lp_verify.py` using `scipy.optimize.linprog(highs)`.*
**Tests:** (property, hypothesis, 10k cases) greedy objective == LP objective (1e-6); with T=15h and repo available, chosen source is OD; with T=1,460h, bond beats OD (tie → bond); equity chosen only after all else exhausted; cap binding shifts remainder to next source; no allocation exceeds capacity. **Done when:** property tests pass and the audit `cost_table` is produced for every call.

### Task 5 — Hourly Quantile Forecaster
**Prompt:** *Implement `data/features.py` (§2.1 feature list; all features strictly from rows ≤ t−1) and `forecast/hourly_model.py` + `walkforward.py`: LightGBM quantile (0.5,0.9,0.99) + L2 mean model on target `outflow`. Expanding window, first fit after 21 days, weekly retrain. Save `artifacts/hourly_preds.parquet`. Enforce monotone quantiles. `scripts/train_walkforward.py` prints coverage and pinball tables vs seasonal-naive.*
**Tests:** **leakage test** — perturb all rows ≥ t in features and assert features at t unchanged; coverage of q50/q90/q99 within ±3pp / ±3pp / ±1.5pp of nominal on days 60–365; pinball loss beats seasonal-naive for all quantiles; q50≤q90≤q99. **Done when:** runtime < 120 s and metrics tables saved to `artifacts/forecast_report.json`.

### Task 6 — Night Path Engine & Repo Gatekeeper
**Prompt:** *Implement `forecast/night_paths.py` (night-block bootstrap of 15-vector residuals stratified by calendar class, 10,000 paths, seeded), `forecast/conformal.py` (rolling κ calibration, §2.3.2), `forecast/cure_time.py` (estimates $T_t(x)$ from simulated paths + pending repo maturity), and `optimize/repo_sizing.py` implementing **Rules A, B, C** (§2.3.3) with bisection for Rule B. Output a `GatekeeperResult` dataclass matching §5.2's `gatekeeper` JSON.*
**Tests:** on a synthetic i.i.d. normal night distribution Rule A returns the 98.61% quantile (±1%); Rule B satisfies $|\mathbb{E}[h(B)]-15r/OD|<0.05$; Rule C ≥ Rule B always; `conservative` reproduces P99.5; running-min (not terminal) is used (test with a path that dips then recovers); calibration coverage ≥ 99% of historical nights at P99.5 after day 60; determinism with fixed seed. **Done when:** in-sample B_B ∈ [$7M, $12M], B_A ∈ [$34M, $39M], B_C(P99.5) ∈ [$39M, $45M] (§0.6).

### Task 7 — Regime Detectors & Need-Time Ladder
**Prompt:** *Implement `regime/flow_regime.py` (CUSUM §2.4.3), `rate_regime.py` (momentum veto §2.4.1, z-score optional, carry-vs-duration helpers), `equity_regime.py` (EWMA realized vol from price, SMA trend, drawdown gate, circuit breaker, permanent-capital test §2.4.2), and `optimize/ladder.py` (need function with day-35 burn-in, $\tau_b$, $\tau_e$, bond/equity targets, pool_req §2.5).*
**Tests:** $\tau_b$≈7,900 h at (y=4.75%, r=4.055%); spread ≤20 bp ⇒ ∞; $\tau_e$≈2.5 yr; equity target = 0 for AUM0=3B and any day; veto fires when Δy_168 = +31 bp and not at +29 bp; CUSUM triggers on injected 4σ shocks and not on 1,000 N(0,1) draws (false-alarm <2%); realized vol on the dataset ≈ 25% (±2pp), **and the constant 18% column is never read**. **Done when:** ladder produces bond targets monotone in NAV.

### Task 8 — AegisFlow State Machine
**Prompt:** *Implement `strategies/aegisflow.py` per §3.3–3.4 composing Tasks 4–7. Maintain the state enum, overlays, estimators (d̂, night residual store), burn-in logic, and emit a `DecisionRecord` for every non-trivial action (§5.6) with reason codes, cost table, and template narrative (`audit/narrative.py`).*
**Tests:** no action uses information from row ≥ t (run with future rows scrambled — decisions identical); sweep only at hour 17; maturity handling; during burn-in no bond purchases before day 35; never buys while overdraft > 0; every sell of bonds is accompanied by a waterfall/refill reason code; **end-to-end at AUM0=3B: PnL ≥ +$55M, Tier-3 allocation ≡ 0, OD interest ≤ $0.5M, haircuts ≤ $25M.** **Done when:** AF beats B0, B1, B2 on net PnL and drawdown.

### Task 9 — Backtester, Benchmarks, Ablations, Frontier
**Prompt:** *Implement `sim/backtester.py` (runs all four strategies, writes artifacts), `benchmarks.py` (AUM0 sensitivity 3/5/10B and the sub-$2.59B demonstration), `ablations.py` (B2+, AF−ladder, AF−waterfall, AF−regime), and `frontier.py` (ε × K grid, §2.3.4). Cache by hash of (config, data).*
**Tests:** identical config ⇒ byte-identical results; ablation ordering AF ≥ AF−waterfall and AF ≥ AF−ladder at 3B; frontier monotonic: higher safety ⇒ lower or equal peak overdraft; full run < 5 s on cached forecasts. **Done when:** `artifacts/*.json` exist and `scripts/run_backtest.py` prints the §4.2 KPI table.

### Task 10 — Stress Engine
**Prompt:** *Implement `data/stress.py` (§5.4 transformer) and `sim/stress_runner.py`. Models are not retrained; load cached forecasts but **recompute features from shocked flows where the model depends on lagged flow** (so the forecaster sees the shock after it occurs — no foresight).*
**Tests:** multiplier=1 & no shocks ⇒ identical to baseline; rate shock +100 bp ⇒ bond price −1.92% at full ramp; equity −30% ⇒ final price × 0.70 relative path; withdrawal×1.5 raises total outflow by exactly 50% in window; B1/B2 degrade more than AF in `perfect_storm`; AF's `STRESS_ELEVATED` overlay triggers within 3 hours of a 4× run event. **Done when:** all presets run < 3 s each.

### Task 11 — FastAPI REST layer
**Prompt:** *Implement `api/schemas.py` (pydantic v2 models for every payload in §5), `main.py`, `routes_*.py`, `deps.py` (startup loads cached artifacts, raises `NOT_READY` otherwise). Implement endpoints §5.1, 5.2 (REST parts), 5.3, 5.4, 5.5, 5.7. Auto-generate OpenAPI; `scripts/export_openapi.py` writes `openapi.json` (for Stitch).*
**Tests (TestClient):** schema validation of every response; `from>=to` ⇒ 400 `INVALID_RANGE`; bad shock param ⇒ 422 `BAD_SHOCK_PARAM`; `/stream/tick` at hour 17 contains `gatekeeper`; pagination cursor stability; response time < 150 ms for cached endpoints. **Done when:** `openapi.json` validates and a smoke script hits every route.

### Task 12 — WebSocket Replay
**Prompt:** *Implement `api/ws.py` for `/ws/replay` per §5.2 with play/pause/seek/speed, backpressure-safe batching (≤30 msg/s), decision events interleaved at the correct tick, graceful disconnect.*
**Tests:** seek to 4000 then play ⇒ first tick index 4000; speed 2000 ⇒ batched messages; pause stops emission within 100 ms; decisions arrive with their tick; invalid command ⇒ error frame, connection stays open. **Done when:** 8,760-tick replay at speed 2000 completes in < 10 s without memory growth.

### Task 13 — Hardening, Docs & Demo Kit
**Prompt:** *Add: README with the §0 audit table and architecture diagram; `make_demo_cache.py` (precomputes everything for AUM0 {3,5,10}B); a `DEMO_SCRIPT.md` (6-minute narrative below); a determinism test; profiling report; type-check (`mypy --strict` on `ledger/` and `optimize/`).*
**Done when:** fresh clone → `make demo` → API serving in < 3 minutes; all tests green.

### Dependency order
`0 → 1 → 2 → 3` (ledger/baselines validated vs prototype) `→ 4 → 5 → 6 → 7 → 8` (AegisFlow) `→ 9 → 10 → 11 → 12 → 13`. Tasks 4 and 5 may run in parallel after Task 3; Tasks 11–12 may start against mocked artifacts once Task 9's schema is frozen.

---

## 7. Demo Narrative & Judge Q&A

### 7.1 Six-minute story
1. **The trap (60 s):** "The data hides a $2.5B/yr structural drain — capital is inventory, not a static pool. We state AUM0 explicitly."
2. **Three theorems (90 s):** overdraft 24× cheaper than cracking repo; equities need a 2.5-yr horizon; bonds only for need-time > 11 months. *Live numbers from `/api/theorems`.*
3. **Benchmark carnage (60 s):** B1 −$1.36B, B2 −$195M, B0 $0, AegisFlow ≈ +$60M; show the ablation ladder.
4. **The 17:00 gatekeeper (60 s):** fan chart for Jul 3; the dial "price of safety" (cost ≈ $0.8M/yr from cost-optimal to P99.5).
5. **Chaos (60 s):** `perfect_storm` preset — watch AegisFlow flip to `STRESS_ELEVATED`, baselines bleed.
6. **Audit (30 s):** click a decision → reason codes + cost table + narrative.

### 7.2 Likely judge questions
* *"Why isn't the buffer at P99.5 as the brief suggests?"* → Rule A/B/C; we ship P99.5 as `conservative` and quantify its cost.
* *"Why zero equities?"* → Theorem 2 + the 15% exit; filters open only with permanent capital. Expected return 10% vs 15% exit cost.
* *"Is this overfit to one year?"* → Parameters derive from closed-form break-evens; forecasts are walk-forward; burn-in rules; one year is all that exists — we say so.
* *"What if AUM is smaller?"* → sensitivity: below $2.59B the drain forces Q4 overdraft/liquidation for every strategy; AegisFlow minimizes the cost.
* *"Overdraft is cheap — isn't that unrealistic?"* → we model a cap `K` and show the frontier; real-world facilities have limits and signalling cost, which is why `guarded` exists.

---

## 8. Risks & Assumptions Register
| # | Assumption / Risk | Mitigation |
|---|---|---|
| 1 | Starting capital unspecified | `AUM0` parameter, sensitivity, stated in UI |
| 2 | Purchases are free (data gives liquidation costs only) | `purchase_cost_bps` knob; show PnL at 10 bp |
| 3 | Overdraft availability/limit unspecified | `overdraft_cap`, `risk_mode`, frontier |
| 4 | No equity dividends in data | price-return only (conservative) |
| 5 | Hourly resolution hides intra-hour deficits | Resolve shortfalls at end of hour; documented |
| 6 | Single-year sample | Walk-forward + closed-form rules; no hyper-parameter search on the full year |
| 7 | Repo break forfeits interest | Included in $c_{T1}$ via $\ell_1$ |
| 8 | Prototype numbers are indicative | Full engine acceptance uses ranges (§0.5), not point equality |

*End of PROJECT_ROADMAP.md*
