import math

import pytest

from drift import signal as sig


def _trend(n=120, step=0.01, start=100.0):
    """An up-trend with mild noise so realized vol is non-degenerate."""
    closes = [start]
    for i in range(n):
        wobble = 0.002 * (1 if i % 2 else -1)  # alternating noise -> non-zero vol
        closes.append(closes[-1] * math.exp(step + wobble))
    return closes


def test_trailing_log_return_matches_definition():
    # A perfectly smooth path: cumulative log-return is exactly lookback * step.
    closes = [100.0]
    for _ in range(60):
        closes.append(closes[-1] * math.exp(0.01))
    r = sig.trailing_log_return(closes, lookback=60)
    assert r == pytest.approx(60 * 0.01, abs=1e-9)


def test_momentum_score_positive_on_uptrend_negative_on_downtrend():
    up = _trend(step=0.01)
    down = list(reversed(up))  # mirror -> a clean down-trend
    assert sig.momentum_score(up, lookback=60, vol_window=30) > 0
    assert sig.momentum_score(down, lookback=60, vol_window=30) < 0


def test_momentum_score_zero_without_history_or_vol():
    flat = [100.0] * 80  # zero volatility -> undefined trend -> 0
    assert sig.momentum_score(flat, lookback=60, vol_window=30) == 0.0
    assert sig.momentum_score([100.0, 101.0], lookback=60, vol_window=30) == 0.0


def test_breakout_detects_new_high_and_low():
    closes = list(range(1, 51))  # strictly increasing -> every bar a new high
    highs = [c + 0.1 for c in closes]
    lows = [c - 0.1 for c in closes]
    assert sig.donchian_breakout(highs, lows, [float(c) for c in closes], channel=40) == 1

    desc = list(reversed([float(c) for c in closes]))
    assert sig.donchian_breakout(list(reversed(highs)), list(reversed(lows)), desc, channel=40) == -1


def test_breakout_zero_inside_channel():
    # Oscillating series whose last close is mid-range -> no fresh breakout.
    closes = [100.0 + (1 if i % 2 else -1) for i in range(60)]
    assert sig.donchian_breakout(closes, closes, closes, channel=40) == 0


def test_information_discreteness_separates_continuous_from_discrete():
    # A smoothly rising path (every bar up) is maximally CONTINUOUS -> ID = +1 * (0 - 1) = -1.
    smooth = [100.0 * (1.01 ** i) for i in range(30)]
    id_smooth = sig.information_discreteness(smooth, lookback=20)
    assert id_smooth == pytest.approx(-1.0, abs=1e-9)
    # Same net rise but driven by one big jump then many small down bars is DISCRETE -> ID > 0.
    jumpy = [100.0] * 15 + [130.0] + [130.0 * (0.999 ** i) for i in range(1, 15)]
    id_jumpy = sig.information_discreteness(jumpy, lookback=20)
    assert id_jumpy > 0.0
    assert id_jumpy > id_smooth                       # discrete scores strictly higher than continuous
    # Insufficient history -> 0.0 (never manufactures a value).
    assert sig.information_discreteness([1.0, 2.0, 3.0], lookback=20) == 0.0


def test_trend_agrees_requires_same_sign_and_real_breakout():
    assert sig.trend_agrees(1.5, 1) is True
    assert sig.trend_agrees(-1.5, -1) is True
    assert sig.trend_agrees(1.5, -1) is False
    assert sig.trend_agrees(1.5, 0) is False
    assert sig.trend_agrees(0.0, 1) is False
