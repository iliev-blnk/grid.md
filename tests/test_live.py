import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from gridmd import live
from gridmd.features import load_tables


def test_can_issue_window():
    assert live.can_issue(pd.Timestamp("2026-07-01T06:00Z"))  # 09:00 EEST
    assert not live.can_issue(pd.Timestamp("2026-07-01T05:59Z"))
    assert live.can_issue(pd.Timestamp("2026-07-01T19:59Z"))  # 22:59
    assert not live.can_issue(pd.Timestamp("2026-07-01T20:00Z"))  # 23:00
    assert live.can_issue(pd.Timestamp("2026-12-01T07:00Z"))  # 09:00 EET
    assert not live.can_issue(pd.Timestamp("2026-12-01T06:30Z"))


class FakeFc:
    def predict(self, rows, shift=None):
        base = rows["lag_d7"].to_numpy()[:, None]
        q = base + np.array([-30, -20, -10, 0, 10, 20, 30])[None, :]
        return q if shift is None else q + np.asarray(shift)[None, :]


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "FORECASTS", tmp_path / "forecasts")
    monkeypatch.setattr(live, "SCORES", tmp_path / "scores")
    monkeypatch.setattr(live, "load_forecaster", lambda: (FakeFc(), {"train_end_day": "2025-04-30"}))
    monkeypatch.setattr(live, "seed_history", lambda: pd.DataFrame(columns=["day", "hour", "y", *live.RAW]))
    return load_tables()


def test_forecast_writes_file_and_refuses_second(env):
    p = live.forecast(date(2025, 5, 14), tables=env, now=pd.Timestamp("2025-05-14T06:05Z"))
    js = json.loads(p.read_text())
    assert p.name == "2025-05-15.json" and js["target_day"] == "2025-05-15"
    assert len(js["hours"]) == 24 and len(js["q"]) == 24 and len(js["q"][0]) == 7
    assert js["issue_cutoff"] == "2025-05-14T09:00:00+03:00" and js["late"] is False
    before = p.read_bytes()
    with pytest.raises(live.AlreadyIssued):
        live.forecast(date(2025, 5, 14), tables=env, now=pd.Timestamp("2025-05-14T07:00Z"))
    assert p.read_bytes() == before


def test_forecast_hour_count_on_dst_days(env):
    assert len(json.loads(live.forecast(date(2026, 3, 28), tables=env, now=pd.Timestamp("2026-03-28T07:10Z")).read_text())["hours"]) == 23
    assert len(json.loads(live.forecast(date(2025, 10, 25), tables=env, now=pd.Timestamp("2025-10-25T06:10Z")).read_text())["hours"]) == 24


def test_not_enough_weather_writes_nothing(env):
    w = env.weather.copy()
    w[:] = np.nan
    t = env._replace(weather=w)
    with pytest.raises(live.NotEnoughWeather):
        live.forecast(date(2025, 5, 14), tables=t, now=pd.Timestamp("2025-05-14T06:05Z"))
    assert not (live.FORECASTS / "2025-05-15.json").exists()


def test_score_skips_incomplete_day(env):
    live.forecast(date(2025, 5, 14), tables=env, now=pd.Timestamp("2025-05-14T06:05Z"))
    load = env.load.drop(index=("2025-05-15", 20))
    out = live.score_ready(env._replace(load=load))
    assert out == []
    out = live.score_ready(env)
    assert [p.name for p in out] == ["2025-05-15.json"]
    s = json.loads(out[0].read_text())
    assert {"mae", "mape", "pinball", "in90", "plan_mape", "plan_bc_mape"} <= set(s)
    assert live.score_ready(env) == []  # already scored
