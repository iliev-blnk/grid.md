import json
import math
from pathlib import Path

import pandas as pd

from gridmd import weather as w

FIX = json.loads((Path(__file__).parent / "fixtures" / "om_prev.json").read_text())


def test_parse_keeps_each_lead():
    df = w.parse_previous_runs(FIX)
    assert len(df) == 48
    for v in w.VARS:
        for k in w.LEADS:
            assert f"{v}_d{k}" in df.columns
    assert df["temperature_2m_d2"].iloc[3:8].isna().all()


def test_freshest_allowed_lead():
    issue = pd.Timestamp("2026-10-12T06:00Z")  # 09:00 Chisinau (EEST)
    assert w.allowed_lead(pd.Timestamp("2026-10-13T06:00Z"), issue) == 1  # valid − 24 h == issue
    assert w.allowed_lead(pd.Timestamp("2026-10-13T06:01Z"), issue) == 2
    assert w.allowed_lead(pd.Timestamp("2026-10-13T21:00Z"), issue) == 2
    assert w.allowed_lead(pd.Timestamp("2026-10-14T07:00Z"), issue) == 3


def test_pick_falls_back_to_older_lead():
    df = w.parse_previous_runs(FIX)
    row = df.iloc[4]
    vals, fb = w.pick(row, lead=2)
    assert vals["temperature_2m"] == row["temperature_2m_d3"] and fb
    vals, fb = w.pick(df.iloc[20], lead=2)
    assert vals["temperature_2m"] == df.iloc[20]["temperature_2m_d2"] and not fb


def test_all_leads_null_is_nan():
    vals, fb = w.pick(w.parse_previous_runs(FIX).iloc[10], lead=1)
    assert math.isnan(vals["cloud_cover"])


def test_md_weighted_weights_sum_to_one():
    assert abs(sum(s[2] for s in w.SITES.values()) - 1) < 1e-12
    one = w.parse_previous_runs(FIX).reset_index()
    m = w.md_weighted(pd.concat([one.assign(site=s) for s in w.SITES]))
    assert abs(m["temperature_2m_d1"].iloc[0] - one["temperature_2m_d1"].iloc[0]) < 1e-9
