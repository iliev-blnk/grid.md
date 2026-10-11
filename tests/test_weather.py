import json
import math
from pathlib import Path

from sarcina import weather as w

FIX = json.loads((Path(__file__).parent / "fixtures" / "om_prev.json").read_text())


def test_day1_with_day2_fallback():
    df = w.parse_previous_runs(FIX)
    assert len(df) == 48
    assert list(df["temperature_2m"].iloc[3:8]) == [12.3, 11.8, 11.9, 12.8, 16.1]
    assert df["fallback"].iloc[3:8].all()
    assert df["fallback"].sum() == 5


def test_all_null_hour_stays_nan():
    df = w.parse_previous_runs(FIX)
    assert math.isnan(df["cloud_cover"].iloc[10])
    assert not df["fallback"].iloc[10]


def test_md_weighted_weights_sum_to_one():
    assert abs(sum(s[2] for s in w.SITES.values()) - 1) < 1e-12
    one = w.parse_previous_runs(FIX).assign(site="chisinau")
    frames = [one.assign(site=s) for s in w.SITES]
    m = w.md_weighted(__import__("pandas").concat(frames))
    assert abs(m["temperature_2m"].iloc[0] - one["temperature_2m"].iloc[0]) < 1e-9
