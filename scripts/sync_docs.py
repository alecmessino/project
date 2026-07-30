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

# Build-time tokens replaced from a single source (drift.site) so firm facts have one home.
sys.path.insert(0, str(ROOT / "src"))
from drift.site import firm_anchor_html  # noqa: E402

FIRM_ANCHOR_TOKEN = "<!--FIRM_ANCHOR-->"


def _inject_tokens(html: str) -> str:
    """Replace build-time tokens with their single-source rendered value."""
    if FIRM_ANCHOR_TOKEN in html:
        html = html.replace(FIRM_ANCHOR_TOKEN, firm_anchor_html())
    return html

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
    "thesis.html": "thesis.html",
    "taxlab.html": "taxlab.html",
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
        rendered = _inject_tokens(template.replace(PLACEHOLDER, data))
        out_p.write_text(rendered)
        print(f"   {tpl:16} -> docs/{out:30} ({len(rendered)} bytes, data {len(data)})")
    # Plain static assets (not templated) — copy them through. CNAME is the GitHub Pages custom-domain
    # file: managed here (source of truth in src/) and shipped in every docs/ deploy so automated
    # publishes never drop the domain.
    for asset in ("CNAME", "driftwood.css", "dw-context.js", "favicon.svg", "mask-icon.svg", "privacy.html", "terms.html", "about.html", "principles.html", "philosophy.html",
                  "insights.html", "research.html", "every-portfolio-has-two-returns.html",
                  "the-worlds-largest-investors.html", "enough-is-a-number.html", "howitworks.html",
                  "coordination.html", "case-business-sale.html",
                  "case-vacation-home.html", "case-inheritance.html",
                  "case-moving-states.html", "case-stock-options.html", "case-rmds.html",
                  "case-widowed.html", "case-charitable-giving.html", "fees.html", "manual.html",
                  "score.html", "review.html", "awor.html", "inside.html", "decision-register.html",
                  "constitution.html", "capital-allocation.html", "opportunity-register.html",
                  "record.html", "ic-memo.html", "transition-plan.html", "partners.html",
                  "coordination-review.html",
                  # the four production pages of the 2026 redesign
                  "the-practice.html", "the-record.html", "tax-atlas.html",
                  "letter.html", "private.html",
                  # Phase 2 dropdown-nav sub-pages (plain editorial stubs)
                  "household-example.html", "our-story.html",
                  "coordination-framework.html", "articles.html", "cpa-collab.html",
                  # Phase 2 nav destinations that existed in src/ but were never registered here, so
                  # every one 404'd in production while the shared nav linked them from ~43 pages.
                  # If a page is in the nav it must be in this tuple; see the nav-integrity test.
                  "leadership.html", "fiduciary.html", "six-systems.html", "first-90-days.html",
                  "commentary.html", "estate-attorneys.html", "referral.html"):
        (DOCS / asset).write_text(_inject_tokens((WEB / asset).read_text()))
        print(f"   {asset:15} -> docs/{asset} (copied)")
    # Binary assets (e.g. the founder headshot) — copy through only if present, so the About page's
    # <img> resolves once the file is dropped in. Optional: absent is fine (the page hides it).
    for asset in ("Headshot.jpg",):
        src = WEB / asset
        if src.exists():
            (DOCS / asset).write_bytes(src.read_bytes())
            print(f"   {asset:15} -> docs/{asset} (copied, binary)")
    # Engraving plates (the page headers). Committed static art, copied through on every build so a
    # docs/ deploy is always self-contained.
    img_src = WEB / "img"
    if img_src.is_dir():
        (DOCS / "img").mkdir(exist_ok=True)
        for pat in ("*.jpg", "*.png"):
            for f in sorted(img_src.glob(pat)):
                (DOCS / "img" / f.name).write_bytes(f.read_bytes())
                print(f"   img/{f.name:22} -> docs/img/{f.name} (copied, binary)")
    if bad:
        print(f"FAILED: {bad} file(s) had problems")
        return 1
    print("OK: docs regenerated from templates, data preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
