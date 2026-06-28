"""Guards for the Tax-Leakage Diagnostic (D2) — the one-page Before/After pitch artifact.

The diagnostic is a Structural Alpha proof: a concentrated, high-turnover book leaking tax versus the
tax-managed engine plugging it, sourced from the Tax-Alpha decomposition (scripts/tax_alpha.py). These
tests lock its numbers' provenance + structure, the compliance framing, and its place in the PRIMARY
client funnel (not the exploratory-research appendix).
"""

import json

from drift.leakage import build_leakage
from drift.exhibit import LEAKAGE_TEMPLATE, render_leakage
from drift.hub import build_hub


def test_build_leakage_state_is_well_formed_and_before_leaks_more_than_after():
    s = build_leakage()
    json.dumps(s)                                  # JSON-able for embedding
    b, a, h = s["before"], s["after"], s["headline"]
    # The whole point: the concentrated book leaks more (keeps less, higher ST%, higher turnover).
    assert b["keep_pct"] < a["keep_pct"]
    assert b["st_share"] > a["st_share"]
    assert b["turnover"] > a["turnover"]
    # After-tax CAGR strictly improves on both ends of the state range.
    assert a["atc_low"] > b["atc_low"] and a["atc_high"] > b["atc_high"]
    # Headline recovery is positive and the structural book is NOT claimed to out-earn pre-tax.
    assert 0 < h["alpha_low"] <= h["alpha_high"]
    assert h["pretax_after"] <= h["pretax_before"]


def test_leakage_states_show_tax_alpha_rising_with_the_rate():
    # The CPA point: tax management matters MORE as the rate climbs — Tax Alpha increases monotonically
    # from the federal-only row to California.
    rows = build_leakage()["states"]
    alphas = [r["alpha"] for r in rows]
    assert alphas == sorted(alphas)                # non-decreasing federal -> CA
    assert rows[0]["state"].lower().startswith("federal") and "California" in rows[-1]["state"]
    for r in rows:
        assert r["after"] > r["before"]            # every environment keeps more after the engine
        assert abs((r["after"] - r["before"]) - r["alpha"]) < 0.31  # alpha ≈ the after-before gap


def test_leakage_template_carries_the_structural_alpha_and_compliance_framing():
    t = LEAKAGE_TEMPLATE.read_text()
    assert "Tax-Leakage Diagnostic" in t
    assert "Structural Alpha" in t
    # honesty / Marketing-Rule guards
    assert "not a forecast that these funds out-perform" in t
    assert "NOT claimed to out-earn pre-tax" in t
    for phrase in ("retroactive application", "no client capital was invested",
                   "does not guarantee future results"):
        assert phrase in t, f"leakage disclosure missing: {phrase!r}"
    # the embed point exists and renders without the placeholder
    html = render_leakage(build_leakage())
    assert "/*__STATE__*/null/*__END__*/" not in html


def test_leakage_is_in_the_primary_funnel_not_the_research_appendix(tmp_path):
    state = build_hub(tmp_path)
    lk = next(e for e in state["exhibits"] if e["href"] == "leakage.html")
    assert lk["appendix"] is False                 # it leads with Structural Alpha, not proof-of-work
    assert "Structural Alpha" in lk["desc"]
