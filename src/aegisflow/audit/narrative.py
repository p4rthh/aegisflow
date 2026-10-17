"""Template narrative generator for institutional audit logging.

See PROJECT_ROADMAP.md §5.6 & Task 8.
Generates human-readable compliance and executive explanations without runtime LLM latency.
"""

from typing import Dict, Any, List


def generate_narrative(
    action_type: str,
    amount_usd: float,
    state_before: Dict[str, float],
    state_after: Dict[str, float],
    reason_codes: List[str],
    forecast: Dict[str, Any],
) -> str:
    """Generate professional treasury audit narrative from decision metadata."""
    if action_type == "SWEEP":
        buffer_usd = forecast.get("buffer_usd", 0.0)
        p995 = forecast.get("night_p995_usd", 0.0)
        target_h = forecast.get("target_od_hours", 5.07)
        exp_h = forecast.get("expected_od_hours", 5.0)
        mode = forecast.get("risk_mode", "cost_optimal")
        is_heavy = "CALENDAR_HEAVY_DAY" in reason_codes

        heavy_str = "Heavy-drain calendar day detected. " if is_heavy else "Normal liquidity conditions. "
        return (
            f"17:00 Sweep ({mode}): Retained ${buffer_usd/1e6:.2f}M operational cash buffer "
            f"(marginal expected overdraft {exp_h:.2f}h vs target {target_h:.2f}h). "
            f"Swept ${amount_usd/1e6:.2f}M to overnight repo. {heavy_str}"
            f"P99.5 tail-risk drain is ${p995/1e6:.2f}M."
        )

    elif action_type == "BOND_BUY":
        tgt = forecast.get("bond_target", 0.0)
        spread = forecast.get("spread_bps", 0.0)
        return (
            f"08:00 Need-Time Ladder: Deployed ${amount_usd/1e6:.2f}M into 2Y Sovereign Bonds "
            f"towards strategic target ${tgt/1e6:.2f}M (Yield spread: +{spread:.1f} bps above repo). "
            f"Rate momentum veto clear."
        )

    elif action_type == "BOND_SELL":
        reason = "WATERFALL_SHORTFALL" if "WATERFALL_SHORTFALL" in reason_codes else "POOL_REFILL"
        fee = amount_usd * 0.02
        net = amount_usd - fee
        return (
            f"Liquidated ${amount_usd/1e6:.2f}M bonds to fund {reason}. "
            f"Delivered net ${net/1e6:.2f}M proceeds after 2.0% market haircut (${fee/1e6:.3f}M)."
        )

    elif action_type == "OVERDRAFT_DRAW":
        exp_cure = forecast.get("expected_cure_hours", 0.0)
        return (
            f"Drew ${amount_usd/1e6:.2f}M from emergency overdraft facility. "
            f"Cheapest bridge for expected {exp_cure:.1f}h recovery (Cost: 0.02% vs 0.5% repo break)."
        )

    elif action_type == "OVERDRAFT_REPAY":
        return f"Repaid ${amount_usd/1e6:.2f}M outstanding overdraft from inbound liquidity."

    elif action_type == "REGIME_CHANGE":
        regime = forecast.get("new_regime", "STRESS_ELEVATED")
        return f"Flow CUSUM threshold tripped: Entered {regime} state. Tightened cash buffer and suspended purchases."

    return f"Executed {action_type} of ${amount_usd/1e6:.2f}M under reasons: {', '.join(reason_codes)}."
