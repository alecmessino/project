import json

from drift.config import Settings
from drift.exhibit import build_state, export_html, render_html
from drift.feed.synthetic import SyntheticFeed
from drift.feed.base import collect_series


def _universe(drifts=(0.6, 0.0, -0.6)):
    series = {}
    for i, d in enumerate(drifts):
        feed = SyntheticFeed(instruments=(f"S{i}",), n_bars=250, regimes=[(250, d)], seed=4 + i)
        series[f"S{i}"] = feed.series(f"S{i}")
    return series


def _settings():
    return Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})


def test_build_state_shape():
    state = build_state(_universe(), _settings(), source="synthetic")
    assert set(state) == {"header", "instruments", "rankings", "cross_backtest"}
    assert state["header"]["n_instruments"] == 3
    assert len(state["instruments"]) == 3
    assert len(state["rankings"]) == 3
    assert state["cross_backtest"]["equity"]  # populated


def test_build_state_is_json_serializable():
    state = build_state(_universe(), _settings())
    json.dumps(state)  # must not raise


def test_instrument_entry_has_backtest_and_signal_fields():
    state = build_state(_universe(), _settings())
    it = state["instruments"][0]
    for key in ("instrument", "score", "side", "weight", "flagged", "backtest"):
        assert key in it
    assert "equity" in it["backtest"] and "sharpe" in it["backtest"]


def test_render_html_embeds_state_and_replaces_placeholder():
    state = build_state(_universe(), _settings(), source="synthetic")
    html = render_html(state)
    assert "/*__STATE__*/null/*__END__*/" not in html  # placeholder consumed
    assert "Driftwood" in html or "Drift" in html
    assert '"cross_backtest"' in html                   # state inlined


def test_export_html_writes_file(tmp_path):
    out = tmp_path / "sub" / "drift.html"
    path = export_html(_universe(), _settings(), out, source="synthetic")
    assert path.exists()
    assert path.read_text().lstrip().startswith("<!DOCTYPE html>")


def test_spark_downsamples_long_curves():
    from drift.exhibit import _spark
    assert len(_spark(list(range(1000)), n=90)) == 90
    assert _spark([1, 2, 3], n=90) == [1, 2, 3]
