import pytest

from drift.config import CrossSectionSettings, Settings
from drift.cross_section import _demean_within_groups, rank_weights, cross_backtest
from drift.feed.synthetic import SyntheticFeed


def test_demean_removes_group_mean():
    scores = {"a": 3.0, "b": 1.0, "c": -1.0, "d": -3.0}
    groups = {"a": "G1", "b": "G1", "c": "G2", "d": "G2"}
    out = _demean_within_groups(scores, groups)
    assert out["a"] == pytest.approx(1.0)   # 3 - mean(3,1)=2
    assert out["b"] == pytest.approx(-1.0)
    assert out["c"] == pytest.approx(1.0)   # -1 - mean(-1,-3)=-2
    assert out["d"] == pytest.approx(-1.0)


def test_region_neutral_changes_the_book():
    # Group G1 all strongly positive, G2 all weakly positive. Raw ranking longs
    # G1 entirely; region-neutral instead ranks WITHIN each group.
    scores = {"a": 5.0, "b": 4.0, "c": 0.5, "d": 0.1}
    vols = {k: 0.2 for k in scores}
    groups = {"a": "G1", "b": "G1", "c": "G2", "d": "G2"}
    cs_raw = CrossSectionSettings(quantile=0.25, neutralize="none")
    cs_neu = CrossSectionSettings(quantile=0.25, neutralize="region")
    raw = rank_weights(scores, vols, cs_raw)
    neu = rank_weights(scores, vols, cs_neu, groups)
    assert raw["a"] > 0 and raw["d"] < 0          # raw: long best abs, short worst abs
    # neutral: within-group leaders long, laggards short -> a (G1 leader) long, b short
    assert neu["a"] > 0 and neu["b"] < 0


def test_neutralize_ignored_without_groups():
    scores = {"a": 2.0, "b": 1.0, "c": -2.0}
    vols = {k: 0.2 for k in scores}
    cs = CrossSectionSettings(quantile=0.34, neutralize="region")
    # No groups passed -> behaves like raw ranking (no crash).
    w = rank_weights(scores, vols, cs, None)
    assert w["a"] > 0 and w["c"] < 0


def test_cross_backtest_runs_region_neutral():
    settings = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    settings.cross_section.neutralize = "region"
    # Use real tickers so the region map applies.
    syms = ["SPY", "IWM", "EFA", "EFV", "EEM", "DGS"]
    series = {}
    for i, s in enumerate(syms):
        series[s] = SyntheticFeed(instruments=(s,), n_bars=250,
                                  regimes=[(250, 0.4 - 0.1 * i)], seed=60 + i).series(s)
    res = cross_backtest(series, settings)
    assert res.n_bars == 250
    assert res.equity_curve
