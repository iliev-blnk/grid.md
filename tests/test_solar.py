import numpy as np
import pandas as pd
import pytest

from gridmd import solar
from gridmd.features import load_tables

T = load_tables()
E = solar.load_era5()


@pytest.fixture(scope="module")
def june():
    f = solar.load_frame(T, E)
    return f[f["day"].str.startswith("2026-06")].reset_index(drop=True)


def synth(f, C, seed=1, shift_days=None):
    rng = np.random.default_rng(seed)
    days = sorted(f["day"].unique())
    level = dict(zip(days, rng.normal(0, 40, len(days))))
    base = 520 + 120 * np.sin((f["hour"] - 8) / 24 * 2 * np.pi) + f["day"].map(level)
    if shift_days:
        base = base + f["day"].isin(shift_days) * 80.0
    out = f.copy()
    out["load"] = base - C * f["yield"] + rng.normal(0, 8, len(f))
    return out


def test_yield_zero_at_night_and_rated_at_stc():
    assert solar.pv_yield(np.array([0.0]), np.array([10.0]))[0] == 0
    assert abs(solar.pv_yield(np.array([1000.0]), np.array([0.0]))[0] - 0.82) < 1e-9  # T_cell = 25 °C


def test_frame_columns(june):
    for c in ("day", "hour", "load", "res", "yield", "wind", "hdh", "cdh", "daytype"):
        assert c in june.columns
    noon, night = june[june["hour"] == 13]["yield"].mean(), june[june["hour"] == 2]["yield"].mean()
    assert noon > 0.3 and night == 0


def test_estimator_recovers_planted_capacity(june):
    r = solar.estimate_hidden(synth(june, 300))
    assert abs(r["C"] - 300) / 300 < 0.10
    assert r["lo"] <= r["C"] <= r["hi"]


def test_day_fixed_effect_ignores_level_shift(june):
    days = sorted(june["day"].unique())[::3]
    a = solar.estimate_hidden(synth(june, 300))["C"]
    b = solar.estimate_hidden(synth(june, 300, shift_days=days))["C"]
    assert abs(a - b) / a < 0.02


def test_misaligned_yield_fits_worse(june):
    s = synth(june, 300)
    shifted = s.copy()
    shifted["yield"] = np.roll(s["yield"].to_numpy(), 3)
    assert solar.estimate_hidden(shifted)["rss"] > solar.estimate_hidden(s)["rss"]


def test_short_month_skipped(june):
    keep = sorted(june["day"].unique())[:15]
    assert solar.estimate_hidden(june[june["day"].isin(keep)]) is None


def test_visible_recovers_planted(june):
    s = june.copy()
    rng = np.random.default_rng(3)
    s["res"] = 5 + 120 * s["yield"] + 40 * s["wind"] + rng.normal(0, 2, len(s))
    r = solar.estimate_visible(s)
    assert abs(r["C"] - 120) < 6


def test_no_bootstrap_gives_point_interval(june):
    r = solar.estimate_hidden(synth(june, 300), boot=0)
    assert r["lo"] == r["C"] == r["hi"]


def test_frame_can_use_tilted_irradiance(june):
    f = solar.load_frame(T, E, irr="gti")
    j = f[f["day"].str.startswith("2026-06")]
    assert j["yield"].max() > 0 and not np.allclose(j["yield"].to_numpy(), june["yield"].to_numpy())


def test_subtract_baseline_by_calendar_month():
    rows = [{"month": "2022-01", "hidden": {"C": 120.0, "lo": 0, "hi": 200}},
            {"month": "2025-01", "hidden": {"C": 520.0, "lo": 400, "hi": 640}},
            {"month": "2025-02", "hidden": {"C": 300.0, "lo": 200, "hi": 400}}]
    out = solar.subtract_baseline(rows, base_from="2021-12", base_to="2022-11")
    assert out[1]["hidden_net"]["C"] == 400.0 and out[1]["hidden_net"]["lo"] == 280.0
    assert out[2]["hidden_net"] is None  # no February in the baseline year
