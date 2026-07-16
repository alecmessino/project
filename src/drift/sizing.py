"""Position sizing and the expected-edge / Kelly math.

Pure, side-effect-free functions, the trading-domain analog of mrbet's
`probability.py`. Betting priced a binary over/under at fixed odds; a trend
position has a *continuous* payoff, so the over/under-CDF machinery is replaced
by two ideas:

* **Volatility targeting**, scale the position so each holding contributes a
  roughly constant volatility budget, the standard managed-futures sizing.
* **Continuous Kelly**, the growth-optimal leverage for a continuous return is
  ``f* = mu / sigma^2`` (mean over variance). We apply a fractional-Kelly scaler
  and a hard leverage cap, mirroring mrbet's fractional, bankroll-capped Kelly.

Transaction cost is first-class here (it was the headline risk in the feasibility
note): an edge only counts if it survives the round-trip cost over the assumed
holding horizon.
"""

from __future__ import annotations

import math


def annualize_vol(per_bar_vol: float, bars_per_year: float) -> float:
    """Scale a per-bar return stdev to an annualized volatility."""
    if per_bar_vol <= 0 or bars_per_year <= 0:
        return 0.0
    return per_bar_vol * math.sqrt(bars_per_year)


def vol_target_weight(
    side_sign: int,
    ann_vol: float,
    target_vol: float,
    max_leverage: float,
) -> float:
    """Signed portfolio weight that targets `target_vol` annualized.

    weight = side_sign * clamp(target_vol / ann_vol, 0, max_leverage)

    A quieter instrument earns more notional to hit the same risk budget; a wild
    one is sized down. Degenerate vol -> no position (avoids divide-by-zero
    leverage blow-ups).
    """
    if side_sign == 0 or ann_vol <= 0 or target_vol <= 0:
        return 0.0
    lev = min(target_vol / ann_vol, max_leverage)
    return side_sign * max(0.0, lev)


def kelly_leverage(
    expected_return: float,
    variance: float,
    max_leverage: float,
) -> float:
    """Growth-optimal leverage f* = expected_return / variance, clamped to [0, cap].

    Returns 0 when there is no positive expected return (no edge -> no bet),
    matching mrbet's "0 if no edge" Kelly.
    """
    if expected_return <= 0 or variance <= 0:
        return 0.0
    f = expected_return / variance
    return max(0.0, min(f, max_leverage))


def expected_edge_per_bar(drift_per_bar: float, continuation: float) -> float:
    """Expected next-bar return of a position that follows the trend.

    Momentum's predictive content is the assumption that a fraction of the recent
    drift *continues*: ``E[r_next] ~= continuation * drift_per_bar``. The
    `continuation` coefficient is the trend-following analog of mrbet's reversion
    weight beta, and, like beta, it ships as an UNVALIDATED default that must be
    fit against logged data before the expected-edge numbers mean anything.
    """
    return continuation * drift_per_bar


def edge_net_of_cost(
    expected_edge: float,
    hold_bars: int,
    cost_bps_per_side: float,
) -> float:
    """Expected edge accrued over the hold horizon, net of round-trip cost.

    edge_after_cost = expected_edge * hold_bars - 2 * (cost_bps / 1e4)

    The position is assumed entered and exited once over `hold_bars` bars, so it
    pays the per-side cost twice. This is the gate that kills paper alpha that
    only exists gross of trading frictions.
    """
    gross = expected_edge * max(0, hold_bars)
    round_trip = 2.0 * (cost_bps_per_side / 1e4)
    return gross - round_trip
