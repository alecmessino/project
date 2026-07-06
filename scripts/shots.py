#!/usr/bin/env python
"""Render the built docs/*.html pages to PNGs (desktop + mobile) for visual design review.

A committed, repeatable visual-QA harness: it renders the real shipped artifacts so design can be
judged by looking, and cross-page drift caught. Uses the venv's Playwright + Chromium and fails
loudly if no browser is available (it never emits blank/placeholder images).

    .venv/bin/python scripts/shots.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "artifacts" / "shots"

# (label, file, query) — the After-Tax Review is captured at its working-paper sections with populated state.
PAGES = [
    ("taxlab-portfolio", "taxlab.html", "?view=portfolio&state=IL"),
    ("taxlab-recs", "taxlab.html", "?view=recs&state=IL"),
    ("taxlab-state", "taxlab.html", "?view=state&state=IL"),
    ("taxlab-review", "taxlab.html", "?view=review&state=IL&port=2000000"),
    ("leakage", "leakage.html", ""),
    ("ledger", "ledger.html", ""),
    ("thesis", "thesis.html", ""),
    ("index", "index.html", ""),
    ("tearsheet", "tearsheet.html", ""),
    ("equities", "equities.html", ""),
]
VIEWPORTS = [("desktop", 1280, 900), ("mobile", 390, 844)]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print(f"FATAL: playwright not importable ({e}). Use the venv: .venv/bin/python scripts/shots.py",
              file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            print(f"FATAL: could not launch Chromium ({str(e)[:200]}). "
                  f"Run `.venv/bin/playwright install chromium`.", file=sys.stderr)
            return 2
        for label, fname, query in PAGES:
            src = DOCS / fname
            if not src.exists():
                print(f"  skip {label}: {src} missing", file=sys.stderr)
                continue
            url = src.as_uri() + query
            for vname, w, h in VIEWPORTS:
                page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
                page.goto(url, wait_until="load")
                page.wait_for_timeout(600)  # let the inline init() render
                out = OUT / f"{label}-{vname}.png"
                page.screenshot(path=str(out), full_page=True)
                page.close()
                written.append(out)
                print(f"  wrote {out.relative_to(ROOT)}")
        browser.close()
    print(f"\n{len(written)} screenshots -> {OUT.relative_to(ROOT)}")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
