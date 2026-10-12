#!/usr/bin/env bash
set -euo pipefail
d="$HOME/.config/systemd/user"
mkdir -p "$d"
cp "$(dirname "$0")/gridmd.service" "$(dirname "$0")/gridmd.timer" "$d/"
systemctl --user daemon-reload
systemctl --user enable --now gridmd.timer
systemctl --user list-timers gridmd.timer --no-pager
