from datetime import date

from gridmd.calendar_md import is_bridge, is_holiday


def test_moldovan_holidays():
    assert is_holiday(date(2026, 4, 13))  # Orthodox Easter Monday
    assert is_holiday(date(2027, 1, 7))  # Orthodox Christmas
    assert not is_holiday(date(2026, 4, 14))


def test_bridge_day():
    # 2026-01-08 (Thu) is Christmas day 2 -> Friday 2026-01-09 sits between it and the weekend
    assert is_bridge(date(2026, 1, 9))
    assert not is_bridge(date(2026, 1, 12))
