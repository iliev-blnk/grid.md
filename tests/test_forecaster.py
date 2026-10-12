import numpy as np
import pandas as pd

from gridmd.forecaster import LoadForecaster, conformal_shift

PARAMS = dict(num_leaves=7, learning_rate=0.1, min_data_in_leaf=20, n_estimators=50)


def test_conformal_shift_constant_errors():
    e = np.full((100, 7), 5.0)
    assert np.allclose(conformal_shift(e), 5.0)


def test_conformal_shift_needs_history():
    assert np.allclose(conformal_shift(np.zeros((10, 7))), 0.0)  # too little history -> no shift
    assert np.allclose(conformal_shift(np.full((10, 7), 9.0)), 0.0)


def test_forecaster_adds_base_back():
    rng = np.random.default_rng(1)
    n = 2000
    rows = pd.DataFrame({"lag_d7": rng.uniform(400, 800, n), "x": rng.normal(0, 1, n)})
    rows["y"] = rows["lag_d7"] + 30 * rows["x"] + rng.normal(0, 5, n)
    fc = LoadForecaster(PARAMS, features=["x"]).fit(rows)
    q = fc.predict(rows.iloc[:5])
    assert q.shape == (5, 7)
    assert np.all(np.abs(q[:, 3] - rows["y"].iloc[:5].to_numpy()) < 40)
