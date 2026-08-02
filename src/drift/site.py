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
BOOKING_URL = "https://calendly.com/alec-messino/15-minute-introductory-meeting"

# Confirmed firm facts (principal-directed, July 2026):
FIRM_LEGAL_NAME = "Driftwood Wealth"
# 2026-08-01, reversing the de-localization above at the principal's direction. The canonical foot
# now has to make the firm reachable, and a reader deciding whether to hand over trust documents is
# entitled to know what city the practice is in. CITY AND STATE ONLY — no street address, which
# remains a legal/ADV disclosure and must not appear in marketing.
FIRM_LOCATION = "Chicago, Illinois"
FIRM_SINCE = "2024"              # founding year, for the "Founded" line
FIRM_PHONE = "(708) 548-7600"    # rendered in the canonical foot; tel: href is derived from it

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
FIRM_CUSTODIAN = "Pershing LLC"

# The month/year the model data is current to, one place; bump at each data refresh.
MODEL_ASOF = "July 2026"


def firm_facts() -> dict:
    """The firm-anchor band's data source. Only non-empty facts are returned, so a partially-known
    firm renders exactly the lines that are true today and grows as facts are confirmed."""
    candidates = {
        "legal_name": FIRM_LEGAL_NAME,
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


def firm_anchor_html() -> str:
    """The coordinates band (Launch Standard, item D): a restrained institution + provenance strip for
    page footers, 'Driftwood Wealth · A PRACTICE OF ALEC MESSINO' left, provenance right. Renders
    only confirmed facts, so an unset fact (CRD, custodian) simply does not appear, never a placeholder.
    One source; change a fact in site.py and every footer follows on the next build.

    The band is styled as a small tracked-caps meta strip (.firm-anchor, driftwood.css) — but the firm
    NAME is the wordmark, and the wordmark is title-case everywhere else on the site (nav brand lockup,
    hub.html hero). .firm-anchor-brand overrides the parent's text-transform so the name renders in its
    one true case here too, while the surrounding descriptor/provenance text keeps the meta-strip
    treatment. 'One logo, one case, one type, everywhere' (2026 wordmark unification)."""
    f = firm_facts()
    left = [f'<span class="firm-anchor-brand">{FIRM_LEGAL_NAME}</span>']
    # Not registered: the practice is named for its principal, not a "Founded" year.
    left.append("A PRACTICE OF ALEC MESSINO")
    if f.get("location"):
        left.append(f["location"].upper())
    if f.get("crd"):
        left.append(f"CRD {f['crd']}")
    # Reachability moved into the anchor, 2026-08-01. The band used to be pure provenance, which meant
    # the pages a professional is most likely to land on carried no way to make contact at all.
    # Rendered as real tel:/mailto: links so a phone can act on them.
    if f.get("phone"):
        digits = "".join(c for c in FIRM_PHONE if c.isdigit())
        left.append(f'<a href="tel:+1{digits}">{FIRM_PHONE}</a>')
    if f.get("contact_email"):
        left.append(f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL.upper()}</a>')
    # custody is provenance, not a coordinate: it belongs on the right with the data vintage.
    right = []
    if f.get("custodian"):
        right.append(f"custody at {f['custodian']}")
    right.append(f"MODEL DATA AS OF {MODEL_ASOF.upper()}")
    return ('<div class="firm-anchor" role="contentinfo">'
            f'<span>{_ANCHOR_SEP.join(left)}</span>'
            f'<span>{_ANCHOR_SEP.join(right)}</span></div>')
