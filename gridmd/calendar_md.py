from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import holidays


@lru_cache(maxsize=None)
def _md(year: int) -> frozenset[date]:
    return frozenset(holidays.country_holidays("MD", years=[year]).keys())


def is_holiday(day: date) -> bool:
    return day in _md(day.year)


def is_bridge(day: date) -> bool:
    """A working day between a public holiday and the weekend: a Monday before a Tuesday holiday,
    or a Friday after a Thursday holiday."""
    if day.weekday() == 0:
        return is_holiday(day + timedelta(days=1))
    if day.weekday() == 4:
        return is_holiday(day - timedelta(days=1))
    return False
