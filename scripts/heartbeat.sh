#!/usr/bin/env bash
# Live heartbeat monitor for the chaos demo.
# Also picks up status codes from req() in the left terminal.
#
# Usage:  bash scripts/heartbeat.sh        (right terminal)

LOG=/tmp/demo.log
> "$LOG"

GREEN='\033[32;1m'
RED='\033[31;1m'
RESET='\033[0m'
LAST_SIZE=0

while true; do
  TS=$(date +%H:%M:%S)

  # --- print any req() entries that landed in the log ---
  CURR_SIZE=$(stat -f%z "$LOG" 2>/dev/null || echo 0)
  if [ "$CURR_SIZE" -gt "$LAST_SIZE" ]; then
    tail -c +"$((LAST_SIZE + 1))" "$LOG" 2>/dev/null
    LAST_SIZE=$CURR_SIZE
  fi

  # --- health poll ---
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health 2>/dev/null)

  if [ -z "$CODE" ] || [ "$CODE" = "000" ]; then
    printf "%s  ${RED}♥ REFUSED${RESET}\n" "$TS"
  elif [[ "$CODE" == 2* ]]; then
    printf "%s  ${GREEN}♥ %s${RESET}\n" "$TS" "$CODE"
  else
    printf "%s  ${RED}♥ %s${RESET}\n" "$TS" "$CODE"
  fi

  sleep 1
done
