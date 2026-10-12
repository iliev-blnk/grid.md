from __future__ import annotations

from pathlib import Path

import pandas as pd


def merge_recent(old: pd.DataFrame, new: pd.DataFrame, key: list[str]) -> pd.DataFrame:
    """Rows of `new` replace rows of `old` with the same key; everything else in `old` is kept."""
    m = pd.concat([old, new], ignore_index=True).drop_duplicates(key, keep="last")
    return m.sort_values(key).reset_index(drop=True)


def write_atomic(df: pd.DataFrame, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    df.to_csv(tmp, index=False, compression={"method": "gzip", "mtime": 0})
    tmp.replace(out)
