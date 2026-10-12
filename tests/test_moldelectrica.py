from datetime import date
from pathlib import Path

import pytest

from gridmd import moldelectrica as me

FIX = Path(__file__).parent / "fixtures"


def text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_parse_real_month_columns():
    df = me.parse_csv(text("me_2024-01.csv"))
    assert list(df.columns) == ["ts", "load", "plan", "gen", "gen_plan", "tpp", "hpp", "res", "md_ua", "md_ro", "balance", "balance_plan"]
    first = df.sort_values("ts").iloc[-1]  # the file is newest-first; 2024-01-03 00:00 is the newest
    assert str(first["ts"]) == "2024-01-03 00:00:00"
    assert (first["load"], first["plan"], first["tpp"]) == (575.0, 646.0, 564.0)


def test_zero_plan_is_nan():
    df = me.parse_csv(text("me_2024-01.csv"))
    row = df[df["ts"].astype(str) == "2024-01-01 00:15:00"].iloc[0]
    assert row["plan"] != row["plan"]  # NaN (the source has 0)
    assert row["load"] == 596.0


def test_hourly_requires_four_quarters():
    df = me.parse_csv(text("me_2024-01.csv"))
    h = me.hourly(df)
    assert ("2024-01-02", 5) in h.index
    dropped = df[df["ts"].astype(str) != "2024-01-02 05:30:00"]
    assert ("2024-01-02", 5) not in me.hourly(dropped).index
    assert h.loc[("2024-01-02", 5), "n"] == 4


def test_dst_days():
    autumn = me.hourly(me.parse_csv(text("me_dst_2025-10-26.csv")))
    assert len([k for k in autumn.index if k[0] == "2025-10-26"]) == 24
    spring = me.hourly(me.parse_csv(text("me_dst_2026-03-29.csv")))
    day = [k[1] for k in spring.index if k[0] == "2026-03-29"]
    assert len(day) == 23 and 3 not in day


def test_empty_body_raises(monkeypatch):
    monkeypatch.setattr(me, "fetch_bytes", lambda url: (FIX / "me_empty.zip").read_bytes())
    with pytest.raises(me.MoldelectricaError) as e:
        me.fetch_month(2016, 1, cache=False)
    assert "2016-01" in str(e.value)


def test_all_zero_day_is_missing_not_zero():
    df = me.parse_csv(text("me_2024-01.csv"))
    day = df["ts"].dt.strftime("%Y-%m-%d") == "2024-01-02"
    df.loc[day, "load"] = float("nan")  # what parse_csv makes of zeros
    h = me.hourly(df)
    assert h.loc[[k for k in h.index if k[0] == "2024-01-02"], "load"].isna().all()


def test_zeros_parse_to_nan():
    t = text("me_2024-01.csv").splitlines()
    head, row = t[0], t[1].split(";")
    row[1] = "0"
    df = me.parse_csv(head + "\n" + ";".join(row) + "\n")
    assert df["load"].isna().all()


def test_missing_column_raises():
    t = text("me_2024-01.csv").replace("Load Shedule;", "")
    with pytest.raises(me.MoldelectricaError) as e:
        me.parse_csv(t)
    assert "Load Shedule" in e.value.reason
