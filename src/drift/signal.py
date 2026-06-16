"""The time-series-momentum signal: how strongly, and which way, is this trending?

Pure functions, no I/O — the mirror of mrbet's `reversion.py`. The thesis is the
opposite one: rather than projecting a final total under a reversion-to-baseline
assumption, we measure how persistently an instrument has been drifting and bet
that the drift continues over the near horizon.

The core quantity is a **volatility-normalized trend score**. Over a lookback of
`L` bars the cumulative log return is

    R = log(P_t / P_{t-L})

Under a random-walk null, `R` has standard deviation `sigma * sqrt(L)` where
`sigma` is the per-bar return volatility. So

    score = R / (sigma * sqrt(L))

is a z-score: ~N(0, 1) when there is no trend, and large in magnitude when the
instrument has drifted far more than its own noise would explain. A Donchian
channel breakout provides an independent confirmation, exactly as mrbet required
an independent model edge on top of a raw line move.
"""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Sequence


def log_returns(closes: Sequence[float]) -> list[float]:
    """Per-bar log returns of a close series (length N -> N-1 returns)."""
    out: list[float] = []
    for prev, cur in zip(closes, closes[1:]):
        if prev > 0 and cur > 0:
            out.append(math.log(cur / prev))
        else:
            out.append(0.0)
    return out


def trailing_log_return(closes: Sequence[float], lookback: int) -> float:
    """Cumulative log return over the last `lookback` bars: log(P_t / P_{t-L})."""
    if lookback <= 0 or len(closes) <= lookback:
        return 0.0
    start, end = closes[-lookback - 1], closes[-1]
    if start <= 0 or end <= 0:
        return 0.0
    return math.log(end / start)


def realized_vol(closes: Sequence[float], window: int) -> float:
    """Per-bar return volatility: population stdev of the last `window` log returns."""
    rets = log_returns(closes)
    if window > 0:
        rets = rets[-window:]
    if len(rets) < 2:
        return 0.0
    return pstdev(rets)


def momentum_score(closes: Sequence[float], lookback: int, vol_window: int) -> float:
    """Volatility-normalized trend strength (a z-score under a random-walk null).

    Returns 0.0 when there isn't enough history or volatility is degenerate, so a
    flat / illiquid series never manufactures a signal.
    """
    if len(closes) <= lookback:
        return 0.0
    sigma = realized_vol(closes, vol_window)
    if sigma <= 0:
        return 0.0
    r = trailing_log_return(closes, lookback)
    return r / (sigma * math.sqrt(lookback))


def drift_per_bar(closes: Sequence[float], lookback: int) -> float:
    """Average per-bar log return over the lookback — the raw drift estimate."""
    if lookback <= 0:
        return 0.0
    return trailing_log_return(closes, lookback) / lookback


def donchian_breakout(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    channel: int,
) -> int:
    """Classic trend-following confirmation via an N-bar Donchian channel.

    Returns +1 when the latest close makes a new `channel`-bar high (upside
    breakout), -1 on a new `channel`-bar low, and 0 when the close sits inside the
    prior channel. The current bar is excluded from the channel so "new high"
    means *strictly above everything in the prior window*.
    """
    if channel <= 0 or len(closes) <= channel:
        return 0
    last = closes[-1]
    prior_high = max(highs[-channel - 1:-1])
    prior_low = min(lows[-channel - 1:-1])
    if last > prior_high:
        return 1
    if last < prior_low:
        return -1
    return 0


def trend_agrees(score: float, breakout: int) -> bool:
    """Whether the momentum score and the breakout point the same way.

    A breakout of 0 (inside the channel) never agrees — the conjunctive trigger
    treats "no fresh breakout" as a failed confirmation, just as mrbet treated a
    sub-threshold line move as a non-event.
    """
    if breakout == 0 or score == 0:
        return False
    return (score > 0) == (breakout > 0)
