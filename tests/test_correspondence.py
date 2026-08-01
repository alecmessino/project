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


def test_firm_anchor_renders_the_firm_name_and_principal():
    a = site.firm_anchor_html()
    # 2026 wordmark unification: the firm name is title-case (matches the nav wordmark everywhere
    # else), not the meta strip's tracked uppercase caps — "DRIFTWOOD WEALTH" must NOT appear.
    assert "Driftwood Wealth" in a
    assert "DRIFTWOOD WEALTH" not in a
    assert "A PRACTICE OF ALEC MESSINO" in a
    assert "FOUNDED 2024" not in a
    assert "ADVISERINFO.SEC.GOV" not in a and "MODEL DATA AS OF JULY 2026" in a


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
    assert "CHICAGO, ILLINOIS" in a.upper()
    assert site.FIRM_LOCATION and "," in site.FIRM_LOCATION, "city and state, not a bare city"
    # Scan the COORDINATES span only, not the whole band: the provenance span on the right names the
    # custodian, "Park Avenue Securities LLC", and a naive scan for "AVENUE" flags it forever.
    coords = re.search(r"<span>(.*?)</span>", a, re.S).group(1).upper()
    for token in ("SUITE", " STREET", " AVENUE", "BOULEVARD", "FLOOR", "P.O. BOX", "PO BOX"):
        assert token not in coords, f"street address token {token!r} in the firm anchor coordinates"
    assert not re.search(r"\b\d{3,5}\s+[NSEW]?\.?\s*[A-Z]", coords), "numbered street line in the anchor"
    assert "CRD" not in coords, "CRD is publish-gated and must not appear"


def test_firm_anchor_omits_unset_facts_never_a_placeholder():
    # Honesty rule: a fact produces output only when it has a real value — never a blank or
    # placeholder line. Custodian is now set to the verified PAS value; CRD stays empty
    # (publish-gated) and must still produce no output.
    facts = site.firm_facts()
    assert "custodian" in facts and facts["custodian"] == "Park Avenue Securities LLC (PAS), member FINRA/SIPC"
    assert "crd" not in facts  # CRD is publish-gated; empty must render nothing, never a placeholder
    a = site.firm_anchor_html()
    assert "PARK AVENUE SECURITIES" in a.upper()
    assert "CRD" not in a and "CUSTODIAN" not in a and "None" not in a


def test_firm_anchor_band_reaches_pages_via_the_build_token():
    # The homepage carries the rendered band (token injected at build), not the raw token.
    idx = (ROOT / "docs" / "index.html").read_text()
    assert "FIRM_ANCHOR" not in idx, "the <!--FIRM_ANCHOR--> token was not injected at build"
    assert "firm-anchor" in idx and "A PRACTICE OF ALEC MESSINO" in idx
    assert "AUSTIN, TEXAS" not in idx.upper(), "de-localized: no city/state stamp in the firm anchor"
