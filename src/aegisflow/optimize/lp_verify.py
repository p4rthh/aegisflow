"""Linear Programming verifier for the waterfall optimization.

See PROJECT_ROADMAP.md §3.1 & Task 4.
Uses scipy.optimize.linprog(method='highs') to prove mathematical optimality.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.optimize import linprog
from aegisflow.types import CostSource


def solve_lp_waterfall(need: float, sources: List[CostSource]) -> Tuple[float, np.ndarray]:
    """Formulate and solve LP:
    
    min sum_s c_s * x_s
    s.t. sum_s x_s == need
         0 <= x_s <= cap_s
    
    Returns (min_cost, allocation_array).
    """
    if need <= 0.0 or len(sources) == 0:
        return 0.0, np.zeros(len(sources))

    c = np.array([s.unit_cost for s in sources], dtype=np.float64)
    bounds = [(0.0, s.capacity if np.isfinite(s.capacity) else None) for s in sources]
    
    # Equality constraint: sum(x_s) == need
    A_eq = np.ones((1, len(sources)), dtype=np.float64)
    b_eq = np.array([need], dtype=np.float64)

    # If total capacity is less than need, solve with <= capacity
    total_cap = sum(s.capacity for s in sources if np.isfinite(s.capacity))
    has_infinite_cap = any(not np.isfinite(s.capacity) for s in sources)
    
    if not has_infinite_cap and total_cap < need:
        # Relax to maximum possible allocation
        b_eq = np.array([total_cap], dtype=np.float64)

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"LP waterfall solve failed: {res.message}")

    return float(res.fun), res.x
