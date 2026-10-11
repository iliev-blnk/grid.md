"""Backtest: tune on 2025-04..09 (train from 2022-01-15), test once on issue dates 2025-10-01..2026-09-30
with a monthly expanding refit. Benchmarks: the operator plan, the bias-corrected plan, and
same-hour-last-week with empirical error quantiles."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .baselines import naive_quantiles
from .forecaster import CONFORMAL_WEEKS, LoadForecaster, conformal_shift
from .features import LOAD_FEATURES, load_rows, load_tables
from .metrics import QUANTILES, coverage, mae, mape, pinball
from .models import QuantileModel
from .timeutil import daterange

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
TRAIN_START = date(2022, 1, 15)
VAL = (date(2025, 4, 1), date(2025, 9, 30))
TEST = (date(2025, 10, 1), date(2026, 9, 30))
ROLL_START = date(2025, 1, 1)  # refits from here so the conformal shift has history; only TEST is scored
GRID = [dict(num_leaves=a, learning_rate=b, min_data_in_leaf=c) for a in (15, 31, 63) for b in (0.03, 0.1) for c in (20, 100)]
MAX_TREES = 2000
NAIVE_WEEKS = 8


# ---------- dataset ----------

def dataset(start: date = TRAIN_START, end: date = TEST[1], cache: bool = True) -> pd.DataFrame:
    path = RESEARCH / "dataset.csv.gz"
    if cache and path.exists():
        ds = pd.read_csv(path, parse_dates=["valid_utc"])
        ds["issue_date"] = pd.to_datetime(ds["issue_date"]).dt.date
        return ds
    t = load_tables()
    ds = pd.concat([load_rows(t, d) for d in daterange(start, end)], ignore_index=True)
    ds = _add_benchmarks(ds, t)
    RESEARCH.mkdir(exist_ok=True)
    ds.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
    return ds


def _add_benchmarks(ds: pd.DataFrame, t) -> pd.DataFrame:
    """Bias-corrected plan: plan − mean(plan − load) over the 28 complete days before the issue date."""
    hist = t.load[["load", "plan"]].copy()
    hist["err"] = hist["plan"] - hist["load"]
    daily = hist.groupby(level="day")["err"].mean()
    daily.index = pd.to_datetime(daily.index)
    bias = daily.rolling("28D", min_periods=7).mean()  # window ending on (and including) each day
    ds = ds.copy()
    prev = pd.to_datetime(ds["issue_date"]) - pd.Timedelta(days=1)  # last complete day at 09:00 on D
    ds["plan_bc"] = ds["plan"] - prev.map(bias).to_numpy()
    return ds


# ---------- splits ----------

def _d(ds) -> pd.Series:
    return ds["issue_date"]


def tune_split(ds: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    d = _d(ds)
    train = (d >= TRAIN_START) & (d <= VAL[0] - timedelta(days=1))
    val = (d >= VAL[0]) & (d <= VAL[1])
    return train, val


def test_months() -> list[date]:
    return [p.to_timestamp().date() for p in pd.period_range(TEST[0], TEST[1], freq="M")]


def rolling_months() -> list[date]:
    return [p.to_timestamp().date() for p in pd.period_range(ROLL_START, TEST[1], freq="M")]


def train_mask(ds: pd.DataFrame, month_start: date) -> pd.Series:
    """Rows whose target day was fully observed before the refit at the start of the month."""
    return (_d(ds) >= TRAIN_START) & (ds["day"] < month_start.isoformat())


def predict_mask(ds: pd.DataFrame, month_start: date) -> pd.Series:
    end = (pd.Timestamp(month_start) + pd.offsets.MonthEnd(0)).date()
    return (_d(ds) >= month_start) & (_d(ds) <= min(end, TEST[1]))


def _xy(ds, mask):
    sub = ds[mask & ds["y"].notna()]
    return sub[LOAD_FEATURES].to_numpy(float), sub["y"].to_numpy(float)


# ---------- naive quantile benchmark ----------

def naive_q(ds: pd.DataFrame, rows: pd.DataFrame) -> np.ndarray:
    """lag_d7 + empirical quantiles of lag_d7 errors over the 8 weeks of targets before each issue date."""
    err = (ds["y"] - ds["lag_d7"]).to_numpy()
    days = pd.to_datetime(ds["day"]).to_numpy()
    out = np.empty((len(rows), 7))
    for issue, idx in rows.groupby("issue_date").groups.items():
        lo = np.datetime64(issue - timedelta(weeks=NAIVE_WEEKS))
        hi = np.datetime64(issue)  # targets strictly before D are complete at 09:00 on D
        e = err[(days >= lo) & (days < hi)]
        pos = rows.index.get_indexer(idx)
        out[pos] = naive_quantiles(e, rows.loc[idx, "lag_d7"].to_numpy())
    return out


# ---------- tune ----------

def tune() -> dict:
    ds = dataset()
    tr, va = tune_split(ds)
    Xtr, ytr = _xy(ds, tr)
    Xva, yva = _xy(ds, va)
    rows = []
    for g in GRID:
        m = QuantileModel({**g, "n_estimators": MAX_TREES}).fit(Xtr, ytr, Xva, yva)
        q = m.predict(Xva)
        trees = int(np.mean([b.best_iteration or MAX_TREES for b in m.boosters]))
        rows.append({**g, "pinball": pinball(yva, q), "mape_median": mape(yva, q[:, 3]),
                     "cov90": coverage(yva, q[:, 0], q[:, 6]), "trees": trees})
        print(rows[-1], flush=True)
    t = pd.DataFrame(rows).sort_values("pinball")
    t.to_csv(RESEARCH / "tune_load.csv", index=False)
    best = t.iloc[0]
    return {"num_leaves": int(best.num_leaves), "learning_rate": float(best.learning_rate),
            "min_data_in_leaf": int(best.min_data_in_leaf), "n_estimators": int(best.trees)}


# ---------- test ----------

def _scores(y, q=None, point=None) -> dict:
    out = {"n": int(len(y))}
    if q is not None:
        out.update(pinball=pinball(y, q), mae=mae(y, q[:, 3]), mape=mape(y, q[:, 3]),
                   cov80=coverage(y, q[:, 1], q[:, 5]), cov90=coverage(y, q[:, 0], q[:, 6]),
                   width90=float(np.mean(q[:, 6] - q[:, 0])))
    else:
        out.update(mae=mae(y, point), mape=mape(y, point))
    return out


def test(params: dict) -> dict:
    ds = dataset()
    raw = []
    for m in rolling_months():
        fc = LoadForecaster(params).fit(ds[train_mask(ds, m)])
        rows = ds[predict_mask(ds, m)].copy()
        q = fc.predict(rows)
        for i, a in enumerate(QUANTILES):
            rows[f"r{int(a * 100):02d}"] = q[:, i]
        raw.append(rows)
        print(f"refit {m}: {len(rows)} rows", flush=True)
    p = pd.concat(raw, ignore_index=True)
    rc = [f"r{int(a * 100):02d}" for a in QUANTILES]
    err = p["y"].to_numpy()[:, None] - p[rc].to_numpy()
    days = pd.to_datetime(p["day"]).to_numpy()
    final = np.full((len(p), 7), np.nan)
    for issue, idx in p.groupby("issue_date").groups.items():
        hist = (days >= np.datetime64(issue - timedelta(weeks=CONFORMAL_WEEKS))) & (days < np.datetime64(issue))
        pos = p.index.get_indexer(idx)
        final[pos] = np.sort(p.loc[idx, rc].to_numpy() + conformal_shift(err[hist])[None, :], axis=1)
    for i, a in enumerate(QUANTILES):
        p[f"q{int(a * 100):02d}"] = final[:, i]
    p = p[p["issue_date"] >= TEST[0]].reset_index(drop=True)
    nq = naive_q(ds, p)
    for i, a in enumerate(QUANTILES):
        p[f"n{int(a * 100):02d}"] = nq[:, i]
    p.to_csv(RESEARCH / "test_load.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    return summarize(p, params)


QCOLS = [f"q{int(a * 100):02d}" for a in QUANTILES]
RCOLS = [f"r{int(a * 100):02d}" for a in QUANTILES]
NCOLS = [f"n{int(a * 100):02d}" for a in QUANTILES]


def summarize(p: pd.DataFrame, params: dict) -> dict:
    """Scores on hours with an observed target, a model forecast and a naive forecast (lag_d7 exists)."""
    ok = p["y"].notna() & p[QCOLS].notna().all(axis=1) & p[NCOLS].notna().all(axis=1)
    both = ok & p["plan"].notna() & p["plan_bc"].notna()

    def block(mask):
        s = p[mask]
        y = s["y"].to_numpy()
        return {
            "model": _scores(y, s[QCOLS].to_numpy()),
            "model_no_conformal": _scores(y, s[RCOLS].to_numpy()),
            "naive_lastweek": _scores(y, s[NCOLS].to_numpy()),
            "plan": _scores(y, point=s["plan"].to_numpy()),
            "plan_bias_corrected": _scores(y, point=s["plan_bc"].to_numpy()),
        }

    month = p["issue_date"].astype(str).str[:7]
    out = {"params": params, "hours_scored": int(both.sum()), "hours_without_forecast": int((p["y"].notna() & ~ok).sum()),
           "overall": block(both), "all_hours_model": _scores(p.loc[ok, "y"].to_numpy(), p.loc[ok, QCOLS].to_numpy()),
           "by_month": {m: block(both & (month == m)) for m in sorted(month.unique())}}
    levels = {f"{a:.2f}": float(np.mean(p.loc[ok, "y"] <= p.loc[ok, c])) for a, c in zip(QUANTILES, QCOLS)}
    out["reliability"] = levels
    (RESEARCH / "test_load.json").write_text(json.dumps(out, indent=1))
    return out
