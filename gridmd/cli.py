from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta


def _range(args) -> tuple[date, date]:
    end = date.today() + timedelta(days=1)
    if args.recent:
        return end - timedelta(days=args.recent), end
    return date.fromisoformat(args.from_), end


def cmd_ingest(args) -> int:
    start, end = _range(args)
    if args.what == "load":
        from .moldelectrica import build_load

        h = build_load(start, end, merge=bool(args.recent))
        print(f"load: {len(h)} hourly rows {h['day'].min()}..{h['day'].max()}")
    elif args.what == "weather":
        from .weather import build_weather

        w = build_weather(max(start, date(2022, 1, 1)), end, merge=bool(args.recent))
        print(f"weather: {len(w)} rows, {w['site'].nunique()} sites")
    elif args.what == "era5":
        from .era5 import build_era5

        e = build_era5(start, date.today(), merge=bool(args.recent))
        print(f"era5: {len(e)} rows, {e['site'].nunique()} sites, nulls {e['ghi'].isna().mean():.2%}")
    else:
        print("prices: deferred (no source whose licence allows public reuse; see spec amendment 2)")
        return 2
    return 0


def cmd_backtest(args) -> int:
    from . import backtest as bt
    from .models import TUNED_LOAD

    if args.stage == "dataset":
        ds = bt.dataset(cache=False)
        print(f"dataset: {len(ds)} rows, {ds['issue_date'].nunique()} issue dates, y missing {ds['y'].isna().mean():.1%}")
    elif args.stage == "tune":
        print("best:", bt.tune())
    else:
        if TUNED_LOAD is None:
            print("refusing to test: pin TUNED_LOAD in sarcina/models.py first")
            return 1
        out = bt.test(TUNED_LOAD)
        print(json.dumps(out["overall"], indent=1))
    return 0


def cmd_retrain(args) -> int:
    from .live import retrain

    print(retrain(force=args.force))
    return 0


def cmd_forecast(args) -> int:
    import pandas as pd

    from .live import AlreadyIssued, can_issue, forecast

    now = pd.Timestamp.now(tz="UTC")
    d = date.fromisoformat(args.date) if args.date else now.tz_convert("Europe/Chisinau").date()
    if not args.date and not can_issue(now) and not args.force:
        print("skip: outside the 09:00-23:00 issue window")
        return 0
    try:
        print(f"forecast: {forecast(d, force=args.force)}")
    except AlreadyIssued as e:
        print(f"skip: already issued {e}")
    return 0


def cmd_score(args) -> int:
    from .live import score_ready

    for p in score_ready():
        print(f"scored: {p}")
    return 0


def cmd_solar(args) -> int:
    from .features import load_tables
    from .solar import load_era5, monthly, subtract_baseline, write_monthly

    t, e = load_tables(), load_era5()
    v1 = monthly(t, e, boot=args.boot, irr="ghi")
    print(f"solar v1 (pre-registered): {len(v1)} months -> {write_monthly(v1)}")
    v2 = subtract_baseline(monthly(t, e, boot=args.boot, irr="gti"))
    print(f"solar v2 (tilted plane, minus 2022 sunshine response): -> {write_monthly(v2, name='solar_monthly_v2.json')}")
    return 0


def cmd_story(args) -> int:
    from .features import load_tables
    from .story import write_story

    print(f"story: {write_story(load_tables())}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="gridmd")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest", help="download sources into data/")
    i.add_argument("what", choices=["load", "prices", "weather", "era5"])
    i.add_argument("--from", dest="from_", default="2021-12-01")
    i.add_argument("--recent", type=int, default=0, help="only the last N days (merged into the existing table)")
    b = sub.add_parser("backtest", help="build the dataset, tune on validation, or test once")
    b.add_argument("stage", choices=["dataset", "tune", "test"])
    r = sub.add_parser("retrain", help="refit the model on all observed days (monthly, or with --force)")
    r.add_argument("--force", action="store_true")
    fc = sub.add_parser("forecast", help="issue the forecast for tomorrow (or for --date's next day)")
    fc.add_argument("--date", help="issue date D (forecasts D+1)")
    fc.add_argument("--force", action="store_true")
    sub.add_parser("score", help="score forecasts whose target day is complete")
    so = sub.add_parser("solar", help="estimate hidden and visible solar capacity by month")
    so.add_argument("--boot", type=int, default=200)
    sub.add_parser("story", help="write data/story.json for the story page")
    args = p.parse_args(argv)
    return {"story": cmd_story, "solar": cmd_solar, "ingest": cmd_ingest, "backtest": cmd_backtest, "retrain": cmd_retrain, "forecast": cmd_forecast,
            "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
