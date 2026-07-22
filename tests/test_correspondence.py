"""Guards for centralized correspondence + the firm-anchor coordinates band (Launch Standard, item D).

The firm's contact endpoint and coordinates live in ONE place (drift.site) and propagate to every page;
these tests fail loudly if a personal Gmail ever returns, if the contact address stops being the firm
domain, or if the firm anchor stops rendering the firm name + principal line — while an unset fact
(CRD, custodian) must still render nothing rather than a placeholder. The anchor is intentionally
de-localized: it must NOT stamp a city/state (Driftwood reads as institutional, not regional).
"""

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
    assert site.CONTACT_EMAIL.endswith("@driftwoodplanning.com"), site.CONTACT_EMAIL
    assert "gmail" not in site.CONTACT_EMAIL
    # the address rendered on pages is the one in site.py (the flip tool keeps literals in sync)
    hub = (ROOT / "src" / "drift" / "web" / "hub.html").read_text()
    assert "gmail" not in hub


def test_firm_anchor_renders_the_firm_name_and_principal():
    a = site.firm_anchor_html()
    assert "DRIFTWOOD WEALTH" in a
    assert "A PRACTICE OF ALEC MESSINO" in a
    assert "FOUNDED 2024" not in a
    assert "ADVISERINFO.SEC.GOV" not in a and "MODEL DATA AS OF JULY 2026" in a


def test_firm_anchor_is_de_localized_no_city_or_state():
    # Driftwood reads as institutional, not regional: the anchor must not stamp a city/state.
    facts = site.firm_facts()
    assert "location" not in facts
    a = site.firm_anchor_html()
    assert "AUSTIN" not in a.upper() and "TEXAS" not in a.upper()


def test_firm_anchor_omits_unset_facts_never_a_placeholder():
    # CRD and custodian are not yet confirmed — they must produce no output (the honesty rule),
    # not a blank or placeholder line.
    facts = site.firm_facts()
    assert "crd" not in facts and "custodian" not in facts
    a = site.firm_anchor_html()
    assert "CRD" not in a and "CUSTODIAN" not in a and "None" not in a


def test_firm_anchor_band_reaches_pages_via_the_build_token():
    # The homepage carries the rendered band (token injected at build), not the raw token.
    idx = (ROOT / "docs" / "index.html").read_text()
    assert "FIRM_ANCHOR" not in idx, "the <!--FIRM_ANCHOR--> token was not injected at build"
    assert "firm-anchor" in idx and "A PRACTICE OF ALEC MESSINO" in idx
    assert "AUSTIN, TEXAS" not in idx.upper(), "de-localized: no city/state stamp in the firm anchor"
