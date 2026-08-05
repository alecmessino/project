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

from drift.site import BOOKING_URL, booking_link  # noqa: E402

WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

# The scheme is fixed so the Calendly export stays readable. Only utm_content varies.
FIXED = ("utm_source=driftwoodwealth", "utm_medium=website", "utm_campaign=coordination_review")


def _booking_hrefs(text: str):
    """Every href pointing at the booking URL, tagged or not."""
    return re.findall(r'href="(' + re.escape(BOOKING_URL) + r'[^"]*)"', text)


def test_the_helper_produces_the_agreed_scheme():
    link = booking_link("coordination-review")
    assert link.startswith(BOOKING_URL + "?")
    for part in FIXED:
        assert part in link, f"{part} missing from {link}"
    assert "utm_content=coordination-review" in link
    # HTML-attribute ready: a raw & in an href is invalid markup and some parsers will eat it.
    assert "&amp;" in link and re.search(r"&(?!amp;)", link) is None


def test_the_helper_refuses_a_placement_that_would_corrupt_the_url():
    for bad in ("", "two words"):
        try:
            booking_link(bad)
        except ValueError:
            continue
        raise AssertionError(f"booking_link({bad!r}) should have been rejected")


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
            if missing:
                broken.append(f"{page.relative_to(DOCS)}: missing {missing}")
    assert not broken, "booking links missing fixed UTM fields:\n  " + "\n  ".join(broken[:12])


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
