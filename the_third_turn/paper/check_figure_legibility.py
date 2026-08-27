#!/usr/bin/env python3
"""Regression gate: no figure may ship text below the legibility floor.

    python3 the_third_turn/paper/check_figure_legibility.py

WHY THIS EXISTS (2026-08-27). Figures are raster PNGs dropped into a fixed text
measure, so the page rescales whatever the generator produced. Authoring a
figure 11in wide and displaying it at 5.96in shrinks every label by 0.54x, and
nothing in the build noticed: all sixteen figure functions were shipping text
between 3.3 and 8.3pt on paper.

The gate reads the generators, not the images, because font size is a property of
the source and the scale factor is a property of the canvas width. Both are
statically knowable, so this needs no rendering and cannot drift.

Rule: canvas width must equal figstyle.FULL_W or HALF_W (scale 1.0), and every
explicit font size must be at least figstyle.FS_MIN.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle  # noqa: E402

GENERATORS = [HERE / "make_figures.py",
              HERE / "make_paper2_figures.py",
              HERE / "make_concept_figures.py",
              HERE.parent / "docs" / "make_companion_figures.py"]
ALLOWED_W = {round(figstyle.FULL_W, 2), round(figstyle.HALF_W, 2)}
TOL = 0.06


def check(path: Path) -> list[str]:
    src = path.read_text()
    tree = ast.parse(src)
    problems = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        seg = ast.get_source_segment(src, node) or ""
        m = re.search(r"figsize=\(\s*([\d.]+)\s*,\s*([\d.]+)", seg)
        if not m:
            continue
        w = float(m.group(1))
        if not any(abs(w - a) <= TOL for a in ALLOWED_W):
            problems.append(f"{path.name}:{node.name}: canvas {w}in is neither FULL_W "
                            f"({figstyle.FULL_W:.2f}) nor HALF_W ({figstyle.HALF_W:.2f}); "
                            f"internal text would scale by {figstyle.FULL_W / w:.2f}x")
        for fs in (float(x) for x in re.findall(r"fontsize=([\d.]+)", seg)):
            if fs < figstyle.FS_MIN:
                problems.append(f"{path.name}:{node.name}: fontsize={fs} is below the "
                                f"{figstyle.FS_MIN}pt floor")
    return problems



def check_rendered(dirs) -> list[str]:
    """The decisive test: measure the PNG the page will actually scale.

    Source figsize is necessary but not sufficient -- a tight bounding box, an
    overflowing artist or a stale file all change the saved extent, and the extent
    is what sets on-page text size.
    """
    from PIL import Image
    problems = []
    for d in dirs:
        for png in sorted(d.glob("*.png")):
            with Image.open(png) as im:
                dpi = im.info.get("dpi", (200, 200))[0] or 200
            widths = {"raster": im.size[0] / dpi}
            # The manuscript embeds the SVG master, so that is the rendition whose
            # width actually sets on-page text size; the PNG is the fallback. Both
            # come off one converged canvas and should agree, but they are measured
            # by different renderers, so measure both rather than assuming.
            svg = png.with_suffix(".svg")
            if svg.is_file():
                head = svg.read_text(errors="ignore")[:600]
                m = re.search(r'width="([\d.]+)pt"', head)
                if m:
                    widths["vector"] = float(m.group(1)) / 72
            for kind, eff in widths.items():
                onpage = figstyle.FS_MIN * figstyle.FULL_W / eff
                if onpage < figstyle.FS_MIN - 0.05:
                    problems.append(f"{png.stem}: {kind} master saved {eff:.2f}in wide, so "
                                    f"{figstyle.FS_MIN}pt text renders at {onpage:.2f}pt "
                                    f"on the page")
    return problems

def main() -> int:
    problems: list[str] = []
    checked = 0
    for g in GENERATORS:
        if not g.exists():
            print(f"  SKIP {g.name} (absent)")
            continue
        found = check(g)
        n = len(re.findall(r"figsize=\(", g.read_text()))
        checked += n
        problems += found
        if not found:
            print(f"  OK   {g.name:<28} {n} figure(s) at scale 1.0, all text >= {figstyle.FS_MIN}pt")
    rendered = check_rendered([HERE / "figures", HERE.parent / "docs" / "figures"])
    if not rendered:
        print(f"  OK   every saved figure is {figstyle.FULL_W:.2f}in wide (scale 1.0)")
    problems += rendered
    for msg in sorted(set(problems)):
        print(f"  FAIL {msg}", file=sys.stderr)
    print(f"\n{checked - len({p.split(':')[1] for p in problems})}/{checked} figures meet the legibility contract")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
