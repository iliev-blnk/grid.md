from datetime import date

from gridmd.timeutil import CHISINAU, local_day_hours


def test_normal_day_has_24_hours():
    assert local_day_hours(date(2026, 7, 1), CHISINAU) == list(range(24))


def test_spring_day_has_no_hour_3():
    h = local_day_hours(date(2026, 3, 29), CHISINAU)
    assert len(h) == 23 and 3 not in h


def test_autumn_day_has_24_wall_clock_labels():
    assert local_day_hours(date(2025, 10, 26), CHISINAU) == list(range(24))
