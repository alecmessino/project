"""Odds conversions and the probability / EV / Kelly math.

All functions are pure and side-effect free so they're trivially unit-testable.
"""

from __future__ import annotations

import math


def american_to_decimal(odds: int) -> float:
    """Convert American odds to decimal (total return per $1 incl. stake)."""
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if odds > 0:
        return 1.0 + odds / 100.0
    return 1.0 + 100.0 / abs(odds)


def american_to_profit(odds: int) -> float:
    """Net profit per $1 staked (decimal odds minus the returned stake)."""
    return american_to_decimal(odds) - 1.0


def american_to_implied_prob(odds: int) -> float:
    """Vig-included implied probability from American odds."""
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def prob_over(line: float, mean: float, sigma: float) -> float:
    """P(final > line) under final ~ Normal(mean, sigma).

    For a half-point line there is no push, so P(under) = 1 - P(over). For an
    integer line we split out the push mass and return only the strict-over mass;
    callers that need the push probability can use `push_prob`.
    """
    if sigma <= 0:
        return 1.0 if mean > line else 0.0
    z = (line - mean) / sigma
    return 1.0 - _norm_cdf(z)


def prob_under(line: float, mean: float, sigma: float) -> float:
    """P(final < line) under final ~ Normal(mean, sigma) (strict-under mass)."""
    if sigma <= 0:
        return 1.0 if mean < line else 0.0
    z = (line - mean) / sigma
    return _norm_cdf(z)


def push_prob(line: float, mean: float, sigma: float) -> float:
    """Approximate probability of an exact push at an integer line.

    Totals are discrete; we approximate the mass on the integer with the normal
    density over a unit-wide bin centered on the line. Half-point lines return 0.
    """
    if abs(line - round(line)) > 1e-9:
        return 0.0
    if sigma <= 0:
        return 0.0
    hi = _norm_cdf((line + 0.5 - mean) / sigma)
    lo = _norm_cdf((line - 0.5 - mean) / sigma)
    return max(0.0, hi - lo)


def expected_value(win_prob: float, odds: int, push_prob_: float = 0.0) -> float:
    """EV per $1 staked. Push refunds the stake (EV contribution 0)."""
    profit = american_to_profit(odds)
    lose_prob = max(0.0, 1.0 - win_prob - push_prob_)
    return win_prob * profit - lose_prob * 1.0


def kelly_fraction(win_prob: float, odds: int, push_prob_: float = 0.0) -> float:
    """Full-Kelly fraction of bankroll. Clamped to [0, 1]; 0 if no edge.

    With push probability p_push, an effective two-outcome Kelly is used by
    renormalizing win/lose over the non-push mass.
    """
    b = american_to_profit(odds)
    if b <= 0:
        return 0.0
    non_push = 1.0 - push_prob_
    if non_push <= 0:
        return 0.0
    p = win_prob / non_push
    q = 1.0 - p
    f = (b * p - q) / b
    return max(0.0, min(1.0, f))


def _norm_cdf(z: float) -> float:
    """Standard normal CDF via erf (avoids a hard scipy dependency here)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
