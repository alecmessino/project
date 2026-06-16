from drift.config import CrossSectionSettings, Settings
from drift.cross_section import cross_backtest, rank_snapshot, rank_weights
from drift.feed.synthetic import SyntheticFeed
from drift.feed.base import collect_series


def _cs(**kw):
    return CrossSectionSettings(**kw)


def test_rank_weights_longs_top_shorts_bottom():
    scores = {"A": 2.0, "B": 1.0, "C": 0.0, "D": -1.0, "E": -2.0}
    vols = {k: 0.2 for k in scores}
    w = rank_weights(scores, vols, _cs(quantile=0.2, weighting="equal"))
    assert w["A"] > 0 and w["E"] < 0      # best long, worst short
    assert w["C"] == 0.0                  # middle untouched


def test_rank_weights_dollar_neutral():
    scores = {"A": 3.0, "B": 1.0, "C": -1.0, "D": -3.0}
    vols = {k: 0.2 for k in scores}
    w = rank_weights(scores, vols, _cs(quantile=0.25, long_short=True, weighting="equal"))
    assert abs(sum(w.values())) < 1e-9    # long budget == short budget


def test_rank_weights_long_only():
    scores = {"A": 3.0, "B": 1.0, "C": -1.0, "D": -3.0}
    vols = {k: 0.2 for k in scores}
    w = rank_weights(scores, vols, _cs(quantile=0.25, long_short=False, weighting="equal"))
    assert all(v >= 0 for v in w.values())
    assert sum(w.values()) > 0


def test_rank_weights_respects_min_universe():
    scores = {"A": 2.0, "B": -2.0}
    vols = {k: 0.2 for k in scores}
    w = rank_weights(scores, vols, _cs(min_universe=3))
    assert all(v == 0.0 for v in w.values())


def test_rank_weights_caps_per_name():
    scores = {"A": 5.0, "B": 1.0, "C": -1.0, "D": -5.0}
    vols = {"A": 0.01, "B": 0.5, "C": 0.5, "D": 0.5}  # A tiny vol -> would dominate inv_vol
    w = rank_weights(scores, vols, _cs(quantile=0.25, weighting="inv_vol", max_weight=0.3))
    assert all(abs(v) <= 0.3 + 1e-9 for v in w.values())


def test_inv_vol_gives_quieter_name_more_weight():
    scores = {"A": 2.0, "B": 2.1, "C": -2.0, "D": -2.1}
    vols = {"A": 0.10, "B": 0.40, "C": 0.2, "D": 0.2}  # A and B both long
    w = rank_weights(scores, vols, _cs(quantile=0.5, long_short=True, weighting="inv_vol"))
    assert w["A"] > w["B"] > 0            # quieter A earns more notional


def _universe(seed_drifts):
    """Build a universe where each instrument trends at a different annual drift."""
    series = {}
    for i, drift in enumerate(seed_drifts):
        feed = SyntheticFeed(instruments=(f"S{i}",), n_bars=300,
                             regimes=[(300, drift)], seed=10 + i)
        series[f"S{i}"] = feed.series(f"S{i}")
    return series


def test_cross_backtest_runs_and_reports():
    settings = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    series = _universe([0.6, 0.2, -0.2, -0.6])
    res = cross_backtest(series, settings)
    assert res.n_bars == 300
    assert len(res.instruments) == 4
    assert res.gross_return >= res.net_return   # cost never helps
    assert res.equity_curve


def test_rank_snapshot_orders_by_score():
    settings = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    series = _universe([0.8, 0.0, -0.8])
    rows = rank_snapshot(series, settings)
    assert [r.instrument for r in rows] == sorted(
        [r.instrument for r in rows], key=lambda x: -dict((r.instrument, r.score) for r in rows)[x]
    )
    assert rows[0].score >= rows[-1].score


def test_collect_series_uniform_across_feeds():
    feed = SyntheticFeed(instruments=("X", "Y"), n_bars=40)
    series = collect_series(feed)
    assert set(series) == {"X", "Y"}
    assert all(len(v) == 40 for v in series.values())
