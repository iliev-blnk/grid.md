"""Open-Meteo Previous Runs: for each valid hour, the values predicted 24, 48 and 72 h before it
(`_previous_day1..3`). A forecast issued at time T may only use leads k with valid − 24k h ≤ T."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .http import fetch_json

URL = ("https://previous-runs-api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
       "&hourly={hourly}&start_date={start}&end_date={end}&timezone=GMT")
LEADS = (1, 2, 3)
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
    """UTC-hour index; one column per variable and lead: `<var>_d1`, `<var>_d2`, `<var>_d3`."""
    h = js["hourly"]
    idx = pd.to_datetime(h["time"], utc=True)
    out = pd.DataFrame(index=idx)
    for v in VARS:
        for k in LEADS:
            out[f"{v}_d{k}"] = pd.Series(h.get(f"{v}_previous_day{k}", [None] * len(idx)), index=idx, dtype=float)
    out.index.name = "hour_utc"
    return out


def allowed_lead(valid_utc: pd.Timestamp, issue_utc: pd.Timestamp) -> int:
    """Smallest lead k (days) whose prediction (made at valid − 24k h) is not after the issue time."""
    for k in LEADS:
        if valid_utc - pd.Timedelta(hours=24 * k) <= issue_utc:
            return k
    raise ValueError(f"no lead ≤ {LEADS[-1]} days covers {valid_utc} from {issue_utc}")


def pick(row: pd.Series, lead: int) -> tuple[dict[str, float], bool]:
    """Values at `lead`, falling back to older leads where missing. Returns (values, used_fallback)."""
    vals, fb = {}, False
    for v in VARS:
        x = np.nan
        for k in LEADS[LEADS.index(lead):]:
            x = row[f"{v}_d{k}"]
            if not np.isnan(x):
                fb |= k != lead
                break
        vals[v] = x
    return vals, fb


def fetch_site(name: str, start: date, end: date, fetch=fetch_json) -> pd.DataFrame:
    lat, lon, _ = SITES[name]
    hourly = ",".join(f"{v}_previous_day{k}" for v in VARS for k in LEADS)
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
    """Population-weighted Moldova means per UTC hour and lead (NaN where any site is missing)."""
    w = weather if "hour_utc" in weather.columns else weather.reset_index()
    cols = [f"{v}_d{k}" for v in VARS for k in LEADS]
    wt = w["site"].map({k: v[2] for k, v in SITES.items()}).to_numpy()
    num = w[cols].mul(wt, axis=0).groupby(w["hour_utc"]).sum(min_count=len(SITES))
    return num / sum(v[2] for v in SITES.values())
