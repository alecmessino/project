"""Guards for the multi-dimension State Tax Map (statemap.py + statemap.html).

Seven FACTUAL regime dimensions per state (income & gains · marriage · death · munis · QSBS · losses ·
basis step-up) plus a descriptive Tax Management Impact dimension. These tests lock dataset coverage +
correctness, the no-fabrication boundaries (the impact figure only where we own it; a "Prove it"
statutory citation only where the exact code section is verified), and the compliance framing. The site
copy/design is our own; we still refuse to reuse the third party's brand name or assets.
"""

import json

from drift.statemap import build_statemap, DIMENSIONS, STATE_ALPHA, _CITATIONS
from drift.exhibit import STATEMAP_TEMPLATE, render_statemap
from drift.taxlab import build_taxlab
from drift.hub import build_hub


def test_dataset_shape_and_dimension_order():
    s = build_statemap()
    json.dumps(s)                                              # JSON-able for embedding
    assert [d["key"] for d in s["dimensions"]] == \
        ["cg", "marriage", "estate", "muni", "qsbs", "loss", "stepup", "alpha"]
    # the 8th is a peer reference dimension now (Tax Management Impact) — no longer a highlighted synthesis
    assert s["dimensions"][-1]["key"] == "alpha"
    assert not any(d.get("highlight") for d in s["dimensions"])
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
    # Every rendered citation must trace to the verified `_CITATIONS` whitelist and nowhere else — no
    # fabricated citations leak in, and every whitelist entry renders. (The seed batch adds the income-
    # &-gains imposing statute for CA/NY/TX/FL; the rest show the honest "summary" line.)
    verified = set(_CITATIONS.keys())
    assert {(s, "cg") for s in ("CA", "NY", "TX", "FL")} <= verified
    for c, rec in st.items():
        for dim, r in rec.items():
            assert ("citation" in r) == ((c, dim) in verified), f"{c}/{dim} citation mismatch"
    # the template renders the Prove-it link and keeps the no-fabrication note
    t = STATEMAP_TEMPLATE.read_text()
    assert "Statute:" in t


def test_template_is_original_and_carries_compliance_framing():
    t = STATEMAP_TEMPLATE.read_text()
    # Firm-approved editorial copy: the page is now the "State Tax Atlas" (a permanent reference), with
    # "Fifty states. Fifty tax personalities." as its subhead and "The Fifty States" as the eyebrow.
    assert "State Tax Atlas" in t
    assert "Fifty states. Fifty tax personalities." in t
    assert "The Fifty States" in t
    assert "America turns 250" not in t
    # ORIGINALITY: we still never reuse the third party's brand name or assets.
    assert "taxalphainsider" not in t.lower()
    # reads the deep-link params + routes Structural Alpha into the diagnostic
    assert 'qp.get("state")' in t and 'qp.get("dim")' in t
    # compliance: not advice; the alpha dimension is illustrative/hypothetical + RIA identity
    assert "not tax, legal, or investment advice" in t
    assert "illustrative" in t and "not a forecast that any fund out-perform" in t
    assert "Park Avenue Securities" in t and "adviserinfo.sec.gov" not in t
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
