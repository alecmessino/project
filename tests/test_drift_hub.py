import json
import re
from pathlib import Path

from drift.hub import build_hub
from drift.exhibit import render_hub

WEB = Path(__file__).resolve().parents[1] / "src" / "drift" / "web"


def test_build_hub_empty_docs_lists_all_exhibits_absent(tmp_path):
    state = build_hub(tmp_path)
    assert state["exhibits"]                       # always lists the exhibit index
    assert all(not e["present"] for e in state["exhibits"])
    assert state["headline"] == []                 # no data files -> no headlines
    json.dumps(state)


def test_build_hub_marks_ledger_present_without_a_performance_headline(tmp_path):
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2026-02-17",
        "entries": [{"equity": 1.0}, {"equity": 1.085}],
    }))
    (tmp_path / "ledger.html").write_text("<html></html>")
    state = build_hub(tmp_path)
    # the ledger exhibit is linkable (appears in the Research appendix) …
    assert any(e["href"] == "ledger.html" and e["present"] for e in state["exhibits"])
    # … but its return never becomes a homepage headline — performance figures live in Research only.
    assert state["headline"] == []


def test_homepage_carries_no_performance_headline(tmp_path):
    # The homepage carries NO performance figure — not the model return, not drawdown. Even when a
    # ledger and tearsheet are present, `headline` stays empty; those figures live in Research only.
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2024-09-16",
        "entries": [{"equity": 1.0}, {"equity": 1.20}, {"equity": 1.02}, {"equity": 1.406}],
    }))
    ts_state = {"books": [{"name": "Equities & ETFs", "strategy": {"max_drawdown": 0.59},
                           "benchmark": {"max_drawdown": 0.58}, "oos": {"test": {"sharpe": 0.77}}}]}
    (tmp_path / "tearsheet.html").write_text(
        "x window.__STATE__ = " + json.dumps(ts_state) + ";\n y")
    state = build_hub(tmp_path)
    assert state["headline"] == []


def test_value_adds_three_distinct_dimensions_no_performance_numbers(tmp_path):
    # The homepage sells three DISTINCT dimensions of value — tax efficiency, implementation quality,
    # behavioral durability — and makes NO expected-return claim. Only the tax pillar carries a number
    # (dollars); no Sharpe, no ratio, no Core Alpha performance figure leaks onto the homepage.
    (tmp_path / "ledger.json").write_text(json.dumps({
        "inception": "2024-09-16",
        "entries": [{"equity": 1.0}, {"equity": 1.20}, {"equity": 1.02}, {"equity": 1.406}],
    }))
    led_state = {"header": {"sharpe": 1.35},
                 "benchmarks": [{"label": "VT", "sharpe": 1.21}, {"label": "VTI", "sharpe": 1.05}]}
    (tmp_path / "ledger.html").write_text(
        "x window.__STATE__ = " + json.dumps(led_state) + ";\n y")
    ts_state = {"books": [{"name": "Equities & ETFs", "strategy": {"max_drawdown": 0.59},
                           "benchmark": {"max_drawdown": 0.58},
                           "oos": {"test": {"sharpe": 0.65}, "train": {"sharpe": 0.65}}}]}
    (tmp_path / "tearsheet.html").write_text(
        "x window.__STATE__ = " + json.dumps(ts_state) + ";\n y")
    va = build_hub(tmp_path)["value_adds"]
    tags = [v["tag"] for v in va]
    assert len(va) == 3
    assert any("keep" in t.lower() for t in tags)      # 1 · taxes
    assert any("build" in t.lower() for t in tags)     # 2 · implementation / architecture
    assert any("stay" in t.lower() for t in tags)      # 3 · behavior
    assert not any("Alpha" in t for t in tags)         # product names never headline a pillar
    # Only ONE pillar carries a number, and it's dollars (families think in dollars).
    with_stat = [v for v in va if v.get("stat")]
    assert len(with_stat) == 1 and with_stat[0]["stat"].startswith("$")
    from drift.leakage import build_leakage
    leak = build_leakage()
    lo, hi = leak["before"]["keep_pct"] * 10_000, leak["after"]["keep_pct"] * 10_000
    assert with_stat[0]["stat"] == f"${lo:,.0f} → ${hi:,.0f}"
    # NO performance/Sharpe/ratio/Core-Alpha figure anywhere in the pillars — those live in Research.
    blob = " ".join(v.get("stat", "") + " " + v.get("stat_label", "") + " " + v.get("note", "") for v in va)
    for banned in ("Sharpe", "≈", "1.35", "0.65", "Core Alpha"):
        assert banned not in blob, f"{banned!r} must not appear on the homepage pillars"
    # Structural Alpha may be named once, small, in the tax pillar's note (honest implementation detail).
    assert "Structural Alpha" in blob


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
    # the research model portfolios — appendix (labeled "Research", no product names on the homepage)
    for h in ("ledger.html", "tearsheet.html", "equities.html", "equities_case_studies.html"):
        assert by_href[h]["appendix"] is True, f"{h} should be in the Research appendix"
    # the appendix blurbs are honest (hypothetical/model) and no longer lead with the "Core Alpha" name
    assert "hypothetical" in by_href["ledger.html"]["desc"].lower()
    assert "model portfolio" in by_href["equities.html"]["desc"].lower()
    assert "Core Alpha" not in by_href["ledger.html"]["desc"]


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



def test_hub_leads_with_coordination_not_taxes():
    # Coordination-first hero: the front door's one sentence is that Driftwood manages the whole
    # after-tax SYSTEM, taxes are just the proof.
    from drift.exhibit import HUB_TEMPLATE
    t = HUB_TEMPLATE.read_text()
    assert "after-tax system" in t                           # sells coordination of the whole system, not a bare tax pitch
    assert "coordinate" in t.lower()
    assert "The architecture" not in t                       # no machinery-led header


def test_capability_sequence_lives_on_the_practice_not_the_homepage():
    """The four-capability path (Diagnose -> Measure -> Coordinate -> Manage) must exist, in order,
    and be reachable, but it answers "how do you work" — a post-interest question. It moved to
    the-practice.html with the 2026 four-plate homepage (the homepage now runs Constraint -> Engine ->
    Register -> Ask, and Plate IV states the method in one sentence instead).

    This guard was previously pointed at hub.html. It is retargeted, NOT relaxed: the sequence and its
    deliberate order are still pinned, and the homepage is still barred from re-growing a second copy,
    so neither the path nor the reason it was moved can be lost silently."""
    from drift.exhibit import HUB_TEMPLATE
    practice = (WEB / "the-practice.html").read_text()
    # Read the page BODY, not the generated masthead. The nav is written by scripts/phase2_nav.py and
    # shares the page's vocabulary, so a menu label can collide with a capability name and silently
    # decide this test's answer: the 2026-08-01 IA restructure added "A Household, Coordinated",
    # whose "Coordinated" contains "Coordinate", which then matched ~8KB above the real sequence and
    # reported the order as drifted while the section itself was untouched.
    practice = re.sub(r'<nav class="dwnav dwnav--phase2".*?</nav>', "", practice, flags=re.S)
    caps = ("Diagnose", "Measure", "Coordinate", "Manage")
    for cap in caps:
        assert cap in practice, f"the {cap} capability should anchor the guided path on The Practice"
    # the order is the argument, not an accident
    positions = [practice.index(c) for c in caps]
    assert positions == sorted(positions), f"capability order drifted: {list(zip(caps, positions))}"
    assert 'id="capabilities"' in practice
    # and the homepage must not carry a duplicate of the sequence it delegated away
    hub = HUB_TEMPLATE.read_text()
    assert 'id="capabilities"' not in hub, "the capability sequence should live on The Practice only"


def test_hub_demotes_research_below_the_primary_path():
    from drift.exhibit import HUB_TEMPLATE
    t = HUB_TEMPLATE.read_text()
    # The homepage ends on a single conviction statement + one invitation (NOT a sitemap/resources
    # directory) — no internal product names, no perf figure on the homepage.
    assert 'class="sec close-conv' in t                      # a conviction close, not a card wall / link list
    assert 'class="res"' not in t                            # the old resources directory is gone
    assert "coordination decisions" in t                     # ends on the thesis, in words
    assert "Core Alpha Research" not in t
    assert 'class="rstat"' not in t                          # no performance figure line on the homepage
    assert "View the track record" not in t
    # the close is the last plate: nothing structural may follow it inside <main>
    assert t.index('class="sec close-conv') > t.index('id="governance"'), "the ask must follow the register"
