"""Minimal .env loader (no dependency) — mirrors mrbet's envload pattern.

Loads ``the_third_turn/.env`` (git-ignored) into ``os.environ`` if present, so
secrets like DISCORD_WEBHOOK_URL / ODDS_API_KEY never have to be committed or
exported by hand. Values already in the environment win (explicit export > file).
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def load_env(path: Path | str = ENV_PATH) -> None:
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:      # explicit env wins over the file
            os.environ[key] = val
