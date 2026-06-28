"""Guards for the multi-dimension State Tax Map (statemap.py + statemap.html).

Five dimensions per state from FACTUAL classifications (our own copy/design — not a clone of any third
party's titles, editorial prose, or assets). These tests lock dataset coverage + correctness, the
no-fabrication boundary (Structural Alpha only where we own the figure), the compliance framing, and
the originality posture.
"""

import json

from drift.statemap import build_statemap, DIMENSIONS, STATE_ALPHA
from drift.exhibit import STATEMAP_TEMPLATE, render_statemap
from drift.taxlab import build_taxlab
from drift.hub import build_hub


def test_dataset_shape_and_dimension_order():
    s = build_statemap()
    json.dumps(s)                                              # JSON-able for embedding
    assert [d["key"] for d in s["dimensions"]] == ["cg", "marriage", "estate", "stepup", "alpha"]
    assert s["dimensions"][-1]["key"] == "alpha" and s["dimensions"][-1].get("highlight") is True
    assert len(s["states"]) == 56                             # 50 + DC + 5 territories


def test_per_dimension_coverage_and_no_fabricated_alpha():
    st = build_statemap()["states"]
    # marriage / estate / step-up classify every tile (incl. territories)
    for dim in ("marriage", "estate", "stepup"):
        assert sum(1 for c in st if dim in st[c]) == 56, dim
    # income & gains classifies every tile (incl. territories); Structural Alpha only where we own it
    assert sum(1 for c in st if "cg" in st[c]) == 56
    assert sum(1 for c in st if "alpha" in st[c]) == 51    # STATE_ALPHA has no territories
    # alpha is present iff we have the figure in STATE_ALPHA — never fabricated
    for c, rec in st.items():
        assert ("alpha" in rec) == (c in STATE_ALPHA)


def test_classifications_are_correct():
    st = build_statemap()["states"]
    # the 9 community-property states (settled law)
    cp = {c for c in st if st[c].get("stepup", {}).get("regime") == "community"}
    assert {"AZ", "CA", "ID", "LA", "NV", "NM", "TX", "WA", "WI"} <= cp
    # estate-tax states include IL (the legacy map omitted it); MD is "both"
    estate = {c for c in st if st[c].get("estate", {}).get("regime") in ("estate", "both")}
    assert {"IL", "WA", "OR", "MN", "MA", "NY", "CT", "RI", "VT", "ME", "HI", "DC"} <= estate
    assert st["MD"]["estate"]["regime"] == "both"
    # harvested-loss conformity: PA/NJ/AL non-conforming; WA long-term-only; MO no-tax
    assert st["PA"]["cg"]["regime"] == "nonconforming" and st["NJ"]["cg"]["regime"] == "nonconforming"
    assert st["WA"]["cg"]["regime"] == "lt_only" and st["MO"]["cg"]["regime"] == "notax"


def test_template_is_original_and_carries_compliance_framing():
    t = STATEMAP_TEMPLATE.read_text()
    # ORIGINALITY: our own title/framing — not the third-party feature's branding or assets
    assert "Fifty states. One after-tax plan." in t
    assert "Fifty states, fifty tax personalities" not in t
    assert "America turns 250" not in t
    assert "taxalphainsider" not in t.lower()
    # reads the deep-link params + routes Structural Alpha into the diagnostic
    assert 'qp.get("state")' in t and 'qp.get("dim")' in t
    # compliance: not advice; the alpha dimension is illustrative/hypothetical + RIA identity
    assert "not tax, legal, or investment advice" in t
    assert "illustrative" in t and "not a forecast that any fund out-perform" in t
    assert "registered investment adviser" in t and "adviserinfo.sec.gov" in t
    # the rendered page bakes the per-state diagnostic deep-links + drops the placeholder
    html = render_statemap(build_statemap())
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert "leakage.html?state=IL" in html


def test_tax_lab_embeds_the_dimension_dataset(tmp_path):
    s = build_taxlab(tmp_path)
    sm = s.get("statemap")
    assert sm and [d["key"] for d in sm["dimensions"]] == ["cg", "marriage", "estate", "stepup", "alpha"]
    assert "IL" in sm["states"] and "estate" in sm["states"]["IL"]


def test_statemap_in_the_primary_funnel(tmp_path):
    state = build_hub(tmp_path)
    sm = next(e for e in state["exhibits"] if e["href"] == "statemap.html")
    assert sm["appendix"] is False
