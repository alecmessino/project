"""The sitemap must describe the site that actually exists.

`_CORE_SITEMAP` is a hand-maintained list, so it rots in two directions and both are silent:

  - it keeps listing pages that were deleted or turned into redirect stubs, which submits 404s and
    noindex URLs to Search Console; and
  - it fails to list pages that were added, so the site's most important new surfaces are simply
    never announced.

Both had happened by 2026-07-31: four stale entries (`library.html`, `familyoffice.html` — deleted
in 3caa0d6c and 404 on the live site — plus `howitworks.html` and `record.html`, now noindex
redirect stubs) and several live pages missing entirely, including the Insights landing page, which
had just been promoted from a noindex stub to a primary navigation destination.
"""
import re
from pathlib import Path

from drift.statepage import _CORE_SITEMAP

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
WEB = ROOT / "src" / "drift" / "web"

_CORE_PAGES = [loc for loc, _, _ in _CORE_SITEMAP if loc.endswith(".html")]


def test_every_sitemap_entry_is_a_page_that_ships():
    """A sitemap entry for a page that does not exist is a 404 submitted on purpose."""
    missing = sorted(p for p in _CORE_PAGES if not (DOCS / p).exists())
    assert not missing, f"sitemap lists pages that do not ship: {missing}"


def test_no_sitemap_entry_is_a_redirect_stub_or_noindex():
    """Announcing a URL that redirects elsewhere, or that asks not to be indexed, wastes crawl
    budget and splits the ranking signal between the stub and its target."""
    bad = []
    for p in _CORE_PAGES:
        t = (DOCS / p).read_text(encoding="utf-8")
        robots = re.search(r'<meta[^>]+name="robots"[^>]*>', t)
        if 'http-equiv="refresh"' in t or (robots and "noindex" in robots.group(0)):
            bad.append(p)
    assert not bad, f"sitemap lists redirect stubs / noindex pages: {bad}"


def test_every_primary_navigation_destination_is_in_the_sitemap():
    """If a page is important enough to sit in the masthead, it is important enough to announce.
    This is the rule that catches the next Insights-shaped omission automatically."""
    nav = re.search(r'<nav class="dwnav dwnav--phase2".*?</nav>',
                    (WEB / "index.html").read_text(encoding="utf-8")
                    if (WEB / "index.html").exists()
                    else (WEB / "hub.html").read_text(encoding="utf-8"), re.S)
    assert nav, "could not read the primary navigation"
    targets = {h.partition("#")[0] for h in re.findall(r'href="([^"]+\.html)[^"]*"', nav.group(0))}
    targets = {t for t in targets if "://" not in t}
    # A noindex destination is legitimately absent — private.html (Client Access) is gated, and
    # announcing it would contradict its own robots directive.
    missing = sorted(t for t in targets if t not in _CORE_PAGES and not _noindex(t))
    assert not missing, f"in the masthead but not in the sitemap: {missing}"


def _noindex(page: str) -> bool:
    p = DOCS / page
    if not p.exists():
        return False
    m = re.search(r'<meta[^>]+name="robots"[^>]*>', p.read_text(encoding="utf-8"))
    return bool(m) and "noindex" in m.group(0)


def test_the_sitemap_has_no_duplicates():
    assert len(_CORE_PAGES) == len(set(_CORE_PAGES)), "duplicate sitemap entries"


def test_the_flagship_pages_are_announced():
    """Named explicitly so a future edit cannot quietly drop them."""
    for page in ("index.html", "insights.html", "driftwood-review.html", "research.html",
                 "coordination-review.html"):
        assert page in _CORE_PAGES, f"{page} must be in the sitemap"
