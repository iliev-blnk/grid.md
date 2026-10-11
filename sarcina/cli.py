from __future__ import annotations

import argparse
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

        h = build_load(start, end)
        print(f"load: {len(h)} hourly rows {h['day'].min()}..{h['day'].max()}")
    elif args.what == "weather":
        from .weather import build_weather

        w = build_weather(max(start, date(2022, 1, 1)), end)
        print(f"weather: {len(w)} rows, {w['site'].nunique()} sites")
    else:
        print("prices: deferred (no source whose licence allows public reuse; see spec amendment 2)")
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sarcina")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest", help="download sources into data/")
    i.add_argument("what", choices=["load", "prices", "weather"])
    i.add_argument("--from", dest="from_", default="2021-12-01")
    i.add_argument("--recent", type=int, default=0, help="only the last N days (merged into the existing table)")
    args = p.parse_args(argv)
    return {"ingest": cmd_ingest}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
