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


def test_model_portfolio_headline_carries_its_drawdown_when_tearsheet_present(tmp_path):
    # P0-3: a return shown without its drawdown is imbalanced — the MP card must carry both.
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2024-09-16",
        "entries": [{"equity": 1.0}, {"equity": 1.406}],
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
    assert "max drawdown" in led["sub"] and "59%" in led["sub"]   # risk shown beside return


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
