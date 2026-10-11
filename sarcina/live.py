"""Daily live forecast and scoring. Forecast files are immutable once written."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .baselines import bias_corrected_plan
from .features import Tables, issue_time, load_rows, load_tables
from .forecaster import CONFORMAL_WEEKS, LoadForecaster, conformal_shift
from .metrics import QUANTILES, mae, mape, pinball
from .timeutil import CHISINAU

ROOT = Path(__file__).resolve().parents[1]
FORECASTS = ROOT / "forecasts"
SCORES = ROOT / "scores"
MODELS = ROOT / "models"
RAW = [f"r{int(a * 100):02d}" for a in QUANTILES]
MAX_MISSING_WEATHER = 6
OPEN_HOUR, CLOSE_HOUR = 9, 23


class AlreadyIssued(Exception):
    pass


class NotEnoughWeather(Exception):
    pass


def can_issue(now_utc: pd.Timestamp) -> bool:
    """The issue window: 09:00–23:00 Moldova time on D (the timer fires at 09:00 or on wake)."""
    h = now_utc.tz_convert(CHISINAU).hour
    return OPEN_HOUR <= h < CLOSE_HOUR


def load_forecaster() -> tuple[LoadForecaster, dict]:
    return LoadForecaster.load(MODELS / "load.json"), json.loads((MODELS / "meta.json").read_text())


def seed_history() -> pd.DataFrame:
    """Raw backtest predictions: conformal history for the first live weeks."""
    p = ROOT / "research" / "test_load.csv.gz"
    if not p.exists():
        return pd.DataFrame(columns=["day", "hour", "y", *RAW])
    return pd.read_csv(p, usecols=["day", "hour", "y", *RAW])


def live_history(tables: Tables) -> pd.DataFrame:
    rows = []
    for f in sorted(FORECASTS.glob("*.json")):
        js = json.loads(f.read_text())
        for h, qr in zip(js["hours"], js["q_raw"]):
            rows.append({"day": js["target_day"], "hour": h, **dict(zip(RAW, qr))})
    df = pd.DataFrame(rows, columns=["day", "hour", *RAW])
    df["y"] = [tables.load["load"].get((d, h), np.nan) for d, h in zip(df["day"], df["hour"])]
    return df


def _shift(tables: Tables, d: date) -> np.ndarray:
    live_h = live_history(tables)
    seed = seed_history()
    seed = seed[~seed["day"].isin(set(live_h["day"]))]
    h = pd.concat([seed, live_h], ignore_index=True)
    lo, hi = (d - timedelta(weeks=CONFORMAL_WEEKS)).isoformat(), d.isoformat()
    h = h[(h["day"] >= lo) & (h["day"] < hi)]
    return conformal_shift(h["y"].to_numpy(float)[:, None] - h[RAW].to_numpy(float))


def _r(a: np.ndarray) -> list:
    return [[None if not np.isfinite(v) else round(float(v), 1) for v in row] for row in a]


def forecast(d: date, tables: Tables | None = None, now: pd.Timestamp | None = None, force: bool = False) -> Path:
    target = d + timedelta(days=1)
    path = FORECASTS / f"{target.isoformat()}.json"
    if path.exists() and not force:
        raise AlreadyIssued(path.name)
    tables = tables or load_tables()
    now = now or pd.Timestamp.now(tz="UTC")
    rows = load_rows(tables, d)
    missing = int(rows["t"].isna().sum())
    if missing > MAX_MISSING_WEATHER:
        raise NotEnoughWeather(f"{missing} target hours without weather")
    fc, meta = load_forecaster()
    raw = fc.predict(rows)
    shift = _shift(tables, d)
    q = np.sort(raw + shift[None, :], axis=1)
    cutoff = issue_time(d)
    inputs = rows.drop(columns=["y", "plan"]).to_csv(index=False).encode()
    js = {
        "target_day": target.isoformat(),
        "issued_at": now.isoformat(),
        "issue_cutoff": cutoff.isoformat(),
        "late": bool(now > cutoff.tz_convert("UTC") + pd.Timedelta(hours=1)),
        "hours": [int(h) for h in rows["hour"]],
        "quantiles": QUANTILES,
        "q": _r(q),
        "q_raw": _r(raw),
        "conformal_shift": [round(float(s), 2) for s in shift],
        "weather_fallback": bool(rows["weather_fallback"].any()),
        "weather_missing_hours": missing,
        "model": meta,
        "inputs_sha256": hashlib.sha256(inputs).hexdigest(),
    }
    FORECASTS.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(js, indent=1))
    tmp.replace(path)
    return path


def score_ready(tables: Tables | None = None) -> list[Path]:
    """Score every unscored forecast whose target day is now fully observed."""
    tables = tables or load_tables()
    out = []
    load, plan = tables.load["load"], tables.load["plan"]
    for f in sorted(FORECASTS.glob("*.json")):
        sp = SCORES / f.name
        if sp.exists():
            continue
        js = json.loads(f.read_text())
        day = js["target_day"]
        y = np.array([load.get((day, h), np.nan) for h in js["hours"]], float)
        if not np.isfinite(y).all():
            continue
        q = np.array([[np.nan if v is None else v for v in r] for r in js["q"]], float)
        ok = np.isfinite(q).all(axis=1)
        pl = np.array([plan.get((day, h), np.nan) for h in js["hours"]], float)
        issue_day = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        bc = bias_corrected_plan(tables.load[["load", "plan"]], pl, issue_day)
        pok = np.isfinite(pl)
        s = {
            "target_day": day, "hours": int(len(y)), "mae": mae(y[ok], q[ok, 3]), "mape": mape(y[ok], q[ok, 3]),
            "pinball": pinball(y[ok], q[ok]), "in90": float(np.mean((y[ok] >= q[ok, 0]) & (y[ok] <= q[ok, 6]))),
            "plan_mape": mape(y[pok], pl[pok]) if pok.any() else None,
            "plan_bc_mape": mape(y[pok], bc[pok]) if pok.any() else None,
            "late": js.get("late", False),
        }
        SCORES.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(s, indent=1))
        out.append(sp)
    return out


def retrain(force: bool = False, today: date | None = None) -> str:
    """Refit on every issue date whose target day is observed; at most once per calendar month."""
    from .backtest import TRAIN_START
    from .models import TUNED_LOAD
    from .timeutil import daterange

    today = today or pd.Timestamp.now(tz=CHISINAU).date()
    meta_p = MODELS / "meta.json"
    if meta_p.exists() and not force:
        meta = json.loads(meta_p.read_text())
        if meta["trained_on"][:7] == today.isoformat()[:7]:
            return f"skip: already trained this month ({meta['trained_on']})"
    t = load_tables()
    last_issue = today - timedelta(days=2)  # target day = today − 1, complete by now
    rows = pd.concat([load_rows(t, d) for d in daterange(TRAIN_START, last_issue)], ignore_index=True)
    fc = LoadForecaster(TUNED_LOAD).fit(rows)
    MODELS.mkdir(exist_ok=True)
    fc.save(MODELS / "load.json")
    meta = {"trained_on": today.isoformat(), "train_end_day": (last_issue + timedelta(days=1)).isoformat(),
            "rows": int(rows["y"].notna().sum()), "params": TUNED_LOAD}
    meta_p.write_text(json.dumps(meta, indent=1))
    return f"retrained: {meta}"
