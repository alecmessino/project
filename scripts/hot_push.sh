#!/usr/bin/env bash
#
# Hot-push ONLY the live data payload(s) to the gh-pages branch on a tight loop,
# so the dashboard streams fresh numbers without waiting for a full GitHub Actions
# rebuild. Run it ALONGSIDE your live ingestion (scripts/live_run.py), which keeps
# rewriting docs/live_market_state.json every cycle:
#
#     # terminal 1 — ingest Bovada + recompute fair value into the JSON
#     MRBET_GAME=config/games/nyk_sas_2026-06-03.yaml python scripts/live_run.py
#
#     # terminal 2 — fire the JSON to the branch the moment it changes
#     scripts/hot_push.sh                 # 20s loop, current branch
#     scripts/hot_push.sh 15 claude/mean-reversion-betting-system-mWBM5
#
# Args:  [interval_seconds]  [branch]   (defaults: 20s, current branch)
# Stop with Ctrl-C.
#
# Only docs/live_market_state.json + docs/odds_history.json are committed, so this
# never touches code and never triggers the heavier board/poll workflows ([skip ci]).
# Heads-up: a commit per tick bloats history fast (~180/hr) — fine for one game
# night; for local-only testing prefer the localhost path (see README / --help).
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,30p' "$0"; exit 0
fi

cd "$(git rev-parse --show-toplevel)"
INTERVAL="${1:-20}"
BRANCH="${2:-$(git branch --show-current)}"
FILES=(docs/live_market_state.json docs/odds_history.json)

echo "hot-push: every ${INTERVAL}s -> origin/${BRANCH}   files: ${FILES[*]}"
echo "(Ctrl-C to stop)"

while true; do
  # Stage only the live files; skip the cycle if nothing changed.
  git add -- "${FILES[@]}" 2>/dev/null || true
  if ! git diff --cached --quiet -- "${FILES[@]}" 2>/dev/null; then
    git -c commit.gpgsign=false \
        -c user.name="github-actions[bot]" \
        -c user.email="github-actions[bot]@users.noreply.github.com" \
        commit -q -m "data: live market stream $(date -u +%H:%M:%S) [skip ci]" \
        -- "${FILES[@]}"
    # Push with bounded exponential backoff on transient network failures.
    for i in 1 2 3 4; do
      if git push -q origin "HEAD:${BRANCH}"; then
        echo "pushed $(date -u +%H:%M:%S)"
        break
      fi
      wait=$((2 ** i)); echo "push failed — retry $i in ${wait}s"; sleep "$wait"
    done
  fi
  sleep "$INTERVAL"
done
