"""Calendar and holiday features for treasury flow seasonality.

See PROJECT_ROADMAP.md §1.2, §2.1 & Task 1.
"""

from datetime import datetime, date, timedelta
from typing import Set
import holidays
import pandas as pd


def get_us_holidays_2026() -> Set[date]:
    """Return set of US holidays for 2026 including observed days."""
    us_holidays = holidays.US(years=2026)
    # Ensure July 3, 2026 (Independence Day observed on Friday since July 4 is Saturday)
    # and Christmas Dec 25 are included
    holiday_dates = set(us_holidays.keys())
    holiday_dates.add(date(2026, 7, 3))
    holiday_dates.add(date(2026, 12, 25))
    holiday_dates.add(date(2026, 1, 1))
    return holiday_dates


def is_heavy_drain_calendar(dt: datetime | pd.Timestamp) -> bool:
    """Classify if a date/timestamp falls into a heavy-drain calendar regime.
    
    Conditions per §2.3.2 & Task 1:
    - Friday (dow == 4) or Saturday (dow == 5)
    - Day of month in {1, 2, 3, 15, 16, 17} (payday bill-pay/settlement waves)
    - Adjacent to a major US holiday (+/- 1 day)
    """
    d = dt.date() if isinstance(dt, (datetime, pd.Timestamp)) else dt
    dow = dt.weekday() if hasattr(dt, 'weekday') else dt.dayofweek
    dom = dt.day

    if dow in (4, 5):  # Friday, Saturday
        return True
    if dom in (1, 2, 3, 15, 16, 17):
        return True

    us_hols = get_us_holidays_2026()
    if d in us_hols:
        return True
    if (d + timedelta(days=1)) in us_hols or (d - timedelta(days=1)) in us_hols:
        return True

    return False
