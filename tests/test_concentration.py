"""Guards for the "Single asset risk" concentration tool (concentration.py + concentration.html).

The tool advertises a public decision aid — 22 de-risking strategies scored across six axes — so every
strategy must be fully scored (no blank cells), name a real family, carry a factual blurb and filter
tags, and the page must ship the not-advice framing + RIA identity. Dataset integrity here prevents a
half-populated heatmap from reaching the live site.
"""

import json

from drift.concentration import build_concentration, AXES, BUCKETS, STRATEGIES
from drift.exhibit import CONCENTRATION_TEMPLATE, render_concentration
from drift.hub import build_hub


def test_dataset_shape_is_complete():
    s = build_concentration()
    json.dumps(s)                                             # JSON-able for embedding
    assert len(s["axes"]) == 6 and len(s["buckets"]) == 5
    assert len(s["strategies"]) == len(STRATEGIES) == 22
    axis_keys = {a["key"] for a in AXES}
    bucket_keys = {b["key"] for b in BUCKETS}
    keys = [st["key"] for st in s["strategies"]]
    assert len(set(keys)) == len(keys), "duplicate strategy key"
    for st in s["strategies"]:
        # every axis scored 1–5 with a human label; no blank cells
        assert set(st["scores"]) == axis_keys, f"{st['key']} missing an axis"
        for ax, cell in st["scores"].items():
            assert 1 <= cell["n"] <= 5 and cell["label"], f"{st['key']}/{ax} bad score"
        assert st["bucket"] in bucket_keys
        assert st["blurb"] and len(st["blurb"]) > 40, f"{st['key']} needs a real blurb"
        assert st["goals"] and st["timelines"], f"{st['key']} needs filter tags"
        assert isinstance(st["simple"], bool) and isinstance(st["insider_ok"], bool)


def test_every_strategy_carries_committee_fit_notes():
    # The detail card reads like an investment committee, not a widget: for each strategy we say when
    # institutions typically reach for it, and where it fits or doesn't. Every strategy must carry all three.
    s = build_concentration()
    for st in s["strategies"]:
        fit = st.get("fit")
        assert fit and all(fit.get(k) and len(fit[k]) > 15 for k in ("inst", "when", "less")), \
            f"{st['key']} missing committee fit notes"
    t = CONCENTRATION_TEMPLATE.read_text()
    assert "When institutions consider this" in t
    assert "Appropriate when" in t and "Less appropriate when" in t


def test_every_bucket_is_represented():
    s = build_concentration()
    present = {st["bucket"] for st in s["strategies"]}
    assert present == {b["key"] for b in BUCKETS}, "a strategy family has no strategies"


def test_filter_tags_reference_real_options():
    s = build_concentration()
    goal_keys = {g["key"] for g in s["goals"]}
    tl_keys = {t["key"] for t in s["timelines"]}
    for st in s["strategies"]:
        assert set(st["goals"]) <= goal_keys, f"{st['key']} has an unknown goal tag"
        assert set(st["timelines"]) <= tl_keys, f"{st['key']} has an unknown timeline tag"
    # the insider filter must actually restrict something (direct single-stock hedges), else it's dead UI
    restricted = [st["key"] for st in s["strategies"] if not st["insider_ok"]]
    assert restricted, "no strategy is insider-restricted — the Current Employee filter would do nothing"


def test_template_renders_and_carries_compliance_framing():
    html = render_concentration(build_concentration())
    assert "/*__STATE__*/null/*__END__*/" not in html          # placeholder replaced
    assert '"strategies"' in html and '"axes"' in html          # dataset embedded
    t = CONCENTRATION_TEMPLATE.read_text()
    assert "How to de-risk a concentrated stock position" in t
    assert "Single asset risk" in t
    # not-advice + RIA identity
    assert "not tax, legal, or investment advice" in t
    assert "Park Avenue Securities" in t and "adviserinfo.sec.gov" not in t
    # ORIGINALITY: our own JS, not the third party's external asset
    assert "taxalphainsider" not in t.lower()


def test_tool_is_in_the_primary_funnel(tmp_path):
    state = build_hub(tmp_path)
    tool = next((e for e in state["exhibits"] if e["href"] == "concentration.html"), None)
    assert tool is not None and tool["appendix"] is False
