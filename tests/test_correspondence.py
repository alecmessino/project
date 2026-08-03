"""Guards for centralized correspondence + the firm-anchor coordinates band (Launch Standard, item D).

The firm's contact endpoint and coordinates live in ONE place (drift.site) and propagate to every page;
these tests fail loudly if a personal Gmail ever returns, if the contact address stops being the firm
domain, or if the firm anchor stops rendering the firm name + principal line — while an unset fact
(CRD, custodian) must still render nothing rather than a placeholder. The anchor carries the city
and state (2026-08-01, reversing the earlier de-localization) but must NEVER carry a street address,
which is a legal/ADV disclosure rather than marketing copy.
"""

import re
from pathlib import Path

from drift import site

ROOT = Path(__file__).resolve().parents[1]
SHIPPED = (
    list((ROOT / "src" / "drift" / "web").glob("*.html"))
    + list((ROOT / "docs").glob("*.html"))
    + [ROOT / "src" / "drift" / "statepage.py"]
)


def test_no_personal_gmail_on_any_shipped_surface():
    offenders = [p.name for p in SHIPPED if "gmail.com" in p.read_text()]
    assert not offenders, f"personal Gmail leaked back onto: {offenders} — flip via scripts/set_contact.py"


def test_contact_endpoint_is_the_firm_domain_and_single_sourced():
    """The contact address must be on the domain the site actually ships on.

    This asserted @driftwoodplanning.com until 2026-08-01, which was a *different* domain from
    driftwoodwealth.com, where every page is canonicalised and where twelve pages already hardcoded
    alec@driftwoodwealth.com. The single-sourcing guard was passing while the one address it guarded
    disagreed with every address on the site.
    """
    assert site.CONTACT_EMAIL.endswith("@driftwoodwealth.com"), site.CONTACT_EMAIL
    assert site.BASE_URL.endswith("driftwoodwealth.com"), site.BASE_URL
    assert "gmail" not in site.CONTACT_EMAIL
    # the address rendered on pages is the one in site.py (the flip tool keeps literals in sync)
    hub = (ROOT / "src" / "drift" / "web" / "hub.html").read_text()
    assert "gmail" not in hub


def test_firm_anchor_leads_with_the_wordmark_and_nothing_else():
    """The name is the first thing in the band and it sits on its own line.

    2026-08-03. The band used to run the wordmark inline with six coordinates, all at the same
    10px tracked caps, which left the firm's own name as the least prominent thing in its own
    footer. It now leads, in its own case, on its own row.
    """
    a = site.firm_anchor_html()
    # 2026 wordmark unification: title-case, matching the nav lockup everywhere else on the site.
    assert '<span class="firm-anchor-brand">Driftwood Wealth</span>' in a
    assert "DRIFTWOOD WEALTH" not in a
    assert a.index("Driftwood Wealth") < a.index("firm-anchor-meta"), \
        "the wordmark no longer leads the band"
    assert "FOUNDED 2024" not in a and "ADVISERINFO.SEC.GOV" not in a


def test_the_anchor_carries_no_descriptor_no_phone_and_no_data_vintage():
    """Three things left the band on 2026-08-03, at the principal's direction, and each for its
    own reason. The descriptor repeated what the page's disclosure already says at length. The
    phone is a different commitment from an inbox, and the email stays. The data vintage was
    provenance for the exhibits and had no business on an essay."""
    a = site.firm_anchor_html()
    assert "A PRACTICE OF" not in a.upper(), "the descriptor is back in the anchor"
    assert "MODEL DATA AS OF" not in a.upper(), "the data vintage is back in the anchor"
    assert "tel:" not in a and not site.FIRM_PHONE, "a phone number is back in the anchor"
    # What must remain: the band still has to make the practice reachable.
    assert "mailto:" in a and site.CONTACT_EMAIL.upper() in a.upper()


def test_firm_anchor_carries_a_city_but_never_a_street_address():
    """City and state, yes. A street address, never.

    This test asserted the opposite until 2026-08-01 ("Driftwood reads as institutional, not
    regional"), and the principal reversed it: the canonical foot now has to make the firm
    reachable, and a reader deciding whether to hand over trust documents is entitled to know what
    city the practice is in. The half of the old rule that still stands is the important half — a
    street address is a legal/ADV disclosure and must not appear in marketing, so that is what is
    guarded here now, along with the CRD number, which remains publish-gated.
    """
    a = site.firm_anchor_html()
    assert "CHICAGO, ILLINOIS" in a.upper() and "AUSTIN, TEXAS" in a.upper()
    assert all("," in c for c in site.FIRM_LOCATIONS), "city and state, not a bare city"
    # Two offices are rendered as two coordinates in the band's own grammar, never joined with a
    # conjunction: "CHICAGO, ILLINOIS AND AUSTIN, TEXAS" is one long string in tracked caps.
    assert " AND " not in a.upper(), "the offices are joined with a conjunction"
    # Scan the COORDINATES strip only, not the whole band. A naive scan of the band would have to
    # cope with whatever the custodian is called, and "Park Avenue Securities" would flag " AVENUE"
    # forever. Anchored on the class rather than on a bare <span>, because every span in the band
    # carries one now.
    m = re.search(r'<span class="firm-anchor-meta">(.*?)</span>\s*</div>', a, re.S)
    assert m, "the anchor no longer has a coordinates strip"
    coords = m.group(1).upper()
    for token in ("SUITE", " STREET", " AVENUE", "BOULEVARD", "FLOOR", "P.O. BOX", "PO BOX"):
        assert token not in coords, f"street address token {token!r} in the firm anchor coordinates"
    assert not re.search(r"\b\d{3,5}\s+[NSEW]?\.?\s*[A-Z]", coords), "numbered street line in the anchor"
    assert "CRD" not in coords, "CRD is publish-gated and must not appear"


def test_firm_anchor_omits_unset_facts_never_a_placeholder():
    """A fact produces output only when it has a real value, never a blank or a placeholder.

    This asserted the custodian was "Park Avenue Securities LLC (PAS), member FINRA/SIPC" until
    2026-08-02, which pinned a factual misstatement: PAS is the broker-dealer, and naming it as the
    custodian says something untrue about where client assets are held, inside a disclosure line.
    The value is withheld until confirmed. The test now guards the PRINCIPLE the original was
    reaching for — unset renders nothing — rather than one particular unverified value.
    """
    facts = site.firm_facts()
    for gated in ("crd", "custodian"):
        if not getattr(site, f"FIRM_{gated.upper().replace('CUSTODIAN', 'CUSTODIAN')}", ""):
            assert gated not in facts, f"{gated} is empty and must not reach the anchor"
    a = site.firm_anchor_html()
    assert "None" not in a and "CRD" not in a
    # No orphaned label: "custody" only ever appears attached to a value.
    assert "custody " not in a or site.FIRM_CUSTODIAN
    # Whatever is withheld, the coordinates the reader needs are still there.
    assert "Driftwood Wealth" in a and "CHICAGO, ILLINOIS" in a.upper()


def test_firm_anchor_band_reaches_pages_via_the_build_token():
    # The homepage carries the rendered band (token injected at build), not the raw token.
    idx = (ROOT / "docs" / "index.html").read_text()
    assert "FIRM_ANCHOR" not in idx, "the <!--FIRM_ANCHOR--> token was not injected at build"
    assert "firm-anchor" in idx and "firm-anchor-brand" in idx
    for coordinate in ("CHICAGO, ILLINOIS", "AUSTIN, TEXAS", "CUSTODY AT BNY PERSHING"):
        assert coordinate in idx.upper(), f"the anchor on the front door lost {coordinate!r}"
