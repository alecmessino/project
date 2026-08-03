"""Guards for the SEC-grade hypothetical-performance framing.

The performance exhibits (the Model Portfolio ledger and the long-history tearsheet)
present *backtested* results. The Marketing Rule requires those be clearly labeled as
hypothetical, with prominent disclosure near the numbers. These tests fail loudly if the
disclosure language or the Model-Portfolio framing is ever dropped, or if the old
"live track record" framing creeps back in.
"""

import re

from drift.exhibit import (
    LEDGER_TEMPLATE,
    TEARSHEET_TEMPLATE,
    HUB_TEMPLATE,
    THESIS_TEMPLATE,
    TAXLAB_TEMPLATE,
    LEAKAGE_TEMPLATE,
    TEMPLATE,  # index.html / dashboard
)

# The three pillars the Marketing Rule wants stated for hypothetical performance.
_REQUIRED_PHRASES = [
    "retroactive application",          # these are a model applied after the fact
    "no client capital was invested",   # not actual client capital
    "does not guarantee future results",  # past performance caveat
]


def _read(p):
    return p.read_text()


def test_ledger_hypothetical_disclosure_present_with_point_of_performance_marker():
    # Maximal-subtle posture (RIA-principal approved, see docs/Compliance_Disclosure_Changes.md):
    # the FULL hypothetical-performance disclosure renders as small print at the FOOT of the page,
    # while the point-of-performance label is kept by the "HYPOTHETICAL" header pill AND the summary
    # card's "Hypothetical backtest" line. All required Marketing-Rule language stays present.
    t = _read(LEDGER_TEMPLATE)
    assert 'class="disclaimer"' in t                      # the disclosure block still exists
    for phrase in _REQUIRED_PHRASES:
        assert phrase in t, f"ledger disclosure missing: {phrase!r}"
    assert "hyp-pill" in t and "HYPOTHETICAL" in t        # header marker at the point of performance
    assert "Hypothetical backtest" in t                   # summary-card inline marker
    # The full disclosure is rendered at the foot — AFTER the metrics, not above them.
    assert t.index("${disclaimerHTML}") > t.index('<div class="metrics">${stats}</div>')


def test_ledger_is_framed_as_a_model_portfolio_not_a_live_track():
    t = _read(LEDGER_TEMPLATE)
    assert "Model Portfolio" in t
    assert "HYPOTHETICAL" in t
    # The abandoned "live / seeded 2-day" framing must be gone.
    assert "seed / live divider" not in t
    assert "live forward ledger" not in t


def test_ledger_renders_alpha_beta_attribution_panel():
    t = _read(LEDGER_TEMPLATE)
    assert "Return attribution" in t
    assert "attribHTML" in t
    assert "s.attribution" in t


def test_tearsheet_carries_hypothetical_disclosure():
    t = _read(TEARSHEET_TEMPLATE)
    assert 'class="disclaimer"' in t
    assert "Hypothetical" in t
    for phrase in _REQUIRED_PHRASES:
        assert phrase in t, f"tearsheet disclosure missing: {phrase!r}"


def test_cross_pages_drop_the_live_track_framing():
    # Landing/hub/thesis should point at the Model Portfolio, not a "live forward ledger".
    for tmpl in (HUB_TEMPLATE, THESIS_TEMPLATE, TEMPLATE):
        t = _read(tmpl)
        assert "live forward ledger" not in t, f"{tmpl.name} still says 'live forward ledger'"


# Driftwood is NOT a registered investment adviser. Every client-facing surface must carry the corrected
# registration disclosure, and the old registration claim (ADV/CRS/adviserinfo links) must never reappear.
def test_every_exhibit_carries_the_registration_disclosure():
    for tmpl in (LEDGER_TEMPLATE, TEARSHEET_TEMPLATE, HUB_TEMPLATE, THESIS_TEMPLATE,
                 TEMPLATE, TAXLAB_TEMPLATE, LEAKAGE_TEMPLATE):
        t = _read(tmpl)
        assert "Park Avenue Securities" in t, f"{tmpl.name}: missing the PAS/Guardian disclosure"
        assert "adviserinfo.sec.gov" not in t, f"{tmpl.name}: stale adviserinfo link (the entity is not registered)"
        assert "Form ADV" not in t and "Form CRS" not in t, f"{tmpl.name}: stale Form ADV/CRS reference"


def test_no_cws_planning_brand_anywhere():
    # The RIA identity is now "Driftwood" itself. The legacy "CWS Planning" brand/legal token must not
    # appear on any shipped surface (the RIA-disclosure phrases guarded above are preserved separately).
    # NB: the functional Calendly booking slug may still contain "cwsplanning" — that is a live URL, not
    # a brand reference, so we check for the human brand phrase, not the slug.
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    targets = list((root / "src" / "drift" / "web").glob("*.html"))
    targets += [root / "src" / "drift" / "statepage.py", root / "src" / "drift" / "firm_models.py",
                root / "scripts" / "og_cards.mjs", root / "scripts" / "og_states.mjs"]
    for p in targets:
        t = p.read_text()
        assert "CWS Planning" not in t and "CWS&nbsp;Planning" not in t, \
            f"{p.name} still references the retired 'CWS Planning' brand"


def test_one_affiliate_sentence_names_one_firm():
    """The affiliate disclaimer must name Driftwood Wealth, and only Driftwood Wealth.

    test_no_cws_planning_brand_anywhere above purges the short brand "CWS Planning" but not the
    long legal form, and that gap shipped: four pages — including hub.html, which sync_docs.py
    renders as docs/index.html, the front door — carried "Capitol Wealth Strategies, LLC" in the
    affiliate sentence while forty-four siblings named Driftwood Wealth. Two of those four named
    both firms at once. site.py's FIRM_LEGAL_NAME is the arbiter, and one firm identity means one
    sentence, not a majority of one.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    canonical = "Driftwood Wealth is not an affiliate or subsidiary of PAS."
    seen: list[str] = []
    for p in sorted((root / "src" / "drift" / "web").glob("*.html")):
        raw = p.read_text()
        assert "Capitol Wealth Strategies" not in raw, \
            f"{p.name} names the retired legal entity 'Capitol Wealth Strategies, LLC'"
        # These pages hard-wrap their disclosure paragraph, so compare on collapsed whitespace —
        # the sentence is the unit under test, not the column the author happened to wrap at.
        t = re.sub(r"\s+", " ", raw)
        found = re.findall(r"[A-Za-z,. ]*?\b(?:is|are) not (?:an affiliate|affiliates) or "
                           r"subsidiar(?:y|ies) of PAS\.", t)
        for sentence in found:
            assert sentence.strip().endswith(canonical), \
                f"{p.name} varies the affiliate sentence: {sentence.strip()!r}"
        seen.extend(found)
    # A regex that matches nothing passes every assertion under it. When the Guardian entity was
    # removed on 2026-08-03 this pattern stopped matching anywhere and the test went green while
    # checking nothing at all, which is the failure mode a disclosure guard can least afford.
    assert len(seen) > 30, (
        f"the affiliate sentence was found on only {len(seen)} pages, so this test is no longer "
        "checking the thing it names")


def test_hypothetical_exhibits_carry_an_audience_statement():
    # P0-2: hypothetical performance shown publicly must state its intended audience and relevance
    # limits (subtle but always rendered). Guards the audience line against removal.
    for tmpl in (LEDGER_TEMPLATE, TEARSHEET_TEMPLATE, LEAKAGE_TEMPLATE):
        t = _read(tmpl)
        assert "Intended for sophisticated investors" in t, f"{tmpl.name}: no audience statement"
        assert "may not be relevant to your situation" in t


def test_ledger_attribution_states_alpha_significance_and_out_of_sample():
    # Alpha must be shown with a significance test and an out-of-sample readout, not as a bare
    # "edge" (M1 / M2) — guards against the over-confident framing creeping back.
    t = _read(LEDGER_TEMPLATE)
    assert "t-stat" in t
    assert "alpha_significant" in t and "alpha_t" in t
    assert "Out-of-sample only" in t
    assert "attribution_oos" in t


# ── Structural Alpha pivot ────────────────────────────────────────────────────────────────────
# The value proposition is "Structural Alpha" — deterministic tax+fee engineering plus deliberate
# factor EXPOSURE ("engineered beta"), explicitly NOT a forecast that the funds out-perform, and NOT
# momentum/market-timing. The momentum work is demoted to an honestly-labeled research satellite.

def test_thesis_leads_with_the_investment_philosophy_not_product_names():
    # The Approach page is now "How We Invest": an evidence-based philosophy, led by principles rather
    # than product names or the retired drift / diffusion name story. Named strategies are demoted to a
    # quiet implementation detail beneath the architecture (which is the product).
    t = _read(THESIS_TEMPLATE)
    assert "How We Invest" in t
    assert "Evidence over prediction" in t
    assert "institutional portfolio architecture" in t.lower()
    # the retired mathematical name-origin / factor-pitch framing is gone
    assert "engineered beta" not in t.lower()
    assert "not market timing" not in t.lower()
    assert "random-walk null" not in t.lower()


def test_core_alpha_exhibits_carry_the_research_banner():
    # The Core Alpha (momentum) dashboard, ledger, and long-history tearsheet are hypothetical model
    # portfolios, not client accounts. Each must carry the honest banner: labeled Core Alpha Research
    # (a hypothetical Model Portfolio) AND name the flagship Structural Alpha as the deployed strategy —
    # so the momentum track can never be mistaken for the shipped, tax-managed client book.
    for tmpl in (LEDGER_TEMPLATE, TEARSHEET_TEMPLATE, TEMPLATE):
        t = _read(tmpl)
        assert "research-banner" in t, f"{tmpl.name}: missing the research banner"
        assert "Core Alpha Research" in t, f"{tmpl.name}: banner not labeled Core Alpha Research"
        assert "Structural Alpha" in t, f"{tmpl.name}: banner does not name the flagship strategy"
        assert "hypothetical" in t.lower(), f"{tmpl.name}: banner must label the track hypothetical"


def test_the_guardian_entity_is_gone_from_every_shipped_surface():
    """Removed 2026-08-03 at the principal's direction: the practice is under Park Avenue
    Securities with custody at BNY Pershing, and the Guardian affiliation no longer describes it.

    Scanned across BOTH trees plus the generators, because the disclosure reaches a page by three
    different routes (a hand-written template, sync_docs.py, and the state-page generator), and a
    stale affiliation surviving on one of them is a false statement about who the firm is.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    targets = (list((root / "src" / "drift" / "web").glob("*.html"))
               + list((root / "docs").glob("*.html"))
               + [root / "src" / "drift" / "statepage.py", root / "scripts" / "phase2_nav.py"])
    offenders = [str(p.relative_to(root)) for p in targets
                 if "Guardian" in p.read_text(encoding="utf-8", errors="replace")]
    assert not offenders, f"the Guardian affiliation is back on: {offenders[:8]}"


def test_the_park_avenue_disclosure_survived_the_removal():
    """The other half. Cutting Guardian must not have taken the broker-dealer with it, and the
    sentence that remains has to still read as a sentence rather than as a seam."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    import re as _re
    checked = 0
    for p in sorted((root / "docs").glob("*.html")):
        t = _re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="replace"))
        if "Park Avenue Securities" not in t:
            continue
        checked += 1
        assert "Registered Representative" in t, f"{p.name} lost the representative disclosure"
        # The seam the removal could leave: the clause that was cut carried the space in front of
        # it, so "Financial Advisor of PAS and a Financial Representative of ..." collapses to
        # "Financial Advisor of PAS ." if the space is not taken with it. Scoped to the sentence
        # rather than the document, because a stylesheet is full of " ." class selectors.
        assert not _re.search(r"of PAS\s+\.", t), f"{p.name} has a dangling space before a period"
        assert not _re.search(r"subsidiary of PAS\s+\.", t), f"{p.name} has a seam in the affiliate line"
    assert checked > 40, f"only {checked} pages carry the PAS disclosure"
