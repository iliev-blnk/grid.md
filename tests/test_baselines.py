import numpy as np
import pandas as pd

from gridmd.baselines import bias_corrected_plan, naive_quantiles


def test_naive_quantiles_shape_and_order():
    rng = np.random.default_rng(0)
    q = naive_quantiles(rng.normal(0, 10, 500), np.array([100.0, 200.0]))
    assert q.shape == (2, 7)
    assert (np.diff(q, axis=1) >= 0).all()
    assert abs(q[0, 3] - 100.0) < 2.5  # median error ≈ 0


def test_bias_corrected_plan():
    # plan over-predicts by exactly 50 MW for 28 days; the correction removes it
    days = [f"2025-05-{d:02d}" for d in range(1, 29)]
    idx = pd.MultiIndex.from_product([days, range(24)], names=["day", "hour"])
    hist = pd.DataFrame({"load": 500.0, "plan": 550.0}, index=idx)
    out = bias_corrected_plan(hist, plan_target=np.array([560.0, 570.0]), issue_day="2025-05-29")
    assert np.allclose(out, [510.0, 520.0])
