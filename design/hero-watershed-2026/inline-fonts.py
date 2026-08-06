#!/usr/bin/env python3
"""Inline Satoshi + Erode into the hero variants so each file opens with no network.

The variants are self-contained by requirement: they are dropped into a live hero slot and judged
there, and a silent fallback to Helvetica would make the type — the thing the drawing sits behind —
the wrong shape. So the two roman variable faces are carried as data URIs.

Idempotent: re-run after editing a variant or after replacing a woff2. It rewrites whatever is
currently in the two @font-face src slots, whether that is the __SATOSHI__/__ERODE__ placeholder or
a previously inlined blob.

    python3 design/hero-watershed-2026/inline-fonts.py
"""
import base64
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "src" / "drift" / "web" / "fonts"
VARIANTS = sorted(HERE.glob("variant-*.html"))
FACES = {"Satoshi": "Satoshi-Variable.woff2", "Erode": "Erode-Variable.woff2"}


def main() -> int:
    payload = {}
    for family, filename in FACES.items():
        src = FONTS / filename
        if not src.exists():
            print(f"!! missing {src}", file=sys.stderr)
            return 1
        payload[family] = base64.b64encode(src.read_bytes()).decode("ascii")

    for page in VARIANTS:
        html = page.read_text(encoding="utf-8")
        for family, b64 in payload.items():
            # Match this family's @font-face src slot: placeholder or an existing base64 blob.
            pattern = re.compile(
                r"(@font-face\{font-family:'" + family + r"'.*?base64,)([^)]*)(\))",
                re.DOTALL,
            )
            html, n = pattern.subn(lambda m: m.group(1) + b64 + m.group(3), html)
            if n != 1:
                print(f"!! {page.name}: expected 1 {family} face, found {n}", file=sys.stderr)
                return 1
        page.write_text(html, encoding="utf-8")
        print(f"   inlined 2 faces -> {page.name} ({len(html) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
