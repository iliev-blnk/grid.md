"""Open-Meteo historical archive (ERA5 reanalysis): actual hourly weather, for estimating the past."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .http import fetch_json
from .tables import merge_recent, write_atomic

URL = ("https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start}"
       "&end_date={end}&hourly=shortwave_radiation,temperature_2m,cloud_cover,wind_speed_100m&timezone=GMT")
ERA5_SITES: dict[str, tuple[float, float]] = {
    "chisinau": (47.01, 28.86), "balti": (47.76, 27.93), "cahul": (45.90, 28.19),
    "ungheni": (47.21, 27.80), "comrat": (46.30, 28.66), "soroca": (48.16, 28.30),
}
ROOT = Path(__file__).resolve().parents[1]


def parse_archive(js: dict) -> pd.DataFrame:
    """UTC hour index (value = mean over the hour ending at the stamp for radiation)."""
    h = js["hourly"]
    df = pd.DataFrame({
        "ghi": pd.Series(h["shortwave_radiation"], dtype=float).to_numpy(),
        "temp": pd.Series(h["temperature_2m"], dtype=float).to_numpy(),
        "cloud": pd.Series(h["cloud_cover"], dtype=float).to_numpy(),
        "wind100": pd.Series(h["wind_speed_100m"], dtype=float).to_numpy(),
    }, index=pd.to_datetime(h["time"], utc=True))
    df.index.name = "hour_utc"
    return df


def build_era5(start: date, end: date, out: Path | None = None, merge: bool = False, fetch=fetch_json) -> pd.DataFrame:
    frames = []
    for site, (lat, lon) in ERA5_SITES.items():
        frames.append(parse_archive(fetch(URL.format(lat=lat, lon=lon, start=start, end=end))).assign(site=site))
    df = pd.concat(frames).reset_index()
    df["hour_utc"] = df["hour_utc"].astype(str)
    out = out or ROOT / "data" / "era5.csv.gz"
    if merge and out.exists():
        df = merge_recent(pd.read_csv(out), df, key=["hour_utc", "site"])
    write_atomic(df, out)
    return df
