#!/usr/bin/env bash
# Daily pipeline (run by the gridmd.timer systemd user unit): refresh data, retrain monthly,
# issue tomorrow's forecast inside the 09:00–23:00 window, score finished days, commit and push.
set -euo pipefail
cd "$(dirname "$0")/.."
S=.venv/bin/gridmd
$S ingest load --recent 14
$S ingest weather --recent 14
$S retrain
$S forecast
$S score
git add data/load.csv.gz data/weather.csv.gz forecasts scores models
if ! git diff --cached --quiet; then
  git commit -q -m "Daily update $(TZ=Europe/Chisinau date +%F)"
  git pull --rebase -q
  git push -q
fi
