import numpy as np

from sarcina.models import QuantileModel

PARAMS = dict(num_leaves=15, learning_rate=0.05, min_data_in_leaf=20, n_estimators=300)


def data(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(1, 10, n)
    return x.reshape(-1, 1), x + rng.normal(0, x)


def test_predictions_sorted_and_heteroscedastic():
    X, y = data(4000, 0)
    m = QuantileModel(PARAMS).fit(X, y)
    q = m.predict(np.array([[2.0], [9.0]]))
    assert (np.diff(q, axis=1) >= 0).all()
    assert (q[1, 5] - q[1, 1]) > (q[0, 5] - q[0, 1])


def test_synthetic_coverage():
    X, y = data(6000, 1)
    m = QuantileModel(PARAMS).fit(X, y)
    Xt, yt = data(3000, 2)
    q = m.predict(Xt)
    cov = np.mean((yt >= q[:, 0]) & (yt <= q[:, 6]))
    assert 0.85 <= cov <= 0.95


def test_save_load_roundtrip(tmp_path):
    X, y = data(1000, 3)
    m = QuantileModel(PARAMS).fit(X, y)
    m.save(tmp_path / "m.json")
    m2 = QuantileModel.load(tmp_path / "m.json")
    assert np.allclose(m.predict(X[:20]), m2.predict(X[:20]))
