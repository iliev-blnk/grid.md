import json
from pathlib import Path

from gridmd import era5

FIX = json.loads((Path(__file__).parent / "fixtures" / "era5_sample.json").read_text())


def test_parse_archive():
    df = era5.parse_archive(FIX)
    assert list(df.columns) == ["ghi", "temp", "cloud", "wind100"]
    assert len(df) == 48 and str(df.index.tz) == "UTC"
    assert df["ghi"].max() > 500 and df["ghi"].min() == 0


def test_six_sites():
    assert set(era5.ERA5_SITES) == {"chisinau", "balti", "cahul", "ungheni", "comrat", "soroca"}
