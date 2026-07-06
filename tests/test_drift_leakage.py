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
    assert "Tax Diagnostic" in t
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
    assert lk["appendix"] is False                 # it's a flagship tax tool, not Core Alpha research
    assert "tax" in lk["desc"].lower()             # the quantified tax edge (the tax-location engine)


def test_state_alpha_table_covers_states_and_matches_the_static_anchors():
    s = build_leakage()
    sa = s["state_alpha"]
    # broad coverage for the personalized diagnostic, incl. no-tax + high-tax + NYC overlay
    for code in ("—", "IL", "NY", "CA", "TX", "FL", "NYC", "MA"):
        assert code in sa and {"before", "after", "alpha"} <= set(sa[code])
    assert len(sa) >= 50
    # the per-state table is the SAME source as the static "by state" rows (no drift)
    by_label = {r["state"]: r for r in s["states"]}
    assert by_label["Illinois"]["alpha"] == sa["IL"]["alpha"] == 4.0     # 30y window (1996–2026)
    assert by_label["California"]["alpha"] == sa["CA"]["alpha"] == 4.7
    # higher state rate -> larger recovered alpha (CA/NYC > IL > no-tax)
    assert sa["NYC"]["alpha"] >= sa["CA"]["alpha"] >= sa["IL"]["alpha"] >= sa["—"]["alpha"]
    # every prospect state keeps more after the engine
    for code, r in sa.items():
        assert r["after"] > r["before"]


def test_leakage_template_personalizes_and_carries_a_booking_cta():
    t = LEAKAGE_TEMPLATE.read_text()
    # reads the cold-outreach deep-link params and localizes off the per-state table
    assert 'qp.get("state")' in t and ('qp.get("portfolio")' in t or 'qp.get("port")' in t)
    assert "state_alpha" in t and "pband" in t
    # compliant reframe (Marketing-Rule): "up to ... in our illustrative modeling", diagnostic-gated
    assert "up to +" in t and "illustrative modeling" in t
    assert "Your actual figure depends on your" in t
    # booking / conversion CTA into the After-Tax Review's Review Summary, forwarding params + utm attribution
    assert 'id="cta-analysis"' in t and "view=review" in t
    assert "utm_campaign" in t                       # campaign params forwarded for attribution
