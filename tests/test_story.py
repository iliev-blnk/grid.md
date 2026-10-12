import json

import numpy as np
import pytest

from gridmd.features import load_tables
from gridmd.story import story_json

T = load_tables()


@pytest.fixture(scope="module")
def S():
    return story_json(T, json.load(open("data/solar_monthly_v2.json")))


def test_monthly_means_match_hourly(S):
    h = T.load.reset_index()
    m = h[h["day"].str.startswith("2024-03")]
    assert abs(S["monthly"]["2024-03"]["load"] - m["load"].mean()) < 0.6
    assert abs(S["monthly"]["2024-03"]["tpp"] - m["tpp"].mean()) < 0.6


def test_profiles_have_24_points(S):
    assert set(S["profiles"]) >= {"2022", "2023", "2024", "2025", "2026"}
    assert all(len(v) == 24 for v in S["profiles"].values())


def test_shares_are_fractions(S):
    for m in S["monthly"].values():
        assert 0 <= m["export_share"] <= 1 and 0 <= m["transit_share"] <= 1


def test_flow_sign_import_positive(S):
    y = S["yearly"]["2025"]
    assert y["net_import"] > 0 and y["md_ro"] > 0


def test_chapter_numbers(S):
    c = S["chapters"]
    assert c["blackout"]["low"] == pytest.approx(289.75, abs=0.5) and c["blackout"]["hour"] == 15
    assert c["corridor"]["share"] == pytest.approx(S["yearly"]["2023"]["transit_share"])
    assert c["duck"]["first"] > c["duck"]["last"]
    assert 400 < c["solar"]["C"] < 1000 and c["solar"]["lo"] < c["solar"]["C"] < c["solar"]["hi"]
    assert c["cutoff"]["tpp_before"] > 2 * c["cutoff"]["tpp_after"]
