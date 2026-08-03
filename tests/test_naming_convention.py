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


DOCS = ROOT / "docs"


# Non-HTML files that nonetheless ship product NAMES into the page. dw-context.js renders the
# household bar and its sibling-tool links at runtime, so every label inside it reaches a visitor's
# screen exactly as if it were markup — but a *.html glob cannot see it. "After-Tax Review" lived
# there for months, in five places (the header comment, two SIBLINGS entries, the bar's own note
# copy, and a comment), shipping the retired name onto three tool pages while this file reported the
# site clean. A name scan has to follow the name, not the file extension.
_NAME_BEARING_ASSETS = ("dw-context.js",)


def _pages():
    return sorted(WEB.glob("*.html")) + [WEB / a for a in _NAME_BEARING_ASSETS]


def _shipped():
    """The BUILT pages, not the templates.

    A shipped page is template + injected `window.__STATE__` data. The templates only contain the
    placeholder, so a name baked into the engine's JSON is invisible to any check that reads src/ —
    and that is exactly where two instances of the retired name survived, including the exhibit card
    titled "After-Tax Review" on the homepage itself. Scanning what deploys is the only scan that
    covers both halves.
    """
    return sorted(DOCS.glob("*.html")) + [DOCS / a for a in _NAME_BEARING_ASSETS]


def _flat(text: str) -> str:
    """Collapse whitespace AND HTML space entities before matching.

    Both rename passes leaked through this gap. The first was a literal string replace and missed a
    link label broken across a line. The second normalised `\\s+` — which does not match `&nbsp;` —
    and so missed "After-Tax&nbsp;Review" sitting in the copy directly above the Tax Diagnostic's
    primary call to action, on a page in the main funnel.
    """
    return re.sub(r"(?:\s|&nbsp;|&#160;)+", " ", text)


def test_no_page_still_uses_a_retired_tool_name():
    bad = []
    for p in _pages() + _shipped():
        t = _flat(p.read_text(encoding="utf-8"))
        for name in RETIRED:
            if name in t:
                bad.append(f"{p.name}: {name}")
    assert not bad, f"retired tool names still shipping: {bad}"


def test_nothing_asks_a_visitor_to_request_a_free_tool():
    """A Lab, an Atlas or a Diagnostic is opened, not requested. Only the engagement is requested.

    The rename produced exactly this: "Request a Private After-Tax Lab" — grammatical nonsense, and
    a button competing with the Coordination Review while pointing at a free calculator."""
    bad = []
    for p in _pages():
        for m in re.finditer(r"Request[^<]{0,40}\b(Lab|Atlas|Diagnostic|Navigator)\b",
                             _flat(p.read_text(encoding="utf-8"))):
            bad.append(f"{p.name}: {m.group(0).strip()!r}")
    assert not bad, f"a free tool is being 'requested' like an engagement: {bad}"


def test_review_is_reserved_for_the_engagement_and_the_quarterly():
    """Any other "<Something> Review" is a free artifact wearing the product's noun.

    Whitespace is normalised before matching. The first rename pass was a literal string replace
    and silently missed `<a ...>After-Tax\\n        Review</a>` — a link label broken across a line
    — so a scan that respects line endings would have declared the site clean while a nav-linked
    page still shipped the old name.
    """
    offenders = set()
    for p in _pages():
        flat = _flat(p.read_text(encoding="utf-8"))
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


# ── the systems taxonomy ──────────────────────────────────────────────────────────────────────
#
# The count is part of the architecture, not a turn of phrase. SEVEN systems radiate from the
# coordination engine: Investments, Taxes, Cash Flow, Family / Purpose, Estate, Protection, and
# Business Ownership. The site said "seven systems" in fourteen places and the filename
# six-systems.html survived from an earlier taxonomy, which is exactly the sort of split that gets
# a stale count copied into new copy by someone reading the file tree instead of the pages.
#
# six-systems.html itself is fine and stays: it has been a redirect stub onto coordination.html for
# some time, so no visitor ever reads the number in its name. What must never ship is a VISIBLE
# "six systems", which is why these tests read rendered prose rather than raw markup.

_SEVEN_SYSTEMS = ("Investments", "Taxes", "Cash Flow", "Family / Purpose", "Estate",
                  "Protection", "Business Ownership")


def _visible(text: str) -> str:
    """What a reader actually sees: markup, comments, script and style removed.

    Authoring comments are deliberately out of scope. hub.html carries one describing a decision
    cascade ("not merely THAT six systems moved, but in what order one ran into the next"), which
    may well be counting the hops in one animated trace rather than the taxonomy. Rewriting a
    comment whose intent is ambiguous is not what this guard is for; shipping the wrong number to a
    prospect is.
    """
    for pattern in (r"<!--[\s\S]*?-->", r"<script[\s\S]*?</script>", r"<style[\s\S]*?</style>"):
        text = re.sub(pattern, " ", text)
    return _flat(re.sub(r"<[^>]+>", " ", text))


def test_no_shipped_page_tells_a_visitor_there_are_six_systems():
    """The deploy-blocking half. A stale count in visible copy is an architectural mismatch the
    reader can see, and it undercuts every other number on the site."""
    offenders = []
    for page in _shipped():
        if page.suffix != ".html":
            continue
        prose = _visible(page.read_text(encoding="utf-8", errors="replace"))
        if re.search(r"\bsix systems\b", prose, re.I):
            offenders.append(page.name)
    assert not offenders, (
        f"pages telling a visitor there are six systems: {offenders}. The taxonomy is seven: "
        f"{', '.join(_SEVEN_SYSTEMS)}.")


def test_the_canonical_page_still_names_all_seven():
    """The other half, and the one that actually decays. Banning the wrong count is worthless if
    the right one quietly loses a member: 'seven systems' would still read fine over six names."""
    canon = (DOCS / "coordination.html").read_text(encoding="utf-8")
    missing = [s for s in _SEVEN_SYSTEMS if s not in canon]
    assert not missing, f"coordination.html no longer names: {missing}"
    assert "seven systems" in _visible(canon), \
        "coordination.html no longer states the count it enumerates"


def test_the_six_systems_url_is_a_redirect_and_not_a_page():
    """It may keep its filename only for as long as nobody reads it. The moment it becomes a real
    page again, its name is a claim, and this fails."""
    stub = WEB / "six-systems.html"
    assert 'http-equiv="refresh"' in stub.read_text(encoding="utf-8"), (
        "six-systems.html is a live page again; its filename now asserts a taxonomy the firm "
        "does not use. Rename it, or point it at coordination.html as before.")
