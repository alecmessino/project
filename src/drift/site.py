"""Single source of truth for the site's public base URL.

Every generated canonical / og:url / og:image / sitemap / JSON-LD URL derives from BASE_URL. The
hand-written literals in src/drift/web/*.html templates mirror it and are kept in sync by
scripts/set_domain.py (guarded by tests/test_site_domain.py) — flip the domain with:

    python scripts/set_domain.py https://www.driftwoodplanning.com

then rebuild (see OPERATIONS.md 'Moving to the custom domain'). Do NOT flip before DNS is live.
"""

BASE_URL = "https://alecmessino.github.io/project"


# ── Firm identity facts — the single insertion point for the deferred operational facts ──────────
#
# The audit's foundation items (custom domain above; contact + firm facts below) each live in ONE
# place so a production value can be inserted once and propagate. Two rules hold here:
#   1. Never publish an unverified fact. Facts that are not yet confirmed are left empty ("") and are
#      intentionally NOT rendered anywhere — the firm-anchor band (roadmap IA-4) emits a line only for
#      a fact that is set, so an empty value produces no output rather than a placeholder.
#   2. The current, already-live values (contact email, booking URL) are recorded here as-is so they
#      can be flipped site-wide in one command the day a firm inbox / scheduler exists:
#          python scripts/set_contact.py --email hello@example.com --booking https://cal.example/intro
#      (mirrors set_domain.py; string-replaces across templates, generators, and docs; reversible.)
#
# Registration / disclosure language is deliberately NOT modeled here: it is a legal decision and is
# left to counsel and the existing (test-guarded) disclosures. See FOUNDATION_FACTS.md.

# Currently live — operational, safe to flip via scripts/set_contact.py:
CONTACT_EMAIL = "hello@driftwoodplanning.com"
BOOKING_URL = "https://calendly.com/alec-messino-cwsplanning/15-minute-introductory-meeting"

# Confirmed firm facts (principal-directed, July 2026):
FIRM_LEGAL_NAME = "Driftwood Capital"
FIRM_LOCATION = "Austin, Texas"  # the firm's city/state — an intentional part of the presentation
FIRM_SINCE = "2024"              # founding year, for the "Founded" line

# Deferred — consumed by the firm-anchor band once confirmed; empty means "render nothing":
FIRM_CRD = ""        # SEC/IARD CRD number
FIRM_CUSTODIAN = ""  # independent third-party custodian (e.g. Schwab / Fidelity / Pershing)

# The month/year the model data is current to — one place; bump at each data refresh.
MODEL_ASOF = "July 2026"


def firm_facts() -> dict:
    """The firm-anchor band's data source. Only non-empty facts are returned, so a partially-known
    firm renders exactly the lines that are true today and grows as facts are confirmed."""
    candidates = {
        "legal_name": FIRM_LEGAL_NAME,
        "location": FIRM_LOCATION,
        "since": FIRM_SINCE,
        "crd": FIRM_CRD,
        "custodian": FIRM_CUSTODIAN,
        "contact_email": CONTACT_EMAIL,
        "booking_url": BOOKING_URL,
    }
    return {k: v for k, v in candidates.items() if v}


_ANCHOR_SEP = "&nbsp;&nbsp;·&nbsp;&nbsp;"


def firm_anchor_html() -> str:
    """The coordinates band (Launch Standard, item D): a restrained institution + provenance strip for
    page footers — 'DRIFTWOOD CAPITAL · AUSTIN, TEXAS · FOUNDED 2024' left, provenance right. Renders
    only confirmed facts, so an unset fact (CRD, custodian) simply does not appear — never a placeholder.
    One source; change a fact in site.py and every footer follows on the next build."""
    f = firm_facts()
    left = [FIRM_LEGAL_NAME.upper()]
    if f.get("location"):
        left.append(f["location"].upper())
    if f.get("since"):
        left.append(f"FOUNDED {f['since']}")
    if f.get("crd"):
        left.append(f"CRD {f['crd']}")
    right = [f"MODEL DATA AS OF {MODEL_ASOF.upper()}", "FORM ADV &amp; CRS AT ADVISERINFO.SEC.GOV"]
    return ('<div class="firm-anchor" role="contentinfo">'
            f'<span>{_ANCHOR_SEP.join(left)}</span>'
            f'<span>{_ANCHOR_SEP.join(right)}</span></div>')
