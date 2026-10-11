from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CHISINAU = "Europe/Chisinau"
BERLIN = "Europe/Berlin"


def _exists(day: date, hour: int, tz: ZoneInfo) -> bool:
    local = datetime(day.year, day.month, day.day, hour, tzinfo=tz)
    back = local.astimezone(timezone.utc).astimezone(tz)
    return back.replace(tzinfo=None) == local.replace(tzinfo=None)


def local_day_hours(day: date, tz: str) -> list[int]:
    """Wall-clock hour labels of a local day: 23 on spring-forward days, 24 otherwise
    (the repeated autumn hour is one label, as in the Moldelectrica archive)."""
    z = ZoneInfo(tz)
    return [h for h in range(24) if _exists(day, h, z)]


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)
