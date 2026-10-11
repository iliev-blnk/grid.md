"""Moldelectrica operative archive: 15-min load, operator plan, generation and flows."""

from __future__ import annotations

import calendar
import io
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .http import fetch_bytes

URL = "https://moldelectrica.md/utils/archive2.php?id=table&type=csv&date1={d1}&date2={d2}"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "me"
COLUMNS = {
    "Date / Time": "ts", "Load": "load", "Load Shedule": "plan", "Generation": "gen",
    "Generation Shedule": "gen_plan", "TPP": "tpp", "HPP": "hpp", "RES": "res", "MD-UA": "md_ua",
    "MD-RO": "md_ro", "Balance": "balance", "Balance Shedule": "balance_plan",
}
ZERO_IS_MISSING = ["load", "plan"]


class MoldelectricaError(Exception):
    def __init__(self, date1: str, reason: str):
        super().__init__(f"moldelectrica {date1}: {reason}")
        self.date1, self.reason = date1, reason


def parse_csv(text: str) -> pd.DataFrame:
    """15-min rows; `ts` = naive local wall-clock interval start. Zeros in load/plan → NaN."""
    df = pd.read_csv(io.StringIO(text), sep=";")
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise MoldelectricaError("csv", f"missing columns: {', '.join(missing)}")
    df = df[list(COLUMNS)].rename(columns=COLUMNS)
    df["ts"] = pd.to_datetime(df["ts"], format="%Y-%m-%d %H:%M")
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    for c in ZERO_IS_MISSING:
        df.loc[df[c] <= 0, c] = np.nan
    return df.drop_duplicates("ts").sort_values("ts").reset_index(drop=True)


def fetch_month(year: int, month: int, cache: bool = True) -> str:
    tag = f"{year}-{month:02d}"
    path = RAW / f"{tag}.csv"
    last = calendar.monthrange(year, month)[1]
    finished = date(year, month, last) < date.today()
    if cache and finished and path.exists():
        return path.read_text(encoding="utf-8")
    raw = fetch_bytes(URL.format(d1=f"{tag}-01", d2=f"{tag}-{last:02d}"))
    try:
        z = zipfile.ZipFile(io.BytesIO(raw))
        text = z.read(z.namelist()[0]).decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, IndexError) as e:
        raise MoldelectricaError(tag, f"not a zip archive ({len(raw)} bytes)") from e
    if cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


def hourly(df15: pd.DataFrame) -> pd.DataFrame:
    """Hourly means indexed by (local day 'YYYY-MM-DD', wall-clock hour); only hours with 4 quarters."""
    d = df15.copy()
    d["day"] = d["ts"].dt.strftime("%Y-%m-%d")
    d["hour"] = d["ts"].dt.hour
    g = d.groupby(["day", "hour"])
    out = g[list(COLUMNS.values())[1:]].mean()
    out["n"] = g.size()
    return out[out["n"] == 4]


def build_load(start: date, end: date, out: Path | None = None) -> pd.DataFrame:
    months = pd.period_range(start, end, freq="M")
    frames = [parse_csv(fetch_month(p.year, p.month)) for p in months]
    df = pd.concat(frames).drop_duplicates("ts").sort_values("ts")
    h = hourly(df).reset_index()
    h = h[(h["day"] >= start.isoformat()) & (h["day"] <= end.isoformat())]
    out = out or ROOT / "data" / "load.csv.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    h.to_csv(tmp, index=False, compression={"method": "gzip", "mtime": 0})
    tmp.replace(out)
    return h
