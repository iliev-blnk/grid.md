import random
from datetime import date, timedelta

import pandas as pd
import pytest

from sarcina import features as f
from sarcina.weather import allowed_lead

T = f.load_tables()


def test_no_input_after_issue_time():
    rnd = random.Random(1)
    days = [date(2024, 2, 1) + timedelta(days=rnd.randrange(0, 960)) for _ in range(30)]
    for d in days:
        rows = f.load_rows(T, d)
        issue = f.issue_time(d).tz_convert("UTC")
        assert f.max_input_time(T, d) <= issue
        for valid, lead in zip(rows["valid_utc"], rows["lead"]):
            assert lead == allowed_lead(valid, issue)
            assert valid - pd.Timedelta(hours=24 * lead) <= issue


def test_lag_d1_rule():
    d = date(2025, 5, 14)
    rows = f.load_rows(T, d).set_index("hour")
    load = T.load["load"]
    assert rows.loc[7, "lag_d1"] == load[("2025-05-14", 7)]
    assert rows.loc[8, "lag_d1"] == load[("2025-05-13", 8)]
    assert rows.loc[15, "lag_d1"] == load[("2025-05-13", 15)]
    assert rows.loc[15, "lag_d7"] == load[("2025-05-08", 15)]


def test_dst_target_rows():
    assert len(f.load_rows(T, date(2026, 10, 24))) == 24  # 25 Oct: autumn change, 24 wall-clock labels
    spring = f.load_rows(T, date(2026, 3, 28))
    assert len(spring) == 23 and 3 not in set(spring["hour"])


def test_features_present_and_target():
    rows = f.load_rows(T, date(2025, 5, 14))
    assert set(f.LOAD_FEATURES) <= set(rows.columns)
    assert rows["y"].notna().all() and rows["plan"].notna().all()
    assert (rows["hdh"] >= 0).all() and (rows["cdh"] >= 0).all()
    assert rows["post2025"].all()


def test_issue_time_is_nine_local():
    t = f.issue_time(date(2026, 12, 1))
    assert (t.hour, str(t.tz)) == (9, "Europe/Chisinau")
    assert t.tz_convert("UTC").hour == 7
