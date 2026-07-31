"""One page measure, site-wide.

Every page frame is the same width and every masthead lands on the same x. That sounds cosmetic; it
is not. The frame had drifted into **nine** different values declared inline on individual pages —
880 / 900 / 920 / 960 / 1000 / 1040 / 1060 / 1080 / 1180 — so clicking from the homepage to Our Story
visibly resized the site, and the wordmark jumped. A site that resizes as you move through it reads
as assembled from parts rather than published.

Two pages hung the masthead off <body> with no frame at all, putting the wordmark at x=30 while
every other page put it at x=120. Six more had **no masthead whatsoever**, including "The Seven
Systems" and "Household Example" — both linked *from* the Coordination dropdown, so following the
menu landed the visitor somewhere with no way back.

The rule now lives once, in driftwood.css. This file stops it being re-declared per page, which is
how it fragmented the first time. Geometry itself is verified in a browser (scripts under
scratchpad); what is pinned here is the *source of truth*, because that is what decays.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
CSS = WEB / "driftwood.css"

FRAME_SELECTORS = (".wrap", ".sheet")


DOCS = ROOT / "docs"


def _pages():
    """Every non-redirect source page that actually SHIPS.

    Scoped to what exists in docs/, the deploy artifact — `brand.html` is an internal brand-spec
    sheet that is deliberately not registered in sync_docs.py, so it has no masthead and needs none.
    Testing the source directory alone would flag it forever.
    """
    out = []
    for f in sorted(WEB.glob("*.html")):
        t = f.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in t:
            continue
        if not (DOCS / f.name).exists() and f.name not in ("hub.html", "index.html", "report.html"):
            continue                      # not shipped (templates are mapped under other names)
        out.append((f.name, t))
    return out


def test_the_shared_stylesheet_defines_the_frame():
    t = CSS.read_text(encoding="utf-8")
    assert re.search(r"\.wrap,\.sheet\{[^}]*max-width:\s*\d+px", t), "the shared frame is gone"
    assert re.search(r"\.wrap,\.sheet\{[^}]*padding-inline:", t), "the shared gutter is gone"
    assert t.count("min-width:1180px") >= 1 and t.count("min-width:1560px") >= 1, \
        "the responsive width ladder is gone"


def test_an_unframed_masthead_still_aligns_to_the_frame():
    """the-practice / the-record hang the nav off <body>. Without this rule the wordmark sits 90px
    left of where it sits on every other page."""
    t = CSS.read_text(encoding="utf-8")
    assert re.search(r"body\s*>\s*\.dwnav--phase2\{[^}]*max-width", t)
    assert re.search(r"body\s*>\s*\.dwnav--phase2\{[^}]*margin-inline:\s*auto", t)


@pytest.mark.parametrize("sel", FRAME_SELECTORS)
def test_no_page_redeclares_the_frame_width(sel):
    """This is how it fragmented before: each page set its own. `max-width:none` is still allowed —
    that is the print / full-bleed escape, not a page width."""
    bad = []
    for name, t in _pages():
        for m in re.finditer(re.escape(sel) + r"\{([^}]*)\}", t):
            if re.search(r"max-width:\s*\d", m.group(1)):
                bad.append(f"{name}: {sel}{{{m.group(1)[:60]}}}")
    assert not bad, f"pages re-declaring the frame width: {bad}"


@pytest.mark.parametrize("sel", FRAME_SELECTORS)
def test_no_page_overrides_the_frame_gutter(sel):
    """A `padding: A B C D` shorthand silently overrides the shared padding-inline — even when the
    horizontal value is 0. Pages declare vertical rhythm with padding-block; the frame owns the
    horizontal gutter."""
    bad = []
    for name, t in _pages():
        for m in re.finditer(re.escape(sel) + r"\{([^}]*)\}", t):
            body = m.group(1)
            if re.search(r"padding-inline:", body):
                bad.append(f"{name}: {sel} sets padding-inline")
            for pm in re.finditer(r"padding:\s*([^;}]+)", body):
                if len(pm.group(1).split()) > 1:
                    bad.append(f"{name}: {sel} sets horizontal padding via shorthand "
                               f"({pm.group(1).strip()!r}) — use padding-block")
    assert not bad, f"frame gutter overridden: {bad}"


def test_every_page_carries_the_masthead():
    """A page reachable from the menu with no way back out is a dead end. Six pages were in that
    state, two of them linked directly from the Coordination dropdown."""
    missing = [n for n, t in _pages() if 'class="dwnav dwnav--phase2"' not in t]
    assert not missing, f"pages with no masthead: {missing}"


def test_the_nav_installer_can_reach_a_page_that_never_had_one():
    """The original sweep skipped any page without an existing <nav> to replace, so a page that
    never had a masthead never got one — silently, forever."""
    src = (ROOT / "scripts" / "phase2_nav.py").read_text(encoding="utf-8")
    assert "WRAP_OPEN_RE" in src, "the installer can no longer add a missing masthead"
    assert "http-equiv" in src, "the installer must still skip redirect stubs"


def test_the_masthead_sits_on_the_frame_not_inside_the_reading_column():
    """It used to be nested in .frame > .inner on many pages — i.e. inside the narrow reading shell —
    so its width tracked the text measure instead of the page."""
    bad = []
    for name, t in _pages():
        i = t.find('<nav class="dwnav dwnav--phase2"')
        if i < 0:
            continue
        before = t[max(0, i - 220):i]
        if re.search(r'<div class="inner"[^>]*>\s*$', before):
            bad.append(name)
    assert not bad, f"masthead nested inside the reading column on: {bad}"
