"""Equity Regime and Risk Filters for Tier 3 Equities.

See PROJECT_ROADMAP.md §2.4.2 & Task 7.
"""

from typing import List, Tuple
import numpy as np
from aegisflow.constants import HOURS_PER_YEAR


class EquityRegimeDetector:
    """Rigorous gatekeeper and volatility estimator for Tier 3 Equities."""

    def __init__(
        self,
        gate_vol_max: float = 0.30,
        dd_gate: float = -0.08,
        breaker_dd: float = 0.12,
        freeze_hours: int = 720,  # 30 days
        ewma_decay: float = 0.97,
    ):
        self.gate_vol_max = gate_vol_max
        self.dd_gate = dd_gate
        self.breaker_dd = breaker_dd
        self.freeze_hours = freeze_hours
        self.ewma_decay = ewma_decay

        self.price_history: List[float] = []
        self.log_returns: List[float] = []
        self.ewma_var: float = (0.20 ** 2) / HOURS_PER_YEAR  # initialized to ~20% ann vol
        self.peak_price_since_buy: float = 0.0
        self.freeze_timer: int = 0

    def update(self, current_price: float) -> float:
        """Update price buffer and compute EWMA annualized realized volatility.
        
        DO NOT use the constant tier3_stock_volatility_pct column!
        """
        if len(self.price_history) > 0:
            last_p = self.price_history[-1]
            ret = np.log(current_price / last_p)
            self.log_returns.append(ret)
            # EWMA variance update
            self.ewma_var = self.ewma_decay * self.ewma_var + (1.0 - self.ewma_decay) * (ret ** 2)

        self.price_history.append(current_price)

        if self.freeze_timer > 0:
            self.freeze_timer -= 1

        annualized_vol = np.sqrt(self.ewma_var * HOURS_PER_YEAR)
        return float(annualized_vol)

    def is_eligible_for_entry(
        self,
        current_price: float,
        nav: float,
        need_2_5yr: float,
        is_stress_elevated: bool,
    ) -> Tuple[bool, str]:
        """Check all five institutional gates (§2.4.2) for equity purchases.
        
        All must pass:
          1. Permanent-capital test: NAV - Need(2.5y) > 0
          2. Trend: price > SMA(30d) and SMA(30d) > SMA(90d)
          3. Drawdown gate: max drawdown from 90d high >= -8%
          4. Realized vol <= 30%
          5. Not in STRESS_ELEVATED
        """
        # 1. Permanent-capital test (Theorem 2)
        if (nav - need_2_5yr) <= 0.0:
            return False, f"PERMANENT_CAPITAL_FAIL (NAV ${nav/1e6:.1f}M <= Need(2.5y) ${need_2_5yr/1e6:.1f}M)"

        # Check circuit breaker freeze
        if self.freeze_timer > 0:
            return False, f"CIRCUIT_BREAKER_FROZEN ({self.freeze_timer} hours remaining)"

        # 5. Stress overlay check
        if is_stress_elevated:
            return False, "FLOW_STRESS_ELEVATED_VETO"

        n_p = len(self.price_history)
        if n_p < 2160:  # 90 days = 2160 hours
            return False, "HISTORY_WARMUP"

        p_array = np.array(self.price_history[-2160:])
        sma_30d = float(np.mean(p_array[-720:]))
        sma_90d = float(np.mean(p_array))

        # 2. Trend filter
        if not (current_price > sma_30d and sma_30d > sma_90d):
            return False, f"TREND_BEARISH (price={current_price:.1f}, sma30={sma_30d:.1f}, sma90={sma_90d:.1f})"

        # 3. Drawdown gate from 90d high
        high_90d = float(np.max(p_array))
        dd = (current_price / high_90d) - 1.0
        if dd < self.dd_gate:
            return False, f"DRAWDOWN_GATE_BREACHED ({dd*100:.1f}% < {self.dd_gate*100:.1f}%)"

        # 4. Realized volatility cap
        ann_vol = np.sqrt(self.ewma_var * HOURS_PER_YEAR)
        if ann_vol > self.gate_vol_max:
            return False, f"VOLATILITY_TOO_HIGH ({ann_vol*100:.1f}% > {self.gate_vol_max*100:.1f}%)"

        return True, "EQUITY_ELIGIBLE"
