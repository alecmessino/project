#!/usr/bin/env python3
"""Render the house mark to design/house-mark/heron-engraving.svg.

The master is a committed static asset — the site build never regenerates it. Run this only when
src/drift/heron.py changes, then commit the result.

It moved out of src/drift/web/img/ on 2026-08-06, when the hero watershed replaced the heron on
the homepage and the mark came off the website entirely. It is NOT a deployed asset any more, so
sync_docs.py no longer copies it and it must not live under web/. The mark itself is unchanged and
still governed by OPERATIONS.md: it is the house mark for print and enduring applications — an
AWOR cover, a flagship essay, a client folder, an embossed die — and this file remains the one
master every one of those takes.

    python3 scripts/build_heron.py

Project: 🪵 Driftwood.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift.heron import render_svg  # noqa: E402

OUT = ROOT / "design" / "house-mark" / "heron-engraving.svg"


def main() -> None:
    svg = render_svg()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"OK: house mark -> {OUT.relative_to(ROOT)}  ({len(svg) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
