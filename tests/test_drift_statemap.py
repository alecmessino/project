"""Guards for the multi-dimension State Tax Map (statemap.py + statemap.html).

Seven FACTUAL regime dimensions per state (income & gains · marriage · death · munis · QSBS · losses ·
basis step-up) plus a highlighted Structural-Alpha synthesis tab. These tests lock dataset coverage +
correctness, the no-fabrication boundaries (Structural Alpha only where we own the figure; a "Prove it"
statutory citation only where the exact code section is verified), and the compliance framing. The site
copy/design is our own; we still refuse to reuse the third party's brand name or assets.
"""

import json

from drift.statemap import build_statemap, DIMENSIONS, STATE_ALPHA
from drift.exhibit import STATEMAP_TEMPLATE, render_statemap
from drift.taxlab import build_taxlab
from drift.hub import build_hub


def test_dataset_shape_and_dimension_order():
    s = build_statemap()
    json.dumps(s)                                              # JSON-able for embedding
    assert [d["key"] for d in s["dimensions"]] == \
        ["cg", "marriage", "estate", "muni", "qsbs", "loss", "stepup", "alpha"]
    assert s["dimensions"][-1]["key"] == "alpha" and s["dimensions"][-1].get("highlight") is True
    assert len(s["states"]) == 56                             # 50 + DC + 5 territories


def test_per_dimension_coverage_and_no_fabricated_alpha():
    st = build_statemap()["states"]
    # every factual dimension classifies every tile (incl. territories)
    for dim in ("cg", "marriage", "estate", "muni", "qsbs", "loss", "stepup"):
        assert sum(1 for c in st if dim in st[c]) == 56, dim
    # Structural Alpha only where we own the figure
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


def test_prove_it_citations_only_where_verified():
    st = build_statemap()["states"]
    # IL is the one state whose exact statutes we've verified — every factual dimension carries a citation.
    for dim in ("cg", "marriage", "estate", "muni", "qsbs", "loss"):
        cites = st["IL"][dim].get("citation")
        assert cites and all(c["url"].startswith("http") and c["label"] for c in cites), dim
    assert any("35 ILCS 405/3" in c["label"] for c in st["IL"]["estate"]["citation"])
    # NO OTHER state carries a fabricated citation — they show the generic source line instead.
    for c, rec in st.items():
        if c == "IL":
            continue
        for dim, r in rec.items():
            assert "citation" not in r, f"{c}/{dim} has an unverified citation"
    # the template renders the Prove-it link and keeps the no-fabrication note
    t = STATEMAP_TEMPLATE.read_text()
    assert "Prove it:" in t


def test_template_is_original_and_carries_compliance_framing():
    t = STATEMAP_TEMPLATE.read_text()
    # Firm-approved editorial copy; the dated 250th-anniversary eyebrow was retired for a timeless one.
    assert "Fifty states, fifty tax personalities" in t
    assert "America turns 250" not in t
    assert "The State Tax Guide" in t
    # ORIGINALITY: we still never reuse the third party's brand name or assets.
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
    assert sm and [d["key"] for d in sm["dimensions"]] == \
        ["cg", "marriage", "estate", "muni", "qsbs", "loss", "stepup", "alpha"]
    assert "IL" in sm["states"] and "estate" in sm["states"]["IL"]


def test_statemap_in_the_primary_funnel(tmp_path):
    state = build_hub(tmp_path)
    sm = next(e for e in state["exhibits"] if e["href"] == "statemap.html")
    assert sm["appendix"] is False
