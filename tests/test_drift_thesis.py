import json

from drift.thesis import build_thesis
from drift.exhibit import render_thesis


def _write_tearsheet(tmp_path):
    state = {"books": [
        {"name": "Equities & ETFs", "n_names": 18, "span": ["1993-02-01", "2026-06-15"],
         "strategy": {"max_drawdown": 0.097, "sharpe": 0.59, "cagr": 0.025},
         "benchmark": {"max_drawdown": 0.506, "sharpe": 0.68, "cagr": 0.107},
         "oos": {"test": {"sharpe": 0.39}}},
    ]}
    (tmp_path / "tearsheet.html").write_text("a window.__STATE__ = " + json.dumps(state) + ";\n b")


def test_build_thesis_pulls_equities(tmp_path):
    _write_tearsheet(tmp_path)
    s = build_thesis(tmp_path)
    assert s["equities"]["span"] == "1993–2026"
    assert s["equities"]["n_names"] == 18
    assert s["equities"]["strat_maxdd"] == 0.097
    assert "crypto" not in s


def test_build_thesis_reads_ledger(tmp_path):
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2026-02-17", "universe": list("abcde"),
        "entries": [{"equity": 1.0}, {"equity": 1.03}],
    }))
    s = build_thesis(tmp_path)
    assert round(s["ledger"]["total_return"], 4) == 0.03
    assert s["ledger"]["sessions"] == 2


def test_build_thesis_degrades_without_files(tmp_path):
    s = build_thesis(tmp_path)
    assert s["equities"] is None and s["ledger"] is None
    json.dumps(s)


def test_render_thesis_embeds_state_and_leads_with_the_philosophy(tmp_path):
    _write_tearsheet(tmp_path)
    html = render_thesis(build_thesis(tmp_path))
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert html.lstrip().startswith("<!DOCTYPE html>")
    # The Approach page is now "How We Invest" — an evidence-first philosophy, not the retired
    # drift / diffusion name story.
    assert "How We Invest" in html
    assert "Evidence over prediction" in html
    assert "random-walk null" not in html.lower()
    assert "driftwood" in html.lower()
