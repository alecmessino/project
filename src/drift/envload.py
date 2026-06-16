"""Tiny .env loader (no python-dotenv dependency).

Reads key=value lines from a local .env into os.environ without overwriting
anything already set. The .env file is gitignored; this never prints values.
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
