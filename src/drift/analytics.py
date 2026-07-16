"""Pure performance/risk analytics: tearsheet metrics from a return stream.

All functions are side-effect free and operate on plain lists, so they unit-test
trivially and can be reused by the tearsheet, the ledger, and any future report.
A "return stream" is a list of (asof, simple_return) pairs; `asof` is an ISO
string whose first four characters are the year (used to bucket by calendar year).
"""

from __future__ import annotations

import math
from typing import Sequence


def equity_from_returns(returns: Sequence[float], start: float = 1.0) -> list[float]:
    eq, out = start, []
    for r in returns:
        eq *= (1.0 + r)
        out.append(eq)
    return out


def max_drawdown(equity: Sequence[float]) -> float:
    """Largest peak-to-trough decline as a positive fraction."""
    peak, mdd = -math.inf, 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd


def ann_vol(returns: Sequence[float], bars_per_year: float) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    return math.sqrt(var) * math.sqrt(bars_per_year)


def sharpe(returns: Sequence[float], bars_per_year: float) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(var)
    return (mean / std * math.sqrt(bars_per_year)) if std > 0 else 0.0


def sortino(returns: Sequence[float], bars_per_year: float) -> float:
    """Like Sharpe but penalizing only downside deviation."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    downside = [r for r in returns if r < 0]
    if not downside:
        return float("inf") if mean > 0 else 0.0
    dd = math.sqrt(sum(r * r for r in downside) / len(returns))
    return (mean / dd * math.sqrt(bars_per_year)) if dd > 0 else 0.0


def cagr(equity: Sequence[float], bars_per_year: float) -> float:
    """Compound annual growth rate implied by an equity curve."""
    if len(equity) < 2 or equity[0] <= 0 or equity[-1] <= 0:
        return 0.0
    years = len(equity) / bars_per_year
    if years <= 0:
        return 0.0
    return (equity[-1] / equity[0]) ** (1.0 / years) - 1.0


def calmar(cagr_: float, max_dd: float) -> float:
    """CAGR per unit of max drawdown, pain-adjusted return."""
    return (cagr_ / max_dd) if max_dd > 0 else 0.0


def hit_rate(returns: Sequence[float]) -> float:
    active = [r for r in returns if abs(r) > 1e-12]
    if not active:
        return 0.0
    return sum(1 for r in active if r > 0) / len(active)


def returns_by_year(dated: Sequence[tuple[str, float]]) -> list[tuple[str, float]]:
    """Compound a dated return stream into per-calendar-year total returns."""
    buckets: dict[str, float] = {}
    for asof, r in dated:
        y = asof[:4]
        buckets[y] = (buckets.get(y, 1.0)) * (1.0 + r)
    return [(y, buckets[y] - 1.0) for y in sorted(buckets)]


def summary(dated: Sequence[tuple[str, float]], bars_per_year: float) -> dict:
    """Full tearsheet metric block for one return stream."""
    rets = [r for _, r in dated]
    eq = equity_from_returns(rets)
    mdd = max_drawdown(eq)
    cg = cagr(eq, bars_per_year)
    sortino_ = sortino(rets, bars_per_year)
    return {
        "total_return": (eq[-1] - 1.0) if eq else 0.0,
        "cagr": cg,
        "sharpe": sharpe(rets, bars_per_year),
        "sortino": (round(sortino_, 2) if sortino_ != float("inf") else None),
        "calmar": calmar(cg, mdd),
        "max_drawdown": mdd,
        "ann_vol": ann_vol(rets, bars_per_year),
        "hit_rate": hit_rate(rets),
        "n_bars": len(rets),
    }
