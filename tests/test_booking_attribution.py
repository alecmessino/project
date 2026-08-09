"""Every booking link must carry its placement, because nothing else can.

A booking completes on calendly.com. The moment a visitor leaves this site, Plausible is blind:
there is no on-site event that can observe a completed booking, and the one that claimed to for
months (`booking_scheduled`, per OPERATIONS.md) never existed. The UTM parameters on the
scheduling link are therefore the *only* mechanism that attributes a booked meeting back to the
page that produced it.

That makes an untagged link a silent failure. It works perfectly, the visitor books, and the
booking simply arrives in Calendly with no idea where it came from. Nothing turns red. This file
is the thing that turns red.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift.site import BOOKING_URL, CAMPAIGNS, booking_link  # noqa: E402

WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

# Source and medium never vary: the visitor came from this website, always.
FIXED = ("utm_source=driftwoodwealth", "utm_medium=website")
# The campaign varies over a CLOSED set (household review / professional referral) so the two
# audiences stay countable apart without the export fragmenting into near-synonyms.
CAMPAIGN_PARAMS = tuple(f"utm_campaign={c}" for c in CAMPAIGNS)


def _booking_hrefs(text: str):
    """Every href pointing at the booking URL, tagged or not."""
    return re.findall(r'href="(' + re.escape(BOOKING_URL) + r'[^"]*)"', text)


def test_the_helper_produces_the_agreed_scheme():
    link = booking_link("coordination-review")
    assert link.startswith(BOOKING_URL + "?")
    for part in FIXED:
        assert part in link, f"{part} missing from {link}"
    assert "utm_campaign=coordination_review" in link, "the household review is still the default"
    assert "utm_content=coordination-review" in link
    # HTML-attribute ready: a raw & in an href is invalid markup and some parsers will eat it.
    assert "&amp;" in link and re.search(r"&(?!amp;)", link) is None


def test_the_helper_tags_a_professional_introduction_to_its_own_campaign():
    """A partner introduction and a household review are different meetings; the export has to
    be able to tell them apart, and utm_content can't do it (a partner can book from any page)."""
    link = booking_link("partners", campaign="cpa_referral")
    assert "utm_campaign=cpa_referral" in link and "utm_campaign=coordination_review" not in link
    for part in FIXED:
        assert part in link, f"{part} missing from {link}"
    assert "utm_content=partners" in link


def test_the_helper_refuses_a_placement_that_would_corrupt_the_url():
    for bad in ("", "two words"):
        try:
            booking_link(bad)
        except ValueError:
            continue
        raise AssertionError(f"booking_link({bad!r}) should have been rejected")


def test_the_helper_refuses_a_campaign_outside_the_agreed_set():
    """An open string here is how a two-line export becomes twelve lines of near-synonyms
    (cpa-referral / cpa_referrals / partner_referral) that no one can total."""
    for bad in ("", "cpa-referral", "partners", "coordination review"):
        try:
            booking_link("partners", campaign=bad)
        except ValueError:
            continue
        raise AssertionError(f"booking_link(campaign={bad!r}) should have been rejected")


def test_every_booking_link_in_the_built_site_is_attributed():
    """The one that matters. An untagged link loses the attribution and says nothing about it."""
    untagged = []
    for page in sorted(DOCS.rglob("*.html")):
        for href in _booking_hrefs(page.read_text(encoding="utf-8")):
            if "utm_content=" not in href:
                untagged.append(f"{page.relative_to(DOCS)}: {href[:80]}")
    assert not untagged, (
        "booking links with no placement — these bookings will arrive in Calendly unattributed:\n  "
        + "\n  ".join(untagged[:12])
    )


def test_every_booking_link_carries_the_whole_scheme():
    """A partial tag is worse than none: it looks instrumented and groups wrongly in the export."""
    broken = []
    for page in sorted(DOCS.rglob("*.html")):
        for href in _booking_hrefs(page.read_text(encoding="utf-8")):
            missing = [p for p in FIXED if p not in href]
            if not any(c in href for c in CAMPAIGN_PARAMS):
                missing.append("utm_campaign (one of %s)" % (CAMPAIGNS,))
            if missing:
                broken.append(f"{page.relative_to(DOCS)}: missing {missing}")
    assert not broken, "booking links missing fixed UTM fields:\n  " + "\n  ".join(broken[:12])


# The three For Professionals pages. Their whole job is to get a CPA, an estate attorney, or an
# advisor onto a call; a booking from one of them that rolls up under the household campaign is
# invisible as partner-channel evidence, which is the only evidence these pages produce.
_PROFESSIONAL_PAGES = ("partners.html", "estate-attorneys.html", "referral.html")


def test_the_professional_pages_book_under_the_referral_campaign():
    for name in _PROFESSIONAL_PAGES:
        for source in (WEB / name, DOCS / name):
            hrefs = _booking_hrefs(source.read_text(encoding="utf-8"))
            assert hrefs, f"{source.name}: no booking link at all — a partner has no way to book"
            assert all("utm_campaign=cpa_referral" in h for h in hrefs), (
                f"{source}: a booking link here rolls up under the household campaign, so the "
                "partner channel cannot be counted"
            )


def test_the_source_templates_are_tagged_too():
    """docs/ is generated; a template fixed only downstream regresses on the next build."""
    untagged = []
    for page in sorted(WEB.glob("*.html")):
        for href in _booking_hrefs(page.read_text(encoding="utf-8")):
            if "utm_content=" not in href:
                untagged.append(f"{page.name}: {href[:80]}")
    assert not untagged, "untagged booking link in a source template:\n  " + "\n  ".join(untagged)


def test_the_bare_booking_url_stays_untagged_in_structured_data():
    """BOOKING_URL is published as a fact about the firm, where a tracking parameter is wrong."""
    assert "utm_" not in BOOKING_URL
