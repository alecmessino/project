"""Single source of truth for the site's public base URL.

Every generated canonical / og:url / og:image / sitemap / JSON-LD URL derives from BASE_URL. The
hand-written literals in src/drift/web/*.html templates mirror it and are kept in sync by
scripts/set_domain.py (guarded by tests/test_site_domain.py), flip the domain with:

    python scripts/set_domain.py https://www.driftwoodplanning.com

then rebuild (see OPERATIONS.md 'Moving to the custom domain'). Do NOT flip before DNS is live.
"""

BASE_URL = "https://driftwoodwealth.com"


# ── Firm identity facts, the single insertion point for the deferred operational facts ──────────
#
# The audit's foundation items (custom domain above; contact + firm facts below) each live in ONE
# place so a production value can be inserted once and propagate. Two rules hold here:
#   1. Never publish an unverified fact. Facts that are not yet confirmed are left empty ("") and are
#      intentionally NOT rendered anywhere, the firm-anchor band (roadmap IA-4) emits a line only for
#      a fact that is set, so an empty value produces no output rather than a placeholder.
#   2. The current, already-live values (contact email, booking URL) are recorded here as-is so they
#      can be flipped site-wide in one command the day a firm inbox / scheduler exists:
#          python scripts/set_contact.py --email hello@example.com --booking https://cal.example/intro
#      (mirrors set_domain.py; string-replaces across templates, generators, and docs; reversible.)
#
# Registration / disclosure language is deliberately NOT modeled here: it is a legal decision and is
# left to counsel and the existing (test-guarded) disclosures. See FOUNDATION_FACTS.md.

# Currently live, operational, safe to flip via scripts/set_contact.py:
# alec@driftwoodwealth.com, not hello@driftwoodplanning.com: twelve pages already hardcode the
# former, and the latter is a different domain from the one the site ships on.
CONTACT_EMAIL = "alec@driftwoodwealth.com"
BOOKING_URL = "https://calendly.com/alec-messino/introductory-call-driftwood-wealth"

# Booking attribution. A booking completes on calendly.com, so nothing on this site can observe it:
# once the visitor leaves, our analytics are blind. Calendly does read UTM parameters off the
# scheduling link and records them against the booked event, which makes the tagged link the only
# place a completed booking can be attributed back to the page that produced it.
#
# The scheme is fixed so the Calendly export stays readable:
#   utm_source    driftwoodwealth   always; the visitor came from this site
#   utm_medium    website           always; distinguishes these from any future email or print link
#   utm_campaign  <campaign>        which audience asked for the meeting, see CAMPAIGNS below
#   utm_content   <placement>       the page that produced it, e.g. coordination-review, state-ca
#
# CAMPAIGNS is deliberately a closed set of two, not a free string. Until 2026-08-09 the campaign
# was a constant (coordination_review) and every booking rolled up to one line in the Calendly
# export. That was right while the site spoke to one audience, and wrong the moment the For
# Professionals pages started asking a CPA or an estate attorney to book: a referral partner
# booking a professional introduction and a household booking a review of their own affairs are
# different meetings, prepared differently, and worth different things. utm_content could not
# separate them, because it already carries the placement and a partner can book from a state page
# too. A second campaign is the smallest change that makes the two countable apart, and keeping it
# an enumeration is what stops the export fragmenting into a dozen near-synonyms the first time
# someone needs a new link.
#
# Keep BOOKING_URL itself untagged: it is also published as structured data about the firm
# (firm_facts below), where a tracking parameter would be wrong. scripts/set_contact.py rewrites
# the bare URL by literal prefix match, so tagged links follow it correctly.
CAMPAIGN_REVIEW = "coordination_review"   # a household asking about its own affairs
CAMPAIGN_REFERRAL = "cpa_referral"        # a CPA, attorney, or advisor asking to work together
CAMPAIGNS = (CAMPAIGN_REVIEW, CAMPAIGN_REFERRAL)

_UTM = "utm_source=driftwoodwealth&utm_medium=website"


def booking_link(placement: str, campaign: str = CAMPAIGN_REVIEW) -> str:
    """The booking URL tagged for `placement`, ready to drop into an href attribute.

    `campaign` must be one of CAMPAIGNS; it defaults to the household review, so every existing
    caller keeps the link it had. Pass CAMPAIGN_REFERRAL from the For Professionals surfaces.

    Returns `&amp;` separators because every use is inside HTML; if a caller ever needs the raw
    URL (an HTTP redirect, a QR code), unescape it rather than adding a second scheme here.
    """
    if not placement or " " in placement:
        raise ValueError(f"placement must be a non-empty slug, got {placement!r}")
    if campaign not in CAMPAIGNS:
        raise ValueError(f"campaign must be one of {CAMPAIGNS}, got {campaign!r}")
    return (f"{BOOKING_URL}?{_UTM}&utm_campaign={campaign}"
            f"&utm_content={placement}").replace("&", "&amp;")

# Confirmed firm facts (principal-directed, July 2026):
FIRM_LEGAL_NAME = "Driftwood Wealth"
# 2026-08-01, reversing the de-localization above at the principal's direction. The canonical foot
# now has to make the firm reachable, and a reader deciding whether to hand over trust documents is
# entitled to know what city the practice is in. CITY AND STATE ONLY — no street address, which
# remains a legal/ADV disclosure and must not appear in marketing.
# 2026-08-03: two offices, and they are rendered as two coordinates rather than joined with "and".
# The band already separates its items with a middot, so "CHICAGO, ILLINOIS · AUSTIN, TEXAS" reads
# as a list in the band's own grammar, while "CHICAGO, ILLINOIS AND AUSTIN, TEXAS" reads as one
# long string with a conjunction buried in tracked caps.
FIRM_LOCATIONS = ("Chicago, Illinois", "Austin, Texas")
FIRM_LOCATION = FIRM_LOCATIONS[0]   # kept for callers that want a single city
FIRM_SINCE = "2024"              # founding year, for the "Founded" line
# 2026-08-03, principal-directed: the phone leaves the canonical foot. The email remains, so the
# band still makes the practice reachable; a number is a different commitment from an inbox.
FIRM_PHONE = ""

# Deferred, consumed by the firm-anchor band once confirmed; empty means "render nothing":
FIRM_CRD = ""        # SEC/IARD CRD number
# CORRECTED 2026-08-02. This held "Park Avenue Securities LLC (PAS), member FINRA/SIPC", which named
# the broker-dealer as the custodian. Those are different roles: PAS is the broker-dealer, Pershing
# custodies. Where client assets are actually held is a factual claim sitting inside a disclosure
# line, which is the worst place to be approximately right.
#
# CONFIRM THE EXACT LEGAL FORM with compliance before this is relied on — "Pershing LLC" is the
# registered entity, but the disclosure convention may be "BNY Mellon | Pershing" or similar. Empty
# renders nothing, by design, so clearing it is always the safe move.
# 2026-08-03, principal-directed: BNY Pershing.
FIRM_CUSTODIAN = "BNY Pershing"

# The month/year the model data is current to, one place; bump at each data refresh.
MODEL_ASOF = "July 2026"


def firm_facts() -> dict:
    """The firm-anchor band's data source. Only non-empty facts are returned, so a partially-known
    firm renders exactly the lines that are true today and grows as facts are confirmed."""
    candidates = {
        "legal_name": FIRM_LEGAL_NAME,
        "locations": FIRM_LOCATIONS,
        "location": FIRM_LOCATION,
        "since": FIRM_SINCE,
        "phone": FIRM_PHONE,
        "crd": FIRM_CRD,
        "custodian": FIRM_CUSTODIAN,
        "contact_email": CONTACT_EMAIL,
        "booking_url": BOOKING_URL,
    }
    return {k: v for k, v in candidates.items() if v}


_ANCHOR_SEP = "&nbsp;&nbsp;·&nbsp;&nbsp;"

# Each coordinate wraps as a unit. Without it the line breaks wherever it runs out of room, and a
# footer that reads "CUSTODY AT / BNY PERSHING" or "CHICAGO, / ILLINOIS" is a footer that has been
# typeset by the viewport rather than by anyone.


def firm_anchor_html() -> str:
    """The coordinates band: the wordmark on its own line, then a hairline meta strip of coordinates
    and provenance. Renders only confirmed facts, so an unset fact (CRD, phone) simply does not
    appear, never a placeholder. One source; change a fact in site.py and every footer follows.

    2026-08-03. The band used to run everything on one line: wordmark, descriptor, city, phone,
    email, custody, data vintage. Seven things in tracked caps at 10px, and the firm's own NAME was
    the least prominent thing in it, because it was competing with six coordinates set in the same
    size. The name now sits above the strip at a size that lets it read as a wordmark, and the
    strip below it carries the coordinates alone.

    Dropped at the principal's direction: "A PRACTICE OF ALEC MESSINO" (the descriptor repeats what
    the page's disclosure already says at length), the phone number, and "MODEL DATA AS OF ...".
    The last of those was provenance for the exhibits and had no business on an essay.
    """
    f = firm_facts()
    left = []
    for city in f.get("locations", ()):
        left.append(city.upper())
    if f.get("crd"):
        left.append(f"CRD {f['crd']}")
    if f.get("phone"):
        digits = "".join(c for c in FIRM_PHONE if c.isdigit())
        left.append(f'<a href="tel:+1{digits}">{FIRM_PHONE}</a>')
    if f.get("contact_email"):
        left.append(f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL.upper()}</a>')
    # Custody used to sit in its own right-hand span, opposite the coordinates. That split earned
    # its keep when the right side carried custody AND the data vintage against five coordinates on
    # the left. With one item on each side it is structure for its own sake, and a two-column flex
    # under a centred wordmark wraps into two rows that no longer agree about their alignment. One
    # row, in the band's own separator, follows whatever the page does.
    if f.get("custodian"):
        left.append(f"CUSTODY AT {f['custodian'].upper()}")
    return ('<div class="firm-anchor" role="contentinfo">'
            f'<span class="firm-anchor-brand">{FIRM_LEGAL_NAME}</span>'
            '<span class="firm-anchor-meta">'
            + _ANCHOR_SEP.join(f'<span class="fa-i">{item}</span>' for item in left)
            + '</span></div>')
