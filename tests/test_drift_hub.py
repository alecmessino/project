import json

from drift.hub import build_hub
from drift.exhibit import render_hub


def test_build_hub_empty_docs_lists_all_exhibits_absent(tmp_path):
    state = build_hub(tmp_path)
    assert state["exhibits"]                       # always lists the exhibit index
    assert all(not e["present"] for e in state["exhibits"])
    assert state["headline"] == []                 # no data files -> no headlines
    json.dumps(state)


def test_build_hub_reads_ledger_headline(tmp_path):
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2026-02-17",
        "entries": [{"equity": 1.0}, {"equity": 1.085}],
    }))
    (tmp_path / "ledger.html").write_text("<html></html>")
    state = build_hub(tmp_path)
    led = [h for h in state["headline"] if h["label"] == "Model Portfolio (hypothetical)"]
    assert led and led[0]["value"] == "+8.5%"
    # A hypothetical return is never coloured as a win (fair-and-balanced framing).
    assert led[0]["tone"] == "neutral"
    assert "hypothetical" in led[0]["sub"]
    # the present file is marked linkable
    assert any(e["href"] == "ledger.html" and e["present"] for e in state["exhibits"])


def test_model_portfolio_headline_carries_ITS_OWN_drawdown_not_the_long_backtests(tmp_path):
    # Corrected P0-3: the 445-session track's return must be paired with the 445-session track's
    # OWN drawdown — never the multi-decade backtest's. A peak-to-trough dip mid-series proves the
    # headline drawdown is computed from this ledger's equity, not borrowed from the tearsheet.
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2024-09-16",
        "entries": [{"equity": 1.0}, {"equity": 1.20}, {"equity": 1.02}, {"equity": 1.406}],
    }))
    ts_state = {"books": [{
        "name": "Equities & ETFs",
        "strategy": {"max_drawdown": 0.59},
        "benchmark": {"max_drawdown": 0.58},
        "oos": {"test": {"sharpe": 0.77}},
    }]}
    (tmp_path / "tearsheet.html").write_text(
        "x window.__STATE__ = " + json.dumps(ts_state) + ";\n y")
    state = build_hub(tmp_path)
    led = [h for h in state["headline"] if h["label"] == "Model Portfolio (hypothetical)"][0]
    assert led["value"] == "+40.6%"
    assert led["tone"] == "neutral"
    # Its own drawdown: 1.20 -> 1.02 is a 15% peak-to-trough dip, NOT the backtest's 59%.
    assert led["dd"] == "−15%"
    assert "59%" not in led["sub"]                 # the long-backtest DD is never stapled to this return
    assert "59%" not in led.get("dd", "")
    # The multi-decade "N% vs N%" drawdown headline was retired from the hub — it must not reappear
    # stapled to (or near) this return.
    assert not [h for h in state["headline"] if "max drawdown" in h["label"]]


def test_value_adds_sourced_and_fair_and_balanced(tmp_path):
    # The three investor value-adds are built from real exhibit state, each paired with its risk.
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2024-09-16",
        "entries": [{"equity": 1.0}, {"equity": 1.20}, {"equity": 1.02}, {"equity": 1.406}],
    }))
    led_state = {"header": {"total_return": 0.406, "after_tax_total_return": 0.267,
                            "tax_drag": 0.139, "sharpe": 1.35},
                 "benchmarks": [{"label": "VT", "sharpe": 1.21, "max_drawdown": 0.165},
                                {"label": "VTI", "sharpe": 1.05, "max_drawdown": 0.193}]}
    (tmp_path / "ledger.html").write_text(
        "x window.__STATE__ = " + json.dumps(led_state) + ";\n y")
    ts_state = {"books": [{"name": "Equities & ETFs", "strategy": {"max_drawdown": 0.59},
                           "benchmark": {"max_drawdown": 0.58}, "oos": {"test": {"sharpe": 0.77}}}]}
    (tmp_path / "tearsheet.html").write_text(
        "x window.__STATE__ = " + json.dumps(ts_state) + ";\n y")
    va = build_hub(tmp_path)["value_adds"]
    tags = [v["tag"] for v in va]
    # The three pillars headline the idea; implementation names are demoted into the notes.
    assert any("taxable core" in t.lower() for t in tags)   # 1 · the taxable core
    assert any("complement" in t.lower() for t in tags)     # 2 · the complement (tax-advantaged)
    assert any("Asset location" in t for t in tags)         # 3 · the decision that routes them
    assert not any("Alpha" in t for t in tags)              # product names never headline a pillar
    flag = next(v for v in va if "Structural Alpha" in v["note"])
    assert flag["stat"].startswith("+") and "%/yr" in flag["stat"]   # leads with the tax-recovery band
    core = next(v for v in va if "Core Alpha" in v["note"])
    assert "persist" in core["note"].lower()            # persistence framing, not a Sharpe race
    assert "1.35" in core["note"]                       # the current hypothetical track is CONTEXT, in the note
    loc = next(v for v in va if "Asset location" in v["tag"])
    # Dollars, not retained-gain percentages: keep_pct% of a $1M realized gain, one source of truth.
    from drift.leakage import build_leakage
    leak = build_leakage()
    lo, hi = leak["before"]["keep_pct"] * 10_000, leak["after"]["keep_pct"] * 10_000
    assert loc["stat"] == f"${lo:,.0f} → ${hi:,.0f}"
    assert "$1 million of realized gains" in loc["stat_label"]


def test_hub_does_not_surface_the_low_signal_drawdown_headline(tmp_path):
    # The near-tie "N% vs N% max drawdown" figure was retired from the hub (it communicated little to a
    # prospect); the tearsheet still carries it in context. The hub must no longer generate it.
    ts_state = {"books": [{
        "name": "Equities & ETFs",
        "strategy": {"max_drawdown": 0.068},
        "benchmark": {"max_drawdown": 0.507},
        "oos": {"test": {"sharpe": 0.49}},
    }]}
    (tmp_path / "tearsheet.html").write_text(
        "x window.__STATE__ = " + json.dumps(ts_state) + ";\n y")
    state = build_hub(tmp_path)
    assert not [h for h in state["headline"] if "max drawdown" in h["label"]]


def test_render_hub_embeds_state(tmp_path):
    html = render_hub(build_hub(tmp_path))
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "Driftwood" in html or "Drift" in html


def test_hub_funnel_leads_with_structural_alpha_and_demotes_momentum_to_appendix(tmp_path):
    # Architecture framing: the primary funnel is the flagship Structural Alpha + tax-location tools
    # (Thesis, Tax Lab); the Core Alpha (momentum) hypothetical model portfolios sit in a labeled
    # "Core Alpha Research" appendix — the tactical engine, not the deployed taxable-account strategy.
    state = build_hub(tmp_path)
    by_href = {e["href"]: e for e in state["exhibits"]}
    # primary funnel — NOT appendix
    assert by_href["thesis.html"]["appendix"] is False
    assert by_href["taxlab.html"]["appendix"] is False
    # Core Alpha research — appendix
    for h in ("ledger.html", "tearsheet.html", "equities.html", "equities_case_studies.html"):
        assert by_href[h]["appendix"] is True, f"{h} should be in the Core Alpha Research appendix"
    # the momentum exhibits are described as Core Alpha Research, not the deployed book
    assert "Core Alpha Research" in by_href["ledger.html"]["desc"]
    assert "Core Alpha Research" in by_href["equities.html"]["desc"]


def test_hero_leads_with_the_structural_alpha_before_after(tmp_path):
    # The hero is the substantiated tax edge (keep-rate before/after + the alpha band), sourced from
    # the regression-locked leakage engine — available even on a bare checkout, never a raw return.
    state = build_hub(tmp_path)
    hr = state["hero"]
    assert hr["keep_before"] < hr["keep_after"]                    # a before/after, not a bare number
    # the honest inversion: slightly LESS pre-tax, wealthier after tax
    assert hr["pretax_after"] < hr["pretax_before"]
    assert 0 < hr["alpha_low"] <= hr["alpha_high"] < 10
    assert hr["horizon"] == 30
    from drift.leakage import build_leakage
    leak = build_leakage()
    assert hr["alpha_low"] == leak["headline"]["alpha_low"]        # single source of truth
    assert hr["keep_after"] == leak["after"]["keep_pct"]


def test_raw_model_return_is_research_tagged_for_the_appendix(tmp_path):
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2024-09-16",
        "entries": [{"equity": 1.0, "date": "2026-06-26"}, {"equity": 1.41, "date": "2026-06-29"}],
    }))
    state = build_hub(tmp_path)
    mp = next(h for h in state["headline"] if h["label"] == "Model Portfolio (hypothetical)")
    assert mp.get("research") is True                              # renders in the appendix, not the hero
    assert "data through 2026-06-29" in mp["sub"]                  # the figure is always dated


def test_hub_leads_with_belief_not_positioning():
    # Belief-first hero: the front door states what we optimize for (what you keep), and the firm's
    # central sentence appears quietly — the "institutional portfolio architecture" positioning is
    # discovered later (on the thesis page's banner), not led with, and "architecture" is rationed here.
    from drift.exhibit import HUB_TEMPLATE
    t = HUB_TEMPLATE.read_text()
    assert "maximize what you keep" in t
    assert "pay attention to different things" in t          # the sentence the firm rests on
    assert "The architecture" not in t                       # the old machinery-led header is gone


def test_hub_template_renders_a_core_alpha_research_appendix_and_does_not_lead_with_the_ledger():
    from drift.exhibit import HUB_TEMPLATE
    t = HUB_TEMPLATE.read_text()
    # a distinct, labeled appendix section exists, separate from the primary exhibit grid
    assert "exhibits-appendix" in t and "Core Alpha Research" in t
    assert "Structural Alpha" in t
    # the hero no longer leads with the momentum "track record"
    assert "View the track record" not in t
