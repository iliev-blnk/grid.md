import numpy as np

from gridmd.metrics import QUANTILES, coverage, mae, mape, pinball


def test_quantile_levels():
    assert QUANTILES == [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]


def test_pinball_known_values():
    y = np.array([10.0])
    assert pinball(y, np.full((1, 7), 10.0)) == 0
    q = np.full((1, 7), 10.0)
    q[0, 3] = 12.0  # median over-predicts by 2: loss (1 - 0.5) * 2
    assert abs(pinball(y, q) - (0.5 * 2) / 7) < 1e-12
    q = np.full((1, 7), 10.0)
    q[0, 0] = 6.0  # q05 under by 4: loss 0.05 * 4
    assert abs(pinball(y, q) - (0.05 * 4) / 7) < 1e-12


def test_coverage_mae_mape():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert coverage(y, np.array([0, 0, 0, 5.0]), np.array([1.5, 1.5, 1.5, 6.0])) == 0.25
    assert mae(y, y + 1) == 1
    assert abs(mape(np.array([100.0, 0.0]), np.array([110.0, 5.0])) - 10.0) < 1e-12  # y ≤ 0 ignored
