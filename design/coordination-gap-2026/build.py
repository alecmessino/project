#!/usr/bin/env python3
"""Build the Coordination Gap print collateral: self-contained HTML, then PDF.

Two things this does that matter:

  1. Inlines Satoshi and Erode as data URIs. These sheets are emailed, forwarded by an attorney,
     and printed on someone else's machine. A silent fallback to Helvetica would change the one
     thing the layout is built around, so the faces travel inside the file. Same reasoning as
     design/hero-watershed-2026/inline-fonts.py, which is where the pattern comes from.

  2. Refuses to build if an em dash or en dash survives in the copy. The house voice does not use
     them, and a stray one arrives via paste rather than by decision, so it is cheaper to fail the
     build than to proofread two pages of dense type every time a figure is revised.

    python3 design/coordination-gap-2026/build.py

Writes collateral/*.html (self-contained) and collateral/*.pdf (US Letter, backgrounds on).
"""
from __future__ import annotations

import base64
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "src" / "drift" / "web" / "fonts"
DIST = HERE / "collateral"
SHEETS = ["onepager-a-coordination-gap.html", "onepager-b-outlast-the-handoff.html"]
# Screen document: same two faces, own stylesheet, no PDF.
REGISTER = "evidence-register.html"
FACES = {"__SATOSHI__": "Satoshi-Variable.woff2", "__ERODE__": "Erode-Variable.woff2"}
BANNED = {"—": "em dash", "–": "en dash"}


def find_chromium() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    for path in sorted(pathlib.Path("/opt/pw-browsers").glob("chromium*/chrome-linux/chrome")):
        return str(path)
    return None


def lint(name: str, html: str) -> list[str]:
    """Banned punctuation, reported with enough context to find it."""
    problems = []
    # Only lint prose, not the base64 font blobs or the stylesheet.
    prose = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    for char, label in BANNED.items():
        for m in re.finditer(re.escape(char), prose):
            snippet = prose[max(0, m.start() - 45): m.start() + 45].replace("\n", " ")
            problems.append(f"{name}: {label} in ...{snippet.strip()}...")
    return problems


def main() -> int:
    blobs = {}
    for token, filename in FACES.items():
        src = FONTS / filename
        if not src.exists():
            print(f"!! missing font {src}", file=sys.stderr)
            return 1
        blobs[token] = base64.b64encode(src.read_bytes()).decode("ascii")

    css = (HERE / "_print.css").read_text(encoding="utf-8")
    for token, blob in blobs.items():
        css = css.replace(token, blob)

    DIST.mkdir(exist_ok=True)
    chromium = find_chromium()
    if chromium is None:
        print("!! no chromium on PATH; writing HTML only", file=sys.stderr)

    problems: list[str] = []
    built: list[pathlib.Path] = []

    for sheet in SHEETS:
        raw = (HERE / sheet).read_text(encoding="utf-8")
        problems += lint(sheet, raw)
        html = raw.replace(
            '<link rel="stylesheet" href="_print.css">', f"<style>\n{css}\n</style>"
        )
        out = DIST / sheet
        out.write_text(html, encoding="utf-8")
        built.append(out)

    reg_src = HERE / REGISTER
    if reg_src.exists():
        reg = reg_src.read_text(encoding="utf-8")
        problems += lint(REGISTER, reg)
        for token, blob in blobs.items():
            reg = reg.replace(token, blob)
        (DIST / REGISTER).write_text(reg, encoding="utf-8")

    if problems:
        print("!! banned punctuation, build stopped:", file=sys.stderr)
        for p in problems:
            print(f"   {p}", file=sys.stderr)
        return 1

    if chromium is None:
        return 0

    for out in built:
        pdf = out.with_suffix(".pdf")
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run(
                [
                    chromium, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--user-data-dir={profile}",
                    "--no-pdf-header-footer", "--print-to-pdf-no-header",
                    f"--print-to-pdf={pdf}", out.as_uri(),
                ],
                check=True, capture_output=True, timeout=180,
            )
        print(f"   {pdf.relative_to(HERE.parents[1])}  {pdf.stat().st_size // 1024} KB")

    print("built", len(built), "sheets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
