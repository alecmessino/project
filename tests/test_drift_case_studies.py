import json

from drift import case_studies as cs
from drift.config import Settings
from drift.exhibit import render_report
from drift.feed.synthetic import SyntheticFeed


def _settings():
    return Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})


def _universe(drifts=(0.6, 0.2, -0.2, -0.6)):
    series = {}
    for i, d in enumerate(drifts):
        feed = SyntheticFeed(instruments=(f"S{i}",), n_bars=320, regimes=[(320, d)], seed=30 + i)
        series[f"S{i}"] = feed.series(f"S{i}")
    return series


def test_each_study_has_required_shape():
    s = _settings()
    series = _universe()
    for study in (cs.study_timeseries(series, s), cs.study_cross(series, s),
                  cs.study_lookback_sensitivity(series, s),
                  cs.study_cost_sensitivity(series, s), cs.study_trend_vs_noise(s)):
        assert study["name"] and study["description"]
        assert isinstance(study["metrics"], list) and study["metrics"]
        for m in study["metrics"]:
            assert set(m) == {"label", "value", "tone"}


def test_trend_vs_noise_control_separates_signal_from_null():
    # Identical params: the genuine trend should beat the driftless walk.
    study = cs.study_trend_vs_noise(_settings())
    vals = {m["label"]: m["value"] for m in study["metrics"]}
    trend = float(vals["Trend net"].rstrip("%"))
    walk = float(vals["Walk net"].rstrip("%"))
    assert trend > walk


def test_cost_sensitivity_table_decays_with_cost():
    study = cs.study_cost_sensitivity(_universe(), _settings(), costs=(1.0, 50.0))
    rows = study["table"]["rows"]
    cheap = float(rows[0][1].rstrip("%"))
    dear = float(rows[1][1].rstrip("%"))
    assert dear <= cheap  # higher cost never improves the net result


def test_build_report_runs_without_live_data():
    report = cs.build_report(_universe(), _settings(), source="synthetic")
    assert report["header"]["n_instruments"] == 4
    assert len(report["studies"]) == 5
    json.dumps(report)  # serializable


def test_build_report_synthetic_only_when_universe_empty():
    report = cs.build_report({}, _settings())
    # No live universe -> only the synthetic control study runs.
    assert [st["name"] for st in report["studies"]] == ["Trend vs. random walk (synthetic control)"]


def test_render_report_embeds_state():
    report = cs.build_report(_universe(), _settings(), source="synthetic")
    html = render_report(report)
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert '"studies"' in html
    assert html.lstrip().startswith("<!DOCTYPE html>")


def test_equity_universe_polygon_skips_when_no_key(monkeypatch):
    # Polygon source with no POLYGON_API_KEY: each fetch raises and is skipped
    # (no network — the key check happens before any HTTP call).
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    assert cs.equity_universe(["SPY", "QQQ"], source="polygon") == {}


def test_build_report_labels_are_asset_agnostic():
    report = cs.build_report(_universe(), _settings(), source="polygon")
    names = [st["name"] for st in report["studies"]]
    assert "Trend-following (time-series)" in names
    assert "Relative-strength (cross-sectional)" in names
    assert not any("Crypto" in n for n in names)  # works for equities too


def test_equal_weight_equity_aggregates():
    eq = cs._equal_weight_equity([[1.0, 1.1, 1.21], [1.0, 0.9, 0.81]])
    assert len(eq) == 3
    assert eq[0] == 1.0
