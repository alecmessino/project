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
CONTACT_EMAIL = "alec.messino@gmail.com"
BOOKING_URL = "https://calendly.com/alec-messino-cwsplanning/15-minute-introductory-meeting"

# Confirmed firm facts:
FIRM_LEGAL_NAME = "Driftwood Capital"

# Deferred — consumed by the firm-anchor band once confirmed; empty means "render nothing":
FIRM_CRD = ""        # SEC/IARD CRD number
FIRM_CUSTODIAN = ""  # independent third-party custodian (e.g. Schwab / Fidelity / Pershing)
FIRM_SINCE = ""      # founding year, for the "since" line


def firm_facts() -> dict:
    """The firm-anchor band's data source. Only non-empty facts are returned, so a partially-known
    firm renders exactly the lines that are true today and grows as facts are confirmed."""
    candidates = {
        "legal_name": FIRM_LEGAL_NAME,
        "crd": FIRM_CRD,
        "custodian": FIRM_CUSTODIAN,
        "since": FIRM_SINCE,
        "contact_email": CONTACT_EMAIL,
        "booking_url": BOOKING_URL,
    }
    return {k: v for k, v in candidates.items() if v}
