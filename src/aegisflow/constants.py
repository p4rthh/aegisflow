"""Global constants for AegisFlow Engine.

See PROJECT_ROADMAP.md §1.3.
"""

HOURS_PER_YEAR: int = 8760
TOTAL_DATASET_HOURS: int = 8760

# Hourly event triggers
REPO_SWEEP_HOUR: int = 17       # 17:00 daily
REPO_MATURE_HOUR: int = 8       # 08:00 next morning
REPO_LOCK_HOURS: int = 15       # 15 hours lockup (17, 18, ..., 07)

# Default market constants (if not dynamically extracted from CSV)
DEFAULT_TIER1_HAIRCUT: float = 0.005    # 0.5% early break penalty
DEFAULT_TIER2_HAIRCUT: float = 0.020    # 2.0% bond liquidation haircut
DEFAULT_TIER3_HAIRCUT: float = 0.150    # 15.0% equity fire-sale haircut
DEFAULT_OVERDRAFT_APR: float = 0.120    # 12.0% overdraft APR
DEFAULT_BOND_DURATION: float = 1.92     # 2Y sovereign bond modified duration

# Breakeven durations in hours (Theorem 1: h* = haircut / (OD/8760))
BREAKEVEN_HOURS_REPO: float = (0.005 / 0.120) * HOURS_PER_YEAR    # 365.0 hours
BREAKEVEN_HOURS_BOND: float = (0.020 / 0.120) * HOURS_PER_YEAR    # 1460.0 hours
BREAKEVEN_HOURS_EQUITY: float = (0.150 / 0.120) * HOURS_PER_YEAR  # 10950.0 hours
