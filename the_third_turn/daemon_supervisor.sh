#!/bin/bash
# Keep exactly one the_third_turn live-ledger daemon alive for the life of this
# container. Respawns the daemon within ~60s if it crashes. A flock guarantees a
# single supervisor even if SessionStart fires more than once.
#
# NOTE: this survives daemon *crashes*, not container *reclaim* — when the cloud
# container is reclaimed on idle, this dies too. True 24/7 needs the GitHub Actions
# runner (see scripts/sentinel_watch.py pattern). SessionStart relaunches this on
# every new container, which is the best an in-container process can do.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-/home/user/project}"
cd "$ROOT" || exit 1
LOG="$ROOT/the_third_turn/output/daemon.log"
LOCK="$ROOT/the_third_turn/output/.supervisor.lock"

exec 9>"$LOCK"
flock -n 9 || exit 0          # another supervisor already owns the ledger

daemon_alive() {
  for pid in $(pgrep -f "live_engine.py" 2>/dev/null); do
    [ "$(cat "/proc/$pid/comm" 2>/dev/null)" = "python3" ] && return 0
  done
  return 1
}

while true; do
  if ! daemon_alive; then
    printf '[%s] supervisor: daemon down — relaunching\n' "$(date -u +%H:%M:%S)" >> "$LOG"
    nohup python3 the_third_turn/live_engine.py >> "$LOG" 2>&1 &
  fi
  sleep 60
done
