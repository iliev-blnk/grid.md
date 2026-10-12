#!/usr/bin/env bash
set -euo pipefail
d="$HOME/.config/systemd/user"
mkdir -p "$d"
cp "$(dirname "$0")/sarcina.service" "$(dirname "$0")/sarcina.timer" "$d/"
systemctl --user daemon-reload
systemctl --user enable --now sarcina.timer
systemctl --user list-timers sarcina.timer --no-pager
