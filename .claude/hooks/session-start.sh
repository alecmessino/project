#!/bin/bash
# SessionStart hook: install mrbet + dev deps so pytest runs out of the box.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Run asynchronously so the session starts without waiting on the install.
# Trade-off: Claude may briefly run before deps finish on the very first session.
echo '{"async": true, "asyncTimeout": 300000}'

cd "${CLAUDE_PROJECT_DIR:-.}"

# Keep the live-ledger daemon up for the life of this container. The supervisor is
# idempotent (flock-guarded) and self-heals the daemon on crash, so the ledger comes
# back automatically after a container reset instead of waiting on a hand-restart.
# (Survives crashes, not container reclaim — true 24/7 is the Actions runner.)
chmod +x "${CLAUDE_PROJECT_DIR:-.}/the_third_turn/daemon_supervisor.sh" 2>/dev/null || true
setsid nohup "${CLAUDE_PROJECT_DIR:-.}/the_third_turn/daemon_supervisor.sh" >/dev/null 2>&1 < /dev/null &

# Editable install with the dev extra (pytest). Idempotent + cache-friendly.
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -e ".[dev]"

# pyproject sets pythonpath=["src"], so `pytest` works from the repo root.
