#!/usr/bin/env python3
"""Regression check: the title block must sit inside the printable measure.

    python3 the_third_turn/paper/check_title_margins.py [file.pdf ...]

WHY THIS EXISTS (2026-08-23). After the papers were retitled, the Paper 2
supplement's title -- three lines at 17pt -- was set flush to both margins, with
about 3pt of slack a side. It never crossed the page box, so a naive
"does anything exceed the MediaBox" test passed, but at that size it reads as
clipped and was reported as clipped by a reader rendering it independently.

The lesson is that flush is not the same as inside. This check therefore demands
real breathing room rather than mere containment, and it measures the TITLE BLOCK
only: justified body text legitimately reaches the full measure, so including it
would make the check vacuous.

Geometry comes from the glyph boxes Poppler reports, not from the CSS, so it
tests the artifact a referee opens rather than our intent.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# @page size Letter, margin 24mm 22mm  ->  22mm = 62.36pt each side.
MARGIN_PT = 62.36
# Required clear space between the title block and the margin. 3pt reads as
# clipped; 18pt (~6mm) is unambiguous at any zoom.
MIN_SLACK_PT = 18.0
# The title block occupies the top of page 1.
TITLE_BAND_PT = 120.0

WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')


def check(pdf: Path) -> list[str]:
    xml = subprocess.run(["pdftotext", "-bbox", "-f", "1", "-l", "1", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    page = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', xml)
    if not page:
        return [f"{pdf.name}: could not read page geometry"]
    pw = float(page.group(1))
    left, right = MARGIN_PT, pw - MARGIN_PT

    band = [(float(a), float(b), float(c), t) for a, b, c, _d, t in
            (m.groups() for m in WORD.finditer(xml)) if float(b) < TITLE_BAND_PT]
    if not band:
        return [f"{pdf.name}: no text found in the title band"]

    xmin = min(w[0] for w in band)
    xmax = max(w[2] for w in band)
    ls, rs = xmin - left, right - xmax
    problems = []
    if ls < MIN_SLACK_PT:
        problems.append(f"{pdf.name}: title block {ls:.1f}pt from the left margin "
                        f"(need {MIN_SLACK_PT:.0f}pt)")
    if rs < MIN_SLACK_PT:
        problems.append(f"{pdf.name}: title block {rs:.1f}pt from the right margin "
                        f"(need {MIN_SLACK_PT:.0f}pt)")
    if not problems:
        print(f"  OK   {pdf.name:<32} title block slack L={ls:5.1f}pt R={rs:5.1f}pt")
    return problems


def main(argv: list[str]) -> int:
    here = Path(__file__).resolve().parent
    pdfs = [Path(a) for a in argv[1:]] or sorted(
        p for p in here.glob("*.pdf") if not p.name.endswith(".raw.pdf"))
    if not pdfs:
        sys.exit("check_title_margins: no PDFs found")
    problems: list[str] = []
    for p in pdfs:
        problems += check(p)
    for msg in problems:
        print(f"  FAIL {msg}", file=sys.stderr)
    print(f"\n{len(pdfs) - len({m.split(':')[0] for m in problems})}/{len(pdfs)} title blocks within the safe measure")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
