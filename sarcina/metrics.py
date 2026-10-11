from __future__ import annotations

import numpy as np

QUANTILES = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
_Q = np.array(QUANTILES)


def pinball(y: np.ndarray, q_pred: np.ndarray) -> float:
    """Mean pinball loss over rows and the 7 quantiles."""
    d = np.asarray(y, float)[:, None] - np.asarray(q_pred, float)
    return float(np.mean(np.maximum(_Q * d, (_Q - 1) * d)))


def coverage(y, lo, hi) -> float:
    y = np.asarray(y, float)
    return float(np.mean((y >= lo) & (y <= hi)))


def mae(y, p) -> float:
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(p, float))))


def mape(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    ok = y > 0
    return float(100 * np.mean(np.abs(y[ok] - p[ok]) / y[ok]))
