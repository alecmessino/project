"""Trend throttle + ragged full-history cross-sectional book."""

from dataclasses import replace
from datetime import date, timedelta

from drift.config import CrossSectionSettings, Settings
from drift.cross_section import cross_book_streams, rank_weights
from drift.feed.synthetic import SyntheticFeed


def test_throttle_scales_exposure_by_positive_breadth():
    vols = {k: 0.2 for k in "abcd"}
    cs = CrossSectionSettings(quantile=0.5, long_short=False, min_score=-99,
                              trend_throttle=True, exposure_floor=0.0)
    # All positive -> breadth 1.0 -> full exposure.
    full = rank_weights({"a": 2.0, "b": 1.5, "c": 1.0, "d": 0.5}, vols, cs)
    # Half positive -> breadth 0.5 -> ~half exposure on the same selection.
    half = rank_weights({"a": 2.0, "b": 1.5, "c": -1.0, "d": -1.5}, vols, cs)
    assert sum(abs(v) for v in full.values()) > sum(abs(v) for v in half.values())
    assert abs(sum(abs(v) for v in half.values()) - 0.5 * sum(abs(v) for v in full.values())) < 1e-6


def test_throttle_respects_exposure_floor():
    vols = {k: 0.2 for k in "abcd"}
    cs = CrossSectionSettings(quantile=0.5, long_short=False, min_score=-99,
                              trend_throttle=True, exposure_floor=0.25)
    # All negative -> breadth 0 -> exposure floored at 0.25 (not zero).
    w = rank_weights({"a": -1.0, "b": -2.0, "c": -3.0, "d": -4.0}, vols, cs)
    gross = sum(abs(v) for v in w.values())
    assert abs(gross - 0.25) < 1e-6


def test_throttle_off_by_default():
    vols = {k: 0.2 for k in "abc"}
    w = rank_weights({"a": 1.0, "b": -0.5, "c": -2.0}, vols, CrossSectionSettings(min_score=-99))
    assert abs(sum(abs(v) for v in w.values()) - 1.0) < 1e-6   # fully invested, no throttle


def _ragged_universe():
    # Two long series + one that starts much later -> exercises ragged handling.
    start = date(2015, 1, 1)
    out = {}
    for i, (n, d) in enumerate([(500, 0.5), (500, -0.3), (200, 0.4)]):
        bars = SyntheticFeed(instruments=(f"S{i}",), n_bars=n, regimes=[(n, d)], seed=70 + i).series(f"S{i}")
        # the short one (200) starts later
        offset = 0 if n == 500 else 300
        out[f"S{i}"] = [replace(b, asof=(start + timedelta(days=offset + k)).isoformat())
                        for k, b in enumerate(bars)]
    return out


def test_cross_book_streams_spans_full_ragged_history():
    s = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    s.cross_section.rebalance_bars = 5
    s.cross_section.min_score = -99
    dated = cross_book_streams(_ragged_universe(), s)
    assert dated
    # spans the earliest series' dates, not truncated to the youngest (which starts +300d)
    assert dated[0][0] < "2015-10-01"
    assert all(isinstance(d, str) for d, _ in dated)
