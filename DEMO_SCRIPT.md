# AegisFlow: 6-Minute Hackathon Demo Script & Judge Q&A Guide

**Challenge:** The Reserve Juggler (Quantitative Systems & Algorithmic Treasury)  
**System:** Institutional Algorithmic Treasury & Liquidity Engine (FastAPI + Google Stitch UI integration)

---

## 1. The Trap & The Institutional Dilemma (Minute 0:00 – 1:00)

> *"Judges, when you process over $20,000,000 every single hour across deposits, withdrawals, and merchant settlements, idle operational cash is a hemorrhage: at 4.2% interest, $1 billion of idle cash bleeds over $42,000,000 a year in lost yield.*
>
> *But when we audited the provided 8,760 hours of data, we discovered a massive institutional reality that naive models miss:*
> **The book suffers from a structural cumulative net liquidity drain of -$2.53 Billion over the year (-$289K/hour, -$6.93M/day). Every single month is net negative.**
>
> *In institutional banking, capital is not a static pool to 'allocate' into a pie chart — it is an inventory with a countdown timer. Without understanding the Need-Time of every dollar, conventional treasury strategies collapse."*

---

## 2. The Three Mathematical Break-Even Theorems (Minute 1:00 – 2:30)

Show the `/api/theorems` panel or live metrics:

> *"Our engine, AegisFlow, is built on three closed-form quantitative theorems that overturn naive treasury conventions:*
>
> 1. **Theorem 1 (Overdraft Dominance):**
>    *Breaking Tier 1 overnight repo early incurs a flat 0.5% fee. At ~4.1% APY, overnight interest on a 15-hour lockup is only 0.007%. A 0.5% break fee is 72x larger than the interest earned!*
>    *However, the 12% APR central-bank overdraft facility costs only $0.12 \times \frac{15}{8760} = 0.0205\%$ for a 15-hour bridge until 08:00 repo release.*
>    **Emergency overdraft is 24.4x cheaper than cracking Tier 1 repo!** *Our waterfall optimizer exploits this: shortfalls that cure in morning maturity are bridged via overdraft, saving millions in forfeited penalties.*
>
> 2. **Theorem 2 (The Equity Horizon Trap):**
>    *Liquidating equities carries a punishing 15.0% fire-sale slippage fee. The break-even holding period for equities vs bonds is:*
>    $$\tau_e = \frac{h_3 - h_2}{\mu_3 - y_2} = \frac{15\% - 2\%}{10\% - 4.75\%} \approx 2.48\text{ years}$$
>    *In a draining book over a 1-year horizon, equities are structurally uneconomic. Furthermore, our EWMA realized volatility filter and trend detector correctly diagnosed the -36.6% equity bear market, vetoing equity exposure entirely and preventing over $1 Billion in losses.*
>
> 3. **Theorem 3 (The Need-Time Bond Ladder):**
>    *Bonds incur a 2.0% market liquidation haircut. With a ~2.2% spread over the liquid repo pool, bonds take 10.8 months (~7,900 hours) to amortize their liquidation cost. AegisFlow sizes its bond investments strictly for capital that will not be needed for at least 11 months."*

---

## 3. Benchmark Carnage vs AegisFlow Alpha (Minute 2:30 – 3:30)

Show the Benchmark Comparison Table (`/api/backtest/compare`):

| Strategy | Net PnL ($) | Net Realized APY | Max Drawdown | Haircuts Paid | Overdraft Interest |
|---|---|---|---|---|---|
| **Baseline 0 (100% Cash Buffer)** | $0.00 | 0.00% | $0.00 | $0.00 | $0.00 |
| **Baseline 1 (Naive Greedy Yield Chaser)** | **-$1,364,160,830** | -76.16% | $1,538,357,729 | $1,164,886,876 | $318,349 |
| **Baseline 2 (Static 20/30/30/20)** | **-$203,336,347** | -11.35% | $263,450,645 | $62,506,508 | $2,789,970 |
| **AegisFlow (Our Engine)** | **+$61,367,359** | **+3.43%** | **$30,574,755** | **$12,132,061** | **$457,493** |

> *"Look at the results:  
> - Baseline 1 (Greedy) loses **$1.36 Billion** from equity crashes and forced 15% haircuts.  
> - Baseline 2 (Static Institutional) loses **$203 Million** due to equity drawdown and fixed rebalancing haircuts.  
> - **AegisFlow generates +$61.37 Million in pure economic PnL (3.43% Realized APY) with over $1.425 Billion in alpha vs Baseline 1 and $264.7 Million in alpha vs Baseline 2!**"*

Show the Ablation Ladder:
- Full AegisFlow: **+$61.4M**
- AF without Bond Ladder: **+$45.6M** ($\Delta = -\$15.7M$ proof of ladder alpha)
- AF with Fixed Liquidity-Rank Waterfall: **+$43.1M** ($\Delta = -\$18.2M$ proof of knapsack optimizer alpha)

---

## 4. The 17:00 Repo Gatekeeper & The Price-of-Safety Frontier (Minute 3:30 – 4:30)

Show `/api/stream/tick?index=17` and `/api/backtest/frontier`:

> *"Every day at 17:00, our Night Path Engine simulates 2,000 paths using a stratified block bootstrap of 15-hour residual vectors. This explicitly preserves the 0.695 serial autocorrelation that an i.i.d. model destroys.
>
> Crucially, we don't dogmatically enforce a single buffer rule: we give the treasury committee a dial via our **Price-of-Safety Frontier**:
> - In `cost_optimal` mode, we solve for the margin where expected overdraft hours equal $\frac{15 \cdot r}{OD} \approx 5.07$ hours, holding a ~$10M buffer.
> - In `conservative` mode, we enforce zero overdraft reliance with a full P99.5 buffer (~$41.8M).
> - And we show that moving from cost-optimal to P99.5 costs only ~$800K/year in forgone repo yield, letting risk executives choose their exact risk-return tradeoff."*

---

## 5. Chaos Injection / Stress Testing (Minute 4:30 – 5:30)

Hit `POST /api/simulate/stress-test` with the `perfect_storm` preset:
- +40% withdrawals
- +150 bps sovereign rate spike
- -30% equity crash
- 4.0x acute bank run event

> *"When chaos strikes, AegisFlow does not retrain models with lookahead bias. Its CUSUM flow detector automatically trips into `STRESS_ELEVATED`, scaling up cash buffers, freezing bond purchases, and safely absorbing the shock while static strategies suffer catastrophic overdraft cascades."*

---

## 6. Audit Trail & Institutional Governance (Minute 5:30 – 6:00)

Show `GET /api/logs/decisions`:
> *"Every single dollar moved, swept, liquidated, or drawn is immutably recorded with complete reason codes, the knapsack cost table, and human-readable compliance narratives for executive audit."*

---

## Likely Judge Questions & Answers

1. **"Why didn't you invest in Tier 3 Equities at all?"**  
   *Answer:* "Theorem 2: The 15.0% liquidation haircut requires a 2.48-year horizon to beat bonds. Because the dataset has a $2.53B structural drain, any equity bought would inevitably be liquidated at a 15% fire-sale penalty. Furthermore, equities crashed -36.6% peak-to-trough; our trend and EWMA realized vol filters correctly vetoed entry."

2. **"Why is overdraft considered a primary bridge tool?"**  
   *Answer:* "Theorem 1: Overdraft at 12% APR costs only 0.0205% for a 15-hour overnight bridge. Breaking repo costs a flat 0.50% (24x more). For shortfalls curing at 08:00 morning maturity, overdraft is the mathematically optimal choice. In guarded mode, we cap overdraft at $25M and show the exact cost frontier."

3. **"Is the system free of lookahead bias?"**  
   *Answer:* "100% causal. All features at row $t$ are constructed from rows $\le t-1$. We enforce this with an automated leakage unit test that perturbs all future rows and asserts zero change in row $t$ features. All models are trained in expanding walk-forward windows with a 21-day burn-in."
