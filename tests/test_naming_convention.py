"""One noun per artifact type, and "Review" belongs to the engagement.

Coordination Review is the product — the thing a visitor is meant to book. Every free artifact on
the site therefore takes a different noun, so nothing competes with it in a menu, a heading, or a
button. This is not style policing: before it was enforced, `taxlab.html` was a free calculator
called the "After-Tax Review" carrying a button that read **"Request a Private After-Tax Review"**,
and it sat in the Coordination dropdown directly above "Schedule a Coordination Review". Two
different things, one noun, adjacent in the same menu.

The convention (OPERATIONS.md):

    Review      the engagement — RESERVED
    Atlas       reference / lookup          State Tax Atlas
    Lab         interactive analysis        After-Tax Lab, Concentrated Position Lab
    Diagnostic  finds what is wrong         Tax Diagnostic

"Lab" is the default suffix for new tools. One suffix scales; six competing metaphors do not.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"

# What may legitimately be called a Review. Three things only, plus their ordinary short forms:
# the engagement, the quarterly publication, and the annual client deliverable the engagement
# produces. Short forms are allowed because prose has to be able to say "the Review" once the
# subject is established — the rule is about NAMING artifacts, not about banning a word.
ALLOWED_REVIEWS = (
    "Coordination Review", "Coordination Reviews",       # the engagement
    "The Driftwood Review", "Driftwood Review",          # the quarterly publication
    "Annual Wealth Operating Review",                    # the annual deliverable …
    "Wealth Operating Review", "Operating Review",       # … and its short forms
    "Annual Review", "The Annual Review",
    "The Review", "Review",
)

RETIRED = ("After-Tax Review", "Concentrated Position Navigator")

_REVIEW_RE = re.compile(r"\b([A-Z][A-Za-z-]*(?:\s+[A-Z][A-Za-z-]*){0,3})\s+Reviews?\b")


def _pages():
    return sorted(WEB.glob("*.html"))


def test_no_page_still_uses_a_retired_tool_name():
    bad = []
    for p in _pages():
        t = p.read_text(encoding="utf-8")
        for name in RETIRED:
            if name in t:
                bad.append(f"{p.name}: {name}")
    assert not bad, f"retired tool names still shipping: {bad}"


def test_review_is_reserved_for_the_engagement_and_the_quarterly():
    """Any other "<Something> Review" is a free artifact wearing the product's noun.

    Whitespace is normalised before matching. The first rename pass was a literal string replace
    and silently missed `<a ...>After-Tax\\n        Review</a>` — a link label broken across a line
    — so a scan that respects line endings would have declared the site clean while a nav-linked
    page still shipped the old name.
    """
    offenders = set()
    for p in _pages():
        flat = re.sub(r"\s+", " ", p.read_text(encoding="utf-8"))
        for m in _REVIEW_RE.finditer(flat):
            phrase = re.sub(r"^The\s+", "", f"{m.group(1)} Review").strip()
            # a bare "the Review" in prose, once the subject is established, is not a product name
            if phrase == "Review":
                continue
            if any(phrase.endswith(a) for a in ALLOWED_REVIEWS if a != "Review"):
                continue
            offenders.add(f"{p.name}: {m.group(0).strip()!r}")
    assert not offenders, (
        "'Review' is reserved for the Coordination Review, the quarterly, and the annual "
        f"deliverable. These compete with it: {sorted(offenders)}"
    )


def test_the_shipped_tools_carry_the_agreed_nouns():
    insights = (WEB / "insights.html").read_text(encoding="utf-8")
    tools = re.search(r'id="decision-tools".*?</section>', insights, re.S)
    assert tools, "the Decision Tools shelf is missing"
    for name in ("State Tax Atlas", "Tax Diagnostic", "After-Tax Lab",
                 "Concentrated Position Lab"):
        assert name in tools.group(0), f"the shelf no longer lists {name!r}"


def test_the_taxlab_cta_asks_for_the_engagement_not_the_tool():
    """The button on a free tool must point at, and be named for, the thing being sold."""
    t = (WEB / "taxlab.html").read_text(encoding="utf-8")
    cta = re.search(r'<a class="primary" id="tl-cta"[^>]*>([^<]+)</a>', t)
    assert cta, "the taxlab CTA is missing"
    assert "Coordination Review" in cta.group(1), f"taxlab CTA reads {cta.group(1)!r}"


def test_every_nav_tool_label_follows_the_convention():
    """The masthead is where the collision was most visible — two 'Reviews' in one dropdown."""
    nav = re.search(r'<nav class="dwnav dwnav--phase2".*?</nav>',
                    (WEB / "hub.html").read_text(encoding="utf-8"), re.S)
    assert nav
    labels = re.findall(r'<a href="[^"]+"[^>]*>([^<]+)</a>', nav.group(0))
    reviews = [l for l in labels if re.search(r"\bReviews?\b", l)]
    for label in reviews:
        assert any(a in label for a in ALLOWED_REVIEWS), (
            f"nav entry {label!r} uses the reserved noun"
        )
