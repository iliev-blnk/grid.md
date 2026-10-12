import pandas as pd

from gridmd.tables import merge_recent


def test_merge_recent_replaces_overlap_and_keeps_old():
    old = pd.DataFrame({"day": ["2026-10-01", "2026-10-02", "2026-10-03"], "hour": [0, 0, 0], "load": [1.0, 2.0, 3.0]})
    new = pd.DataFrame({"day": ["2026-10-03", "2026-10-04"], "hour": [0, 0], "load": [30.0, 4.0]})
    m = merge_recent(old, new, key=["day", "hour"])
    assert m["load"].tolist() == [1.0, 2.0, 30.0, 4.0]


def test_merge_recent_never_drops_rows_missing_from_new():
    old = pd.DataFrame({"day": ["2026-10-03", "2026-10-03"], "hour": [0, 1], "load": [3.0, 3.5]})
    new = pd.DataFrame({"day": ["2026-10-03"], "hour": [0], "load": [30.0]})
    assert merge_recent(old, new, key=["day", "hour"])["load"].tolist() == [30.0, 3.5]
