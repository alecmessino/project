#!/usr/bin/env python3
"""Render the hero flock to src/drift/web/img/hero-flock.svg.

Unlike the house mark (scripts/build_heron.py), this IS a deployed asset: it lives under web/img/
so sync_docs.py copies it into docs/img/ and the ?hero=flock control arm can load it with a plain
<img>. That difference is the point. The heron is one bird, rare, and kept out of the web tree so
no page can reach for it as texture; the flock is many birds, deliberately anonymous, and texture
is the only thing it is for.

Run this when src/drift/flock.py changes, then commit the result and re-run sync_docs.py.

    python3 scripts/build_flock.py

Project: 🪵 Driftwood.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift.flock import render_svg  # noqa: E402

OUT = ROOT / "src" / "drift" / "web" / "img" / "hero-flock.svg"


def main() -> None:
    svg = render_svg()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"OK: hero flock -> {OUT.relative_to(ROOT)}  ({len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
