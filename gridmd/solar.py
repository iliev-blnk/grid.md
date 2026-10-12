"""Hidden solar: how much PV capacity Moldova's net load reveals that the grid operator does not meter.

Per calendar month, OLS on all hours with a day fixed effect (demeaning within day):
    load_h = α_day + γ_(hour, daytype) + δ·hdh_h + ε·cdh_h − C_hidden · yield_h + e_h
and, for the metered renewables column,
    res_h = c + C_visible · yield_h + w · wind_h + e_h
where yield_h is the AC output of 1 kW of PV under that hour's actual (ERA5) weather."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .calendar_md import is_holiday
from .features import Tables, valid_utc

ROOT = Path(__file__).resolve().parents[1]
PR = 0.82
PR_BAND = (0.75, 0.90)
MIN_DAYS = 20
BOOT = 200


def pv_yield(ghi: np.ndarray, temp: np.ndarray, pr: float = PR) -> np.ndarray:
    """kW AC per kW installed: GHI/1000 · PR · (1 − 0.004·(T_cell − 25)), T_cell = T_air + GHI/800·20."""
    ghi = np.asarray(ghi, float)
    tcell = np.asarray(temp, float) + ghi / 800 * 20
    return np.clip(ghi / 1000 * pr * (1 - 0.004 * (tcell - 25)), 0, None)


def load_era5(root: Path = ROOT) -> pd.DataFrame:
    e = pd.read_csv(root / "data" / "era5.csv.gz")
    e["hour_utc"] = pd.to_datetime(e["hour_utc"], utc=True)
    return e


def national(era5: pd.DataFrame, pr: float = PR) -> pd.DataFrame:
    """Per UTC stamp: mean PV yield, mean wind-power proxy and mean temperature over the sites."""
    e = era5.copy()
    e["yield"] = pv_yield(e["ghi"], e["temp"], pr)
    e["wind"] = np.clip((e["wind100"] / 3.6 / 12) ** 3, 0, 1)
    return e.groupby("hour_utc")[["yield", "wind", "temp"]].mean()


def load_frame(tables: Tables, era5: pd.DataFrame, pr: float = PR) -> pd.DataFrame:
    """One row per local hour: load, metered RES and the weather of that hour.
    ERA5 radiation at stamp S is the mean over the hour ending at S, so local hour h (starting at
    valid_utc) is matched to the stamp valid_utc + 1 h."""
    n = national(era5, pr)
    L = tables.load.reset_index()[["day", "hour", "load", "res"]]
    stamps = [valid_utc(pd.Timestamp(d).date(), int(h)) + pd.Timedelta(hours=1) for d, h in zip(L["day"], L["hour"])]
    w = n.reindex(pd.DatetimeIndex(stamps))
    L["yield"], L["wind"], L["temp"] = w["yield"].to_numpy(), w["wind"].to_numpy(), w["temp"].to_numpy()
    L["hdh"] = np.clip(18 - L["temp"], 0, None)
    L["cdh"] = np.clip(L["temp"] - 22, 0, None)
    dt = pd.to_datetime(L["day"])
    L["daytype"] = ((dt.dt.weekday >= 5) | dt.dt.date.map(is_holiday)).astype(int)
    return L.dropna(subset=["yield"]).reset_index(drop=True)


def _complete_days(f: pd.DataFrame) -> list[str]:
    g = f.groupby("day")["load"].agg(lambda s: s.notna().sum())
    n = f.groupby("day").size()
    return sorted(g[(g == n) & (n >= 23)].index)


def _design(f: pd.DataFrame):
    hours = f["hour"].to_numpy()
    dtype = f["daytype"].to_numpy()
    dummies = np.zeros((len(f), 48))
    dummies[np.arange(len(f)), hours + 24 * dtype] = 1
    X = np.column_stack([dummies, f["hdh"], f["cdh"], f["yield"]])
    return X


def _fit(f: pd.DataFrame) -> tuple[float, float]:
    X = _design(f)
    y = f["load"].to_numpy(float)
    day = f["day"].to_numpy()
    # within-day demeaning = day fixed effects
    df = pd.DataFrame(np.column_stack([X, y]))
    dm = df - df.groupby(day).transform("mean")
    Xd, yd = dm.iloc[:, :-1].to_numpy(), dm.iloc[:, -1].to_numpy()
    beta, *_ = np.linalg.lstsq(Xd, yd, rcond=None)
    resid = yd - Xd @ beta
    return float(-beta[-1]), float(np.mean(resid ** 2))


def estimate_hidden(f: pd.DataFrame, boot: int = BOOT, seed: int = 7) -> dict | None:
    days = _complete_days(f)
    if len(days) < MIN_DAYS:
        return None
    f = f[f["day"].isin(days)].reset_index(drop=True)
    C, rss = _fit(f)
    rng = np.random.default_rng(seed)
    groups = {d: g for d, g in f.groupby("day")}
    draws = []
    for _ in range(boot):
        pick = rng.choice(days, len(days), replace=True)
        parts = [groups[d].assign(day=f"{d}#{i}") for i, d in enumerate(pick)]
        draws.append(_fit(pd.concat(parts, ignore_index=True))[0])
    lo, hi = np.percentile(draws, [5, 95])
    return {"C": C, "lo": float(lo), "hi": float(hi), "rss": rss, "n_days": len(days)}


def estimate_visible(f: pd.DataFrame) -> dict | None:
    s = f.dropna(subset=["res", "yield", "wind"])
    if s["day"].nunique() < MIN_DAYS:
        return None
    X = np.column_stack([np.ones(len(s)), s["yield"], s["wind"]])
    beta, *_ = np.linalg.lstsq(X, s["res"].to_numpy(float), rcond=None)
    return {"C": float(beta[1]), "wind_coef": float(beta[2])}


def monthly(tables: Tables, era5: pd.DataFrame, boot: int = BOOT) -> list[dict]:
    frames = {pr: load_frame(tables, era5, pr) for pr in (PR, *PR_BAND)}
    out = []
    base = frames[PR]
    for m in sorted(base["day"].str[:7].unique()):
        fm = base[base["day"].str.startswith(m)]
        h = estimate_hidden(fm, boot)
        if h is None:
            continue
        band = {}
        for pr in PR_BAND:
            hb = estimate_hidden(frames[pr][frames[pr]["day"].str.startswith(m)], boot=0)
            band[f"C_pr{int(pr * 100):03d}"] = None if hb is None else round(hb["C"], 1)
        v = estimate_visible(fm)
        out.append({"month": m, "n_days": h["n_days"],
                    "hidden": {"C": round(h["C"], 1), "lo": round(h["lo"], 1), "hi": round(h["hi"], 1), **band},
                    "visible": None if v is None else {"C": round(v["C"], 1), "wind_coef": round(v["wind_coef"], 1)}})
        print(m, out[-1]["hidden"], out[-1]["visible"], flush=True)
    return out


def write_monthly(rows: list[dict], root: Path = ROOT) -> Path:
    p = root / "data" / "solar_monthly.json"
    p.write_text(json.dumps(rows, indent=1))
    return p
