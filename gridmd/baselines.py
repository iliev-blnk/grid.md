from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import QUANTILES


def naive_quantiles(history_errors: np.ndarray, point: np.ndarray) -> np.ndarray:
    """Point forecast + empirical quantiles of past errors (actual − point)."""
    e = np.asarray(history_errors, float)
    e = e[np.isfinite(e)]
    return np.asarray(point, float)[:, None] + np.quantile(e, QUANTILES)[None, :]


def bias_corrected_plan(hist: pd.DataFrame, plan_target: np.ndarray, issue_day: str, days: int = 28) -> np.ndarray:
    """Operator plan minus its mean error (plan − load) over the `days` days before `issue_day`."""
    h = hist[(hist.index.get_level_values("day") < issue_day)]
    recent = sorted(set(h.index.get_level_values("day")))[-days:]
    h = h[h.index.get_level_values("day").isin(recent)]
    bias = np.nanmean((h["plan"] - h["load"]).to_numpy())
    return np.asarray(plan_target, float) - (bias if np.isfinite(bias) else 0.0)
