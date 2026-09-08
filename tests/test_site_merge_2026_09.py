"""The 2026-09 production merge of the approved site design, pinned.

Homepage v2 (lock 1a) plus six inner pages were ported from the approved design files into the
production templates. These are the lock-ins from the handoff that would decay silently: one
prospect CTA label site-wide, a deliberately distinct professional CTA, the office line verbatim,
no teal on the Fees page's promotional accents, and the record strip's nomenclature.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

PROSPECT_CTA = "Request a Coordination Review"
PROFESSIONAL_CTA = "Professional introduction, 15 minutes"
OFFICE_LINE = "Chicago, Illinois &middot; Austin, Texas"


def _body(name: str) -> str:
    t = (WEB / name).read_text(encoding="utf-8")
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    return re.sub(r'<nav class="dwnav.*?</nav>', "", t, flags=re.S)


def test_the_hero_qualifier_is_the_approved_sentence():
    assert ("Fifteen minutes. Nothing to prepare. No products. Fee in writing before work."
            in (WEB / "hub.html").read_text(encoding="utf-8"))


def test_the_prospect_cta_label_is_the_same_everywhere():
    """Hero, global nav, the Review page's primary action, and the closing actions."""
    hub = (WEB / "hub.html").read_text(encoding="utf-8")
    assert f'<a class="primary" href="coordination-review.html">{PROSPECT_CTA} &rarr;</a>' in hub
    assert f'<a class="dwnav-cta" href="coordination-review.html">{PROSPECT_CTA} ' in hub
    review = _body("coordination-review.html")
    books = re.findall(r'<a class="book"[^>]*>([^<]+)</a>', review)
    assert books and all(b.startswith(PROSPECT_CTA) for b in books), books
    assert "Schedule the 15-minute introduction" not in review
    assert f"{PROSPECT_CTA} &rarr;" in _body("fees.html")


def test_the_professional_cta_stays_distinct():
    body = _body("partners.html")
    books = re.findall(r'<a class="book"[^>]*>([^<]+)</a>', body)
    assert books and all(b.startswith(PROFESSIONAL_CTA) for b in books), books
    assert all("utm_campaign=cpa_referral" in h for h in re.findall(r'<a class="book" href="([^"]+)"', body))
    assert PROSPECT_CTA not in body, "the partners page body must not carry the prospect CTA"
    assert "No client data." in body


def test_the_office_line_is_verbatim():
    assert OFFICE_LINE in (WEB / "leadership.html").read_text(encoding="utf-8")
    assert "<dd>Chicago, Illinois</dd>" not in (WEB / "leadership.html").read_text(encoding="utf-8")


def test_fees_promotional_accents_carry_no_teal():
    css_and_body = re.sub(r":root\{[^}]*\}", "", (WEB / "fees.html").read_text(encoding="utf-8"))
    for teal in ("#15806a", "#15463a", "var(--teal", "var(--accent)"):
        assert teal not in css_and_body, f"teal accent {teal} on the Fees page"


def test_the_record_strip_ships_on_the_four_pages_with_the_approved_hierarchy():
    order = ["The Coordination Report", "The Opportunity Register", "The Wealth Operating Manual",
             "Your 90-Day Plan", "The Decision Register"]
    for page in ("index.html", "coordination-review.html", "principles.html"):
        t = (DOCS / page).read_text(encoding="utf-8")
        if page == "coordination-review.html":
            names = re.findall(r'<span class="dt">([^<]+)</span>', t)
        else:
            names = re.findall(r'<span class="rs-n">\d\d</span>([^<]+)</a>', t)
        assert names == order, f"{page}: {names}"
    manual = (DOCS / "manual.html").read_text(encoding="utf-8")
    assert '<div class="record-mast">' in manual and 'aria-current="page">03 Wealth Operating Manual' in manual
    assert 'onclick="window.print()"' in manual and "Set in Satoshi" not in manual
    for retired in ("Coordination Index", "Coordination Register"):
        for page in ("index.html", "coordination-review.html", "principles.html", "manual.html", "fees.html",
                     "partners.html", "leadership.html"):
            assert retired not in (DOCS / page).read_text(encoding="utf-8"), f"{retired!r} on {page}"


def test_no_design_runtime_leaked_into_production():
    for page in WEB.glob("*.html"):
        t = page.read_text(encoding="utf-8")
        for residue in ("dc-import", "<x-dc", "support.js", "localhost", ".dc.html\""):
            assert residue not in t, f"{page.name} carries design residue {residue!r}"
