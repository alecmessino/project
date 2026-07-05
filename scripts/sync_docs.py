#!/usr/bin/env python3
"""Regenerate docs/*.html from the src/drift/web/*.html templates, re-injecting the
window.__STATE__ data already present in the current docs output. Lets us edit the
static template structure without re-running the (network-bound) drift CLI: the live
data is preserved verbatim, only the surrounding HTML/CSS/JS is refreshed.

Run from repo root:  python3 scripts/sync_docs.py
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
PLACEHOLDER = "/*__STATE__*/null/*__END__*/"

# template -> docs output
PAIRS = {
    "hub.html": "index.html",
    "index.html": "equities.html",
    "report.html": "equities_case_studies.html",
    "leakage.html": "leakage.html",
    "statemap.html": "statemap.html",
    "concentration.html": "concentration.html",
    "ledger.html": "ledger.html",
    "tearsheet.html": "tearsheet.html",
    "taxlab.html": "taxlab.html",
    "thesis.html": "thesis.html",
}
STATE_RE = re.compile(r"window\.__STATE__ = (.*?);\s*\n")


def main() -> int:
    bad = 0
    for tpl, out in PAIRS.items():
        tpl_p, out_p = WEB / tpl, DOCS / out
        template = tpl_p.read_text()
        if template.count(PLACEHOLDER) != 1:
            print(f"!! {tpl}: expected exactly 1 state placeholder, found "
                  f"{template.count(PLACEHOLDER)}")
            bad += 1
            continue
        m = STATE_RE.search(out_p.read_text())
        if not m:
            print(f"!! {out}: could not find existing window.__STATE__ data")
            bad += 1
            continue
        data = m.group(1)
        rendered = template.replace(PLACEHOLDER, data)
        out_p.write_text(rendered)
        print(f"   {tpl:16} -> docs/{out:30} ({len(rendered)} bytes, data {len(data)})")
    # Plain static assets (not templated) — copy them through.
    for asset in ("driftwood.css", "dw-context.js", "about.html", "philosophy.html"):
        (DOCS / asset).write_text((WEB / asset).read_text())
        print(f"   {asset:15} -> docs/{asset} (copied)")
    # Binary assets (e.g. the founder headshot) — copy through only if present, so the About page's
    # <img> resolves once the file is dropped in. Optional: absent is fine (the page hides it).
    for asset in ("Headshot.jpg",):
        src = WEB / asset
        if src.exists():
            (DOCS / asset).write_bytes(src.read_bytes())
            print(f"   {asset:15} -> docs/{asset} (copied, binary)")
    if bad:
        print(f"FAILED: {bad} file(s) had problems")
        return 1
    print("OK: docs regenerated from templates, data preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
