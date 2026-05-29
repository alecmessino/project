#!/bin/bash
# SessionStart hook: install mrbet + dev deps so pytest runs out of the box.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Editable install with the dev extra (pytest). Idempotent + cache-friendly.
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -e ".[dev]"

# pyproject sets pythonpath=["src"], so `pytest` works from the repo root.
