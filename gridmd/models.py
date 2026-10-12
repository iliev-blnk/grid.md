from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from .metrics import QUANTILES

# Pinned from the validation run (research/tune_load.csv) before the test window is scored; None = untuned.
TUNED_LOAD: dict | None = {"num_leaves": 15, "learning_rate": 0.03, "min_data_in_leaf": 100, "n_estimators": 638}


class QuantileModel:
    """One LightGBM model per quantile; predictions sorted per row so quantiles never cross."""

    def __init__(self, params: dict):
        self.params = dict(params)
        self.boosters: list[lgb.Booster] = []

    def fit(self, X, y, X_val=None, y_val=None) -> "QuantileModel":
        p = {k: v for k, v in self.params.items() if k != "n_estimators"}
        n = self.params.get("n_estimators", 1000)
        self.boosters = []
        for a in QUANTILES:
            params = {"objective": "quantile", "alpha": a, "verbosity": -1, "seed": 7, **p}
            train = lgb.Dataset(np.asarray(X, float), np.asarray(y, float))
            if X_val is not None:
                val = lgb.Dataset(np.asarray(X_val, float), np.asarray(y_val, float), reference=train)
                b = lgb.train(params, train, n, valid_sets=[val], callbacks=[lgb.early_stopping(50, verbose=False)])
            else:
                b = lgb.train(params, train, n)
            self.boosters.append(b)
        return self

    def predict(self, X) -> np.ndarray:
        X = np.asarray(X, float)
        q = np.column_stack([b.predict(X, num_iteration=b.best_iteration or None) for b in self.boosters])
        return np.sort(q, axis=1)

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps({"params": self.params, "quantiles": QUANTILES,
                                          "boosters": [b.model_to_string() for b in self.boosters]}))

    @classmethod
    def load(cls, path: Path) -> "QuantileModel":
        js = json.loads(Path(path).read_text())
        m = cls(js["params"])
        m.boosters = [lgb.Booster(model_str=s) for s in js["boosters"]]
        return m
