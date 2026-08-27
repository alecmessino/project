#!/usr/bin/env python3
"""Release gate: figures ship as vector, or as raster at production resolution.

    python3 the_third_turn/paper/check_figure_output.py [pdf ...]

WHY THIS EXISTS (2026-08-27). The built PDFs embedded every figure as a PNG at
roughly 195-201 PPI. That is a production defect: journals ask for 300 PPI for
halftones and vector for line art, and all sixteen of these figures are line art
generated from code, where "we only have a raster" is a choice rather than a
constraint.

So every generator now writes an SVG and a PDF master beside the PNG from the
same converged canvas (figstyle.save_at_measure), and paper/build_pdf.py points
the manuscript at the SVG, which Chromium prints as paths and embedded text
rather than rasterizing. This gate holds that in place, and is deliberately
written to accept either outcome:

  * VECTOR   -- the document embeds no raster image at all; or
  * RASTER   -- every embedded image is at least RASTER_PPI_FLOOR PPI.

Either is publishable. Silently sliding back to 200 PPI is not.

The gate also checks that a vector master exists for every figure the sources
reference, since the masters are the artifact a journal's production desk asks
for and a missing one is invisible until they ask.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle  # noqa: E402

ROOT = HERE.parent
DOCS = [HERE / f"{s}.md" for s in (
    "paper1", "paper1_anon", "paper2", "paper2_anon",
    "paper2_journal", "paper2_journal_anon",
    "paper2_supplement", "paper2_supplement_anon")]
DOCS.append(ROOT / "docs" / "VISUAL_COMPANION.md")

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def masters(doc: Path) -> list[str]:
    """Every figure a document references is missing a vector master."""
    if not doc.is_file():
        return []
    out = []
    for src in IMG_RE.findall(doc.read_text()):
        ref = (doc.parent / src)
        for ext in figstyle.VECTOR_FMTS:
            if not ref.with_suffix(f".{ext}").is_file():
                out.append(f"{doc.name}: {src} has no .{ext} master")
    return out


def figure_count(pdf: Path) -> int:
    """How many figures the markdown behind this PDF references."""
    doc = pdf.with_suffix(".md")
    return len(IMG_RE.findall(doc.read_text())) if doc.is_file() else 0


def embedding(pdf: Path) -> tuple[str, list[str]]:
    """Classify one PDF's figure embedding and report anything below the floor."""
    rows = subprocess.run(["pdfimages", "-list", str(pdf)],
                          capture_output=True, text=True, check=True).stdout.splitlines()
    ppis, low = [], []
    for r in rows[2:]:
        f = r.split()
        if len(f) < 15:
            continue
        try:
            x, y = float(f[12]), float(f[13])
        except ValueError:
            continue
        ppis.append(min(x, y))
        if min(x, y) < figstyle.RASTER_PPI_FLOOR:
            low.append(f"{pdf.name}: page {f[0]} embeds a raster {f[2]} at "
                       f"{min(x, y):.0f} PPI, below the "
                       f"{figstyle.RASTER_PPI_FLOOR} PPI floor")
    if not ppis:
        n = figure_count(pdf)
        return (f"vector -- {n} figure(s), no raster objects" if n
                else "no figures"), []
    return f"raster, {min(ppis):.0f}-{max(ppis):.0f} PPI", low


def main(argv: list[str]) -> int:
    pdfs = [Path(a) for a in argv] or sorted(
        p for p in [d.with_suffix(".pdf") for d in DOCS] if p.is_file())
    problems: list[str] = []
    for doc in DOCS:
        problems += masters(doc)
    if not problems:
        print(f"  OK   every referenced figure has "
              f"{'/'.join('.' + e for e in figstyle.VECTOR_FMTS)} masters")
    for pdf in pdfs:
        if not pdf.is_file():
            problems.append(f"{pdf}: not built")
            continue
        kind, low = embedding(pdf)
        problems += low
        print(f"  {'FAIL' if low else 'OK  '} {pdf.name:<28} {kind}")
    for msg in sorted(set(problems)):
        print(f"  FAIL {msg}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
