"""Regression guard for the two defects an independent review found on 878934c8: Claude Design
artifact preview links (claude.ai/code/artifact/*) shipped in production templates, and placeholder
href="#" links left in the primary site navigation. This is the second time artifact links have
escaped review, so both are made structurally impossible to reintroduce silently: every shipped
*.html page is swept, not just the four pages that regressed.

Scope: every *.html under src/drift/web/ (the source templates) and docs/ (the generated,
deployed output), recursively, so a regression is caught whether it lands in a template or only
in a hand-edited docs/ file.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

# The primary site navigation carries one of exactly two class names: "dwnav" (the legacy/shared
# chrome) or "nav" (the four 2026-redesign production pages). Other <nav> landmarks exist
# (class="procbar", a per-page process breadcrumb; class="series-rail", a research-series pager)
# and are deliberately NOT the primary nav — a href="#" there is a different, unreviewed surface.
_PRIMARY_NAV_RE = re.compile(r'<nav class="(?:dwnav|nav)"[^>]*>.*?</nav>', re.S)


def _shipped_html():
    return sorted(set(WEB.glob("*.html")) | set(DOCS.glob("**/*.html")))


def test_no_claude_ai_artifact_links_on_any_shipped_page():
    offenders = []
    for p in _shipped_html():
        if "claude.ai" in p.read_text(encoding="utf-8", errors="replace"):
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, (
        "claude.ai (a private Claude Design preview link) leaked onto a shipped page — "
        f"these are not production URLs: {offenders}"
    )


def test_no_placeholder_href_in_the_primary_nav():
    offenders = []
    for p in _shipped_html():
        text = p.read_text(encoding="utf-8", errors="replace")
        m = _PRIMARY_NAV_RE.search(text)
        if not m:
            continue  # pages without a primary nav (e.g. redirect stubs) have nothing to check
        if 'href="#"' in m.group(0):
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, (
        'href="#" placeholder link left in the primary <nav> — every nav destination must resolve '
        f"to a real page: {offenders}"
    )
