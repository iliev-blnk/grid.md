"""Open-Meteo Previous Runs: weather forecasts as issued ~1 day (fallback ~2 days) before each hour."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .http import fetch_json

URL = ("https://previous-runs-api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
       "&hourly={hourly}&start_date={start}&end_date={end}&timezone=GMT")
VARS = ["temperature_2m", "apparent_temperature", "shortwave_radiation", "cloud_cover", "wind_speed_10m"]
# name: (lat, lon, population weight)
SITES: dict[str, tuple[float, float, float]] = {
    "chisinau": (47.01, 28.86, 0.55),
    "balti": (47.76, 27.93, 0.15),
    "cahul": (45.90, 28.19, 0.15),
    "ungheni": (47.21, 27.80, 0.15),
}
ROOT = Path(__file__).resolve().parents[1]


def parse_previous_runs(js: dict) -> pd.DataFrame:
    h = js["hourly"]
    idx = pd.to_datetime(h["time"], utc=True)
    out = pd.DataFrame(index=idx)
    fb = np.zeros(len(idx), bool)
    for v in VARS:
        d1 = pd.Series(h[f"{v}_previous_day1"], index=idx, dtype=float)
        d2 = pd.Series(h.get(f"{v}_previous_day2", [None] * len(idx)), index=idx, dtype=float)
        use2 = d1.isna() & d2.notna()
        out[v] = d1.where(~use2, d2)
        fb |= use2.to_numpy()
    out["fallback"] = fb
    out.index.name = "hour_utc"
    return out


def fetch_site(name: str, start: date, end: date, fetch=fetch_json) -> pd.DataFrame:
    lat, lon, _ = SITES[name]
    hourly = ",".join(f"{v}_previous_day{k}" for v in VARS for k in (1, 2))
    df = parse_previous_runs(fetch(URL.format(lat=lat, lon=lon, hourly=hourly, start=start, end=end)))
    return df.assign(site=name)


def build_weather(start: date, end: date, out: Path | None = None) -> pd.DataFrame:
    df = pd.concat([fetch_site(s, start, end) for s in SITES]).reset_index()
    out = out or ROOT / "data" / "weather.csv.gz"
    tmp = out.with_suffix(".tmp")
    df.to_csv(tmp, index=False, compression={"method": "gzip", "mtime": 0})
    tmp.replace(out)
    return df


def md_weighted(weather: pd.DataFrame) -> pd.DataFrame:
    """Population-weighted Moldova means per UTC hour (NaN where any site is missing)."""
    w = weather.copy()
    w["w"] = w["site"].map({k: v[2] for k, v in SITES.items()})
    if "hour_utc" not in w.columns:
        w = w.reset_index()
    g = w.groupby("hour_utc")
    out = pd.DataFrame({v: g.apply(lambda x, v=v: (x[v] * x["w"]).sum(min_count=len(SITES)) / x["w"].sum(),
                                   include_groups=False) for v in VARS})
    out["fallback"] = g["fallback"].any()
    return out
