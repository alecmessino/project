import json

from drift.config import Settings
from drift.exhibit import build_dashboard_state, export_html, render_html
from drift.ledger import seed_ledger
from drift.feed.synthetic import SyntheticFeed


def _universe(drifts=(0.6, 0.0, -0.6)):
    series = {}
    for i, d in enumerate(drifts):
        feed = SyntheticFeed(instruments=(f"S{i}",), n_bars=250, regimes=[(250, d)], seed=4 + i)
        series[f"S{i}"] = feed.series(f"S{i}")
    return series


def _settings():
    return Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})


def _ledger_path(tmp_path):
    """A real seeded Model Portfolio ledger — the single source of truth the dashboard projects."""
    led = seed_ledger(_universe(), _settings(), sessions=80)
    p = tmp_path / "ledger.json"
    p.write_text(json.dumps(led))
    return p


def test_dashboard_state_is_a_projection_of_the_ledger(tmp_path):
    state = build_dashboard_state(_ledger_path(tmp_path), _settings())
    # the operational projection shape (holdings/watch/rebalance/performance) — not the old
    # series-recomputed shape.
    assert {"version", "date", "header", "holdings", "watch",
            "rebalance", "blotter", "performance"} <= set(state)
    # held + waiting == the ONE universe (no "8 vs 9" contradiction possible)
    assert len(state["holdings"]) + len(state["watch"]) == state["header"]["n_universe"]
    assert state["header"]["n_held"] == len(state["holdings"])


def test_holdings_carry_the_three_distinct_fields(tmp_path):
    state = build_dashboard_state(_ledger_path(tmp_path), _settings())
    rows = state["holdings"] + state["watch"]
    assert rows
    for r in rows:
        # Portfolio weight and Signal strength are DISTINCT named fields (never a bare "weight").
        assert "portfolio_weight" in r and "signal_strength" in r
        assert "weight" not in r
        assert r["status"] in {"Buy", "Sell", "Increase", "Reduce", "Hold", "Waiting"}
    # held rows carry weight; waiting rows are exactly weight 0
    assert all(r["portfolio_weight"] > 0 for r in state["holdings"])
    assert all(r["portfolio_weight"] == 0 and r["status"] == "Waiting" for r in state["watch"])


def test_performance_chart_is_dated(tmp_path):
    state = build_dashboard_state(_ledger_path(tmp_path), _settings())
    perf = state["performance"]
    assert len(perf["dates"]) == len(perf["equity"]) and perf["dates"]  # a dated x-axis exists


def test_dashboard_state_is_json_serializable(tmp_path):
    json.dumps(build_dashboard_state(_ledger_path(tmp_path), _settings()))  # must not raise


def test_build_dashboard_state_is_none_without_a_ledger(tmp_path):
    assert build_dashboard_state(tmp_path / "absent.json", _settings()) is None


def test_latest_rebalance_blotter_diffs_a_rotation():
    from dataclasses import replace
    from datetime import date, timedelta
    from drift.exhibit import latest_rebalance_blotter
    # Six names (> min_universe; quantile 0.5 -> top 3 held). Three lead then fade, three lag then
    # surge, so the held set rotates at a rebalance: the surging names enter, the fading ones exit —
    # exactly what the blotter must surface. (Real ISO dates so the date-ordered walk isn't scrambled.)
    start = date(2020, 1, 1)
    series = {}
    plan = [(f"LEAD{i}", [(130, 0.7), (130, -0.7)], 20 + i) for i in range(3)] + \
           [(f"LAG{i}", [(130, -0.7), (130, 0.7)], 30 + i) for i in range(3)]
    for name, regs, seed in plan:
        bars = SyntheticFeed(instruments=(name,), n_bars=260, regimes=regs, seed=seed).series(name)
        series[name] = [replace(b, asof=(start + timedelta(days=k)).isoformat()) for k, b in enumerate(bars)]
    bl = latest_rebalance_blotter(series, _settings())
    assert bl is not None and bl["trades"]
    assert {"date", "prev_date", "since_return", "n_held", "trades"} <= set(bl)
    for t in bl["trades"]:
        assert t["action"] in {"NEW", "ADD", "TRIM", "EXIT"}
        assert set(t) == {"instrument", "action", "prev_weight", "weight", "delta"}
    # an entry/exit pair has a real weight move (not an immaterial wiggle)
    assert any(t["action"] in {"NEW", "EXIT"} for t in bl["trades"])
    assert all(abs(t["delta"]) > 0 for t in bl["trades"])


def test_blotter_is_none_for_too_short_history():
    from drift.exhibit import latest_rebalance_blotter
    series = {f"S{i}": SyntheticFeed(instruments=(f"S{i}",), n_bars=1, regimes=[(1, 0.0)],
                                     seed=i).series(f"S{i}") for i in range(3)}
    assert latest_rebalance_blotter(series, _settings()) is None


def test_render_html_embeds_state_and_replaces_placeholder(tmp_path):
    state = build_dashboard_state(_ledger_path(tmp_path), _settings())
    html = render_html(state)
    assert "/*__STATE__*/null/*__END__*/" not in html  # placeholder consumed
    assert "Driftwood" in html or "Drift" in html
    assert '"holdings"' in html                         # state inlined


def test_export_html_writes_file(tmp_path):
    out = tmp_path / "sub" / "drift.html"
    path = export_html(_ledger_path(tmp_path), _settings(), out)
    assert path.exists()
    assert path.read_text().lstrip().startswith("<!DOCTYPE html>")


def test_spark_downsamples_long_curves():
    from drift.exhibit import _spark
    assert len(_spark(list(range(1000)), n=90)) == 90
    assert _spark([1, 2, 3], n=90) == [1, 2, 3]
