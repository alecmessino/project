"""Tiny .env loader (no dependency on python-dotenv).

Reads key=value lines from a local .env into os.environ without overwriting
anything already set, and aliases THE_ODDS_API_KEY -> ODDS_API_KEY so the live
provider (which reads ODDS_API_KEY) picks up the forward-capture key. The .env
file is gitignored; this never prints values.
"""

from __future__ import annotations

import os
import pathlib


def load_env(path: str | pathlib.Path = ".env") -> None:
    p = pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
    # The provider reads ODDS_API_KEY; accept THE_ODDS_API_KEY as an alias.
    if "ODDS_API_KEY" not in os.environ and os.environ.get("THE_ODDS_API_KEY"):
        os.environ["ODDS_API_KEY"] = os.environ["THE_ODDS_API_KEY"]


def has_odds_key() -> bool:
    """True if a key is available — without revealing it."""
    return bool(os.environ.get("ODDS_API_KEY") or os.environ.get("THE_ODDS_API_KEY"))
