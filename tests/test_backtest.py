from datetime import date

import pandas as pd

from sarcina import backtest as bt


def fake_ds():
    days = pd.date_range("2022-01-15", "2026-09-30", freq="D").date
    return pd.DataFrame({"issue_date": days, "day": [(d + pd.Timedelta(days=1)).isoformat() for d in days], "y": 1.0})


def test_grid_is_fixed():
    assert len(bt.GRID) == 12
    assert {g["num_leaves"] for g in bt.GRID} == {15, 31, 63}
    assert {g["learning_rate"] for g in bt.GRID} == {0.03, 0.1}
    assert {g["min_data_in_leaf"] for g in bt.GRID} == {20, 100}


def test_splits_respect_dates():
    ds = fake_ds()
    tr, va = bt.tune_split(ds)
    assert ds.loc[tr, "issue_date"].max() <= date(2025, 3, 31)
    assert ds.loc[tr, "issue_date"].min() >= date(2022, 1, 15)
    assert ds.loc[va, "issue_date"].min() == date(2025, 4, 1) and ds.loc[va, "issue_date"].max() == date(2025, 9, 30)
    assert not (ds.loc[tr | va, "issue_date"] >= date(2025, 10, 1)).any()


def test_expanding_refit_never_sees_future():
    ds = fake_ds()
    months = bt.test_months()
    assert months[0] == date(2025, 10, 1) and months[-1] == date(2026, 9, 1) and len(months) == 12
    for m in months:
        train = bt.train_mask(ds, m)
        assert ds.loc[train, "day"].max() < m.isoformat()  # every training target was observed before the refit
        pred = bt.predict_mask(ds, m)
        assert ds.loc[pred, "issue_date"].min() == m


def test_rolling_months_start_before_test():
    r = bt.rolling_months()
    assert r[0] == date(2025, 1, 1) and r[-1] == date(2026, 9, 1) and len(r) == 21
