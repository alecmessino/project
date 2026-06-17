"""Turnover controls: rebalance cadence, min-score gating, long-only default."""

from drift.config import CrossSectionSettings, Settings
from drift.cross_section import cross_backtest, rank_weights
from drift.feed.synthetic import SyntheticFeed


def _universe(drifts, n=400):
    out = {}
    for i, d in enumerate(drifts):
        out[f"S{i}"] = SyntheticFeed(instruments=(f"S{i}",), n_bars=n,
                                     regimes=[(n, d)], seed=80 + i).series(f"S{i}")
    return out


def _settings(**cs):
    s = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    for k, v in cs.items():
        setattr(s.cross_section, k, v)
    return s


def test_long_only_default_has_no_shorts():
    scores = {"a": 2.0, "b": 1.0, "c": -1.0, "d": -2.0}
    vols = {k: 0.2 for k in scores}
    w = rank_weights(scores, vols, CrossSectionSettings())   # default long_short=False
    assert all(v >= 0 for v in w.values())
    assert w["a"] > 0 and w["d"] == 0.0


def test_min_score_lightens_the_book_when_nothing_trends():
    # All scores below the threshold -> nothing held (book goes to cash).
    scores = {"a": 0.3, "b": 0.2, "c": 0.1}
    vols = {k: 0.2 for k in scores}
    cs = CrossSectionSettings(min_score=0.5, long_short=False)
    w = rank_weights(scores, vols, cs)
    assert all(v == 0.0 for v in w.values())
    # Raise one above the threshold -> only that one is held.
    scores["a"] = 1.2
    w = rank_weights(scores, vols, cs)
    assert w["a"] > 0 and w["b"] == 0.0 and w["c"] == 0.0


def test_rebalance_cadence_cuts_turnover():
    series = _universe([0.5, 0.2, -0.2, -0.5])
    daily = cross_backtest(series, _settings(rebalance_bars=1, min_score=0.0))
    monthly = cross_backtest(series, _settings(rebalance_bars=21, min_score=0.0))
    assert monthly.turnover < daily.turnover            # far fewer trades
    assert monthly.n_bars == daily.n_bars               # same horizon


def test_cross_backtest_still_runs_with_all_controls():
    res = cross_backtest(_universe([0.6, 0.1, -0.3, -0.6]),
                         _settings(rebalance_bars=21, min_score=0.5, long_short=False))
    assert res.equity_curve
    assert res.gross_return >= res.net_return           # cost never helps
