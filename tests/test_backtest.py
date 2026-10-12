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


def test_summarize_skips_rows_without_forecast(tmp_path, monkeypatch):
    import numpy as np

    monkeypatch.setattr(bt, "RESEARCH", tmp_path)
    n = 60
    p = pd.DataFrame({"issue_date": [date(2025, 10, 1)] * n, "y": 500.0, "plan": 520.0, "plan_bc": 505.0})
    for c in bt.QCOLS + bt.RCOLS + bt.NCOLS:
        p[c] = 500.0
    p.loc[0, bt.QCOLS] = np.nan
    out = bt.summarize(p, {})
    assert np.isfinite(out["overall"]["model"]["mape"]) and out["overall"]["model"]["n"] == n - 1


def test_figures_write_svgs(tmp_path, monkeypatch):
    monkeypatch.setattr(bt, "RESEARCH", tmp_path)
    s = {"by_month": {f"2026-{m:02d}": {k: {"mape": 10.0 + m} for k in ("model", "plan", "plan_bias_corrected", "naive_lastweek")}
                      for m in range(1, 13)},
         "reliability": {f"{a:.2f}": a for a in [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]}}
    bt.figures(s)
    svg = (tmp_path / "figures" / "monthly_mape.svg").read_text()
    assert svg.startswith("<svg") and svg.count("<circle") == 12 * 3
    assert (tmp_path / "figures" / "reliability.svg").read_text().count("<circle") == 7
