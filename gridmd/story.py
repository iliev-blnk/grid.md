"""Aggregates for the 2021–2026 story page: small monthly/yearly tables and one number per chapter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .features import Tables

ROOT = Path(__file__).resolve().parents[1]
PREWAR = ("2021-12-01", "2022-02-23")
ANCHORS = [
    {"label": "total solar, end 2024", "MW": 394, "source": "CNED via pv-magazine, 3 Mar 2026",
     "url": "https://www.pv-magazine.com/2026/03/03/moldova-installs-315-mw-of-solar-in-2025/"},
    {"label": "total solar, end 2025", "MW": 710, "source": "CNED via pv-magazine, 3 Mar 2026",
     "url": "https://www.pv-magazine.com/2026/03/03/moldova-installs-315-mw-of-solar-in-2025/"},
    {"label": "prosumers, end 2025", "MW": 195, "source": "CNED via pv-magazine, 3 Mar 2026",
     "url": "https://www.pv-magazine.com/2026/03/03/moldova-installs-315-mw-of-solar-in-2025/"},
]


def _r(v, nd=1):
    return None if v is None or not np.isfinite(v) else round(float(v), nd)


def _agg(g: pd.DataFrame) -> dict:
    return {
        "load": _r(g["load"].mean()), "tpp": _r(g["tpp"].mean()), "hpp": _r(g["hpp"].mean()),
        "res": _r(g["res"].mean()), "net_import": _r(g["balance"].mean()),
        "md_ua": _r(g["md_ua"].mean()), "md_ro": _r(g["md_ro"].mean()),
        "export_share": _r((g["balance"] < 0).mean(), 3),
        "transit_share": _r(((g["md_ro"] > 0) & (g["md_ua"] < 0)).mean(), 3),
        "min_load": _r(g["load"].min()),
    }


def story_json(tables: Tables, solar_v2: list[dict]) -> dict:
    h = tables.load.reset_index()
    h["year"], h["month"] = h["day"].str[:4], h["day"].str[:7]
    yearly = {y: _agg(g) for y, g in h.groupby("year")}
    monthly = {m: _agg(g) for m, g in h.groupby("month")}

    mj = h[h["month"].str[5:].isin(["05", "06"])]
    profiles = {y: [_r(v) for v in g.groupby("hour")["load"].mean().reindex(range(24))] for y, g in mj.groupby("year")}
    piv = mj.pivot_table(index=["year", "day"], columns="hour", values="load")
    duck = (piv[13] / piv[20]).groupby(level="year").median()

    bo = h[(h["day"] >= "2022-10-01") & (h["day"] <= "2022-12-31")]
    daily = bo.groupby("day")["load"].agg(["mean", "min"]).round(1)
    nov23 = h[h["day"] == "2022-11-23"].sort_values("hour")
    low = nov23.loc[nov23["load"].idxmin()]
    noon = nov23[nov23["hour"].between(9, 13)]["load"].max()

    pre = h[(h["day"] >= PREWAR[0]) & (h["day"] <= PREWAR[1])]
    rows = [r for r in solar_v2 if r.get("hidden_net")]
    summer = [r for r in rows if r["month"] in [f"2026-0{m}" for m in range(5, 10)]]
    mean = lambda k: _r(np.mean([r["hidden_net"][k] for r in summer]), 0)

    chapters = {
        "before": {"tpp_share": _r((pre["tpp"] / pre["load"]).median(), 3), "load": _r(pre["load"].mean(), 0),
                   "tpp": _r(pre["tpp"].mean(), 0)},
        "blackout": {"day": "2022-11-23", "hour": int(low["hour"]), "low": _r(low["load"]), "before": _r(noon)},
        "corridor": {"year": "2023", "share": yearly["2023"]["transit_share"], "export_share": yearly["2023"]["export_share"],
                     "md_ro": yearly["2023"]["md_ro"], "md_ua": yearly["2023"]["md_ua"]},
        "cutoff": {"tpp_before": yearly["2024"]["tpp"], "tpp_after": yearly["2025"]["tpp"],
                   "import_before": yearly["2024"]["net_import"], "import_after": yearly["2025"]["net_import"]},
        "duck": {"first_year": "2022", "first": _r(duck.get("2022"), 2), "last_year": "2026", "last": _r(duck.get("2026"), 2),
                 "min_load": yearly["2026"]["min_load"]},
        "solar": {"C": mean("C"), "lo": mean("lo"), "hi": mean("hi"),
                  "visible": _r(np.mean([r["visible"]["C"] for r in summer]), 0), "prosumers": 195},
    }
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "yearly": yearly, "monthly": monthly, "profiles": profiles,
        "duck_ratio": {y: _r(v, 2) for y, v in duck.items()},
        "blackout": {"daily": {d: {"mean": r["mean"], "min": r["min"]} for d, r in daily.iterrows()},
                     "hours": [_r(v) for v in nov23["load"]]},
        "solar": [{"month": r["month"], "hidden": r["hidden_net"], "visible": r["visible"]["C"] if r["visible"] else None} for r in rows],
        "chapters": chapters,
        "anchors": ANCHORS,
    }


def write_story(tables: Tables, root: Path = ROOT) -> Path:
    s = story_json(tables, json.loads((root / "data" / "solar_monthly_v2.json").read_text()))
    p = root / "data" / "story.json"
    p.write_text(json.dumps(s))
    return p
