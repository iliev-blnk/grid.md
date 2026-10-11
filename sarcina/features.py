"""Feature rows for the D+1 load forecast issued at 09:00 Europe/Chisinau on D.

Leakage rules: load actuals are used only for hours that ended by 08:00 on D (the 08:00–09:00
hour may not be published at 09:00); weather comes from the freshest lead predicted at or before
the issue time (see weather.allowed_lead)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .calendar_md import is_bridge, is_holiday
from .timeutil import CHISINAU, local_day_hours
from .weather import VARS, allowed_lead, md_weighted, pick

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo(CHISINAU)
LAST_KNOWN_HOUR = 7  # on D, hours 00..07 (ending by 08:00) are treated as known at 09:00
REGIME = date(2025, 1, 1)
LOAD_FEATURES = ["hour", "dow", "month", "holiday", "bridge", "post2025", "lag_d1", "lag_d7", "mean_last24",
                 "t", "t_app", "hdh", "cdh", "rad", "cloud", "wind", "t_daymean"]


class Tables(NamedTuple):
    load: pd.DataFrame  # index (day 'YYYY-MM-DD', hour), columns load, plan, ...
    weather: pd.DataFrame  # index UTC hour, columns <var>_d<k> (Moldova population-weighted)


def load_tables(root: Path = ROOT) -> Tables:
    load = pd.read_csv(root / "data" / "load.csv.gz").set_index(["day", "hour"]).sort_index()
    w = pd.read_csv(root / "data" / "weather.csv.gz")
    w["hour_utc"] = pd.to_datetime(w["hour_utc"], utc=True)
    return Tables(load, md_weighted(w))


def issue_time(d: date) -> pd.Timestamp:
    return pd.Timestamp(datetime(d.year, d.month, d.day, 9), tz=TZ)


def valid_utc(day: date, hour: int) -> pd.Timestamp:
    """UTC start of a local wall-clock hour (the first occurrence on the autumn change day)."""
    return pd.Timestamp(datetime(day.year, day.month, day.day, hour, tzinfo=TZ, fold=0)).tz_convert("UTC")


def _known_keys(d: date) -> list[tuple[str, int]]:
    """The 24 hourly keys ending at 08:00 on D: D−1 08..23 and D 00..07."""
    prev = (d - timedelta(days=1)).isoformat()
    return [(prev, h) for h in range(LAST_KNOWN_HOUR + 1, 24)] + [(d.isoformat(), h) for h in range(LAST_KNOWN_HOUR + 1)]


def _get(load: pd.Series, key) -> float:
    try:
        return float(load[key])
    except KeyError:
        return np.nan


def load_rows(tables: Tables, d: date) -> pd.DataFrame:
    target = d + timedelta(days=1)
    tday = target.isoformat()
    load = tables.load["load"]
    plan = tables.load["plan"]
    issue = issue_time(d).tz_convert("UTC")
    known = _known_keys(d)
    last24 = np.nanmean([_get(load, k) for k in known]) if any(k in load.index for k in known) else np.nan
    rows, used = [], set()
    temps = []
    for h in local_day_hours(target, CHISINAU):
        v = valid_utc(target, h)
        k = allowed_lead(v, issue)
        wrow = tables.weather.loc[v] if v in tables.weather.index else None
        if wrow is None:
            vals, fb = {x: np.nan for x in VARS}, False
        else:
            vals, fb = pick(wrow, k)
        same_d = (d.isoformat(), h)
        d1 = same_d if h <= LAST_KNOWN_HOUR else ((d - timedelta(days=1)).isoformat(), h)
        d7 = ((target - timedelta(days=7)).isoformat(), h)
        used.update([d1, d7])
        t = vals["temperature_2m"]
        temps.append(t)
        rows.append({
            "issue_date": d, "day": tday, "hour": h, "valid_utc": v, "lead": k, "weather_fallback": fb,
            "dow": target.weekday(), "month": target.month, "holiday": int(is_holiday(target)),
            "bridge": int(is_bridge(target)), "post2025": int(target >= REGIME),
            "lag_d1": _get(load, d1), "lag_d7": _get(load, d7), "mean_last24": last24,
            "t": t, "t_app": vals["apparent_temperature"], "hdh": max(0.0, 18 - t) if t == t else np.nan,
            "cdh": max(0.0, t - 22) if t == t else np.nan, "rad": vals["shortwave_radiation"],
            "cloud": vals["cloud_cover"], "wind": vals["wind_speed_10m"],
            "y": _get(load, (tday, h)), "plan": _get(plan, (tday, h)),
        })
    df = pd.DataFrame(rows)
    df["t_daymean"] = np.nanmean(temps) if any(t == t for t in temps) else np.nan
    used.update(known)
    df.attrs["max_input"] = max(valid_utc(date.fromisoformat(k[0]), k[1]) + pd.Timedelta(hours=1) for k in used)
    return df


def max_input_time(tables: Tables, d: date) -> pd.Timestamp:
    """End (UTC) of the latest load-actual hour any feature of D's forecast reads."""
    return load_rows(tables, d).attrs["max_input"]
