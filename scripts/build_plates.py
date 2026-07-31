#!/usr/bin/env python3
"""Render the Canonical Survey Library to src/drift/web/img/plates/*.svg.

The ten plates are committed static assets, exactly like driftwood.css and docs/fonts/ — the
nightly job does not regenerate them and nothing at request time computes them. Run this only
when src/drift/plates.py changes, then commit the result; sync_docs.py copies them into docs/.

    python3 scripts/build_plates.py

The generator is deterministic, so a run with no source change rewrites the files byte-for-byte
and leaves an empty diff. If this produces a diff you did not expect, the geometry moved.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from drift.plates import build_all, render_svg  # noqa: E402

OUT = ROOT / "src" / "drift" / "web" / "img" / "plates"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for plate in build_all():
        svg = render_svg(plate)
        (OUT / f"{plate.name}.svg").write_text(svg, encoding="utf-8")
        print(f"   {plate.name:11} {plate.structure:34} {len(svg):>7,} bytes")
    print(f"OK: {len(list(OUT.glob('*.svg')))} canonical plates -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
