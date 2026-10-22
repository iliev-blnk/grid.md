#!/usr/bin/env bash
# Run by gridmd-failed.service when the daily run fails: sends the tail of its log to Telegram.
# Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from ~/.claude/telegram.env; does nothing without them.
set -uo pipefail
ENV_FILE="$HOME/.claude/telegram.env"
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
[ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ] || exit 0

log=$(journalctl --user -u gridmd.service -n 15 -o cat --no-pager | tail -c 3500)
text="⚠️ grid.md daily run failed ($(TZ=Europe/Chisinau date '+%F %H:%M'))"$'\n\n'"${log}"$'\n\n'"journalctl --user -u gridmd.service"

curl -sS --max-time 15 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=${text}" \
  -d disable_web_page_preview=true >/dev/null
