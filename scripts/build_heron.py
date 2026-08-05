#!/usr/bin/env python3
"""Render the house mark to src/drift/web/img/heron-engraving.svg.

The master is a committed static asset, exactly like driftwood.css and the survey plates — the
site build never regenerates it. Run this only when src/drift/heron.py changes, then commit the
result; sync_docs.py copies it into docs/.

    python3 scripts/build_heron.py

Project: 🪵 Driftwood.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift.heron import render_svg  # noqa: E402

OUT = ROOT / "src" / "drift" / "web" / "img" / "heron-engraving.svg"


def main() -> None:
    svg = render_svg()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"OK: house mark -> {OUT.relative_to(ROOT)}  ({len(svg) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
