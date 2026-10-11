"""The load forecaster: quantile models of (load − same hour last week), then a rolling conformal
shift that moves each quantile by the matching quantile of its errors over the previous 8 weeks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .features import LOAD_FEATURES
from .metrics import QUANTILES
from .models import QuantileModel

BASE = "lag_d7"
CONFORMAL_WEEKS = 8
MIN_HISTORY = 48


def conformal_shift(errors: np.ndarray) -> np.ndarray:
    """errors[n, 7] = y − q (past forecasts). Shift for quantile a = a-quantile of its errors."""
    e = np.asarray(errors, float)
    e = e[np.isfinite(e).all(axis=1)]
    if len(e) < MIN_HISTORY:
        return np.zeros(len(QUANTILES))
    return np.array([np.quantile(e[:, i], a) for i, a in enumerate(QUANTILES)])


class LoadForecaster:
    def __init__(self, params: dict, features: list[str] = LOAD_FEATURES):
        self.params, self.features = params, list(features)
        self.model = QuantileModel(params)

    def fit(self, rows: pd.DataFrame) -> "LoadForecaster":
        r = rows[rows["y"].notna() & rows[BASE].notna()]
        self.model.fit(r[self.features].to_numpy(float), (r["y"] - r[BASE]).to_numpy(float))
        return self

    def predict(self, rows: pd.DataFrame, shift: np.ndarray | None = None) -> np.ndarray:
        """Raw quantiles + base (+ conformal shift), sorted per row. Rows without a base get NaN."""
        q = self.model.predict(rows[self.features].to_numpy(float)) + rows[BASE].to_numpy(float)[:, None]
        if shift is not None:
            q = q + np.asarray(shift)[None, :]
        return np.sort(q, axis=1)

    def save(self, path: Path) -> None:
        self.model.save(path)

    @classmethod
    def load(cls, path: Path, features: list[str] = LOAD_FEATURES) -> "LoadForecaster":
        fc = cls({}, features)
        fc.model = QuantileModel.load(path)
        fc.params = fc.model.params
        return fc
