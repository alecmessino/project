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
    # The multi-decade drawdown still appears — explicitly attributed to the long backtest.
    dd = [h for h in state["headline"] if "max drawdown" in h["label"]][0]
    assert dd["value"] == "59% vs 58%" and "multi-decade" in dd["sub"]


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
    assert any("Tax" in t for t in tags)            # 1 · tax + fee optimization
    assert any("Risk" in t for t in tags)           # 2 · risk-managed, paired with its drawdown
    assert any("decades" in t for t in tags)        # 3 · out-of-sample honesty
    tax = next(v for v in va if "Tax" in v["tag"])
    assert tax["stat"] == "−14%"                    # the tax drag itself, not a promised return
    risk = next(v for v in va if "Risk" in v["tag"])
    assert "−15%" in risk["note"]                   # this track's own drawdown, shown beside Sharpe
    oos = next(v for v in va if "decades" in v["tag"])
    assert "59%" in oos["note"]                     # the long-backtest worst loss, disclosed


def test_build_hub_reads_tearsheet_drawdown_headline(tmp_path):
    ts_state = {"books": [{
        "name": "Equities & ETFs",
        "strategy": {"max_drawdown": 0.068},
        "benchmark": {"max_drawdown": 0.507},
        "oos": {"test": {"sharpe": 0.49}},
    }]}
    html = "x window.__STATE__ = " + json.dumps(ts_state) + ";\n y"
    (tmp_path / "tearsheet.html").write_text(html)
    state = build_hub(tmp_path)
    dd = [h for h in state["headline"] if "max drawdown" in h["label"]]
    assert dd and dd[0]["value"] == "7% vs 51%"


def test_render_hub_embeds_state(tmp_path):
    html = render_hub(build_hub(tmp_path))
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "Driftwood" in html or "Drift" in html


def test_hub_funnel_leads_with_structural_alpha_and_demotes_momentum_to_appendix(tmp_path):
    # Structural Alpha pivot: the primary funnel leads with the structural narrative (Thesis, Tax Lab);
    # the momentum exhibits (ledger, tearsheet, dashboard, case studies) are relegated to an honestly
    # labeled "Exploratory research" appendix — proof of work, not the deployed strategy.
    state = build_hub(tmp_path)
    by_href = {e["href"]: e for e in state["exhibits"]}
    # primary funnel — NOT appendix
    assert by_href["thesis.html"]["appendix"] is False
    assert by_href["taxlab.html"]["appendix"] is False
    # exploratory research — appendix
    for h in ("ledger.html", "tearsheet.html", "equities.html", "equities_case_studies.html"):
        assert by_href[h]["appendix"] is True, f"{h} should be in the exploratory-research appendix"
    # the momentum exhibits are described as exploratory research, not the deployed book
    assert "Exploratory research" in by_href["ledger.html"]["desc"]
    assert "Exploratory research" in by_href["equities.html"]["desc"]


def test_hub_template_renders_an_exploratory_research_appendix_and_does_not_lead_with_the_ledger():
    from drift.exhibit import HUB_TEMPLATE
    t = HUB_TEMPLATE.read_text()
    # a distinct, labeled appendix section exists, separate from the primary exhibit grid
    assert "exhibits-appendix" in t and "Exploratory research" in t
    assert "Structural Alpha" in t
    # the hero no longer leads with the momentum "track record"
    assert "View the track record" not in t
