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

# NOTE: the local daemon supervisor is intentionally NOT launched here anymore. The
# GitHub Actions runner (the_third_turn_live.yml) is now the authoritative 24/7 banker
# and commits the panels to the branch; a local session daemon only duplicated it and
# dirtied the tracked panels, causing git friction. Re-add only for local debugging.

# Editable install with the dev extra (pytest). Idempotent + cache-friendly.
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -e ".[dev]"

# pyproject sets pythonpath=["src"], so `pytest` works from the repo root.
