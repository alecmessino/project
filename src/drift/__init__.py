"""Driftwood — a time-series-momentum (trend-following) signal system.

Driftwood is the structural sibling of `mrbet`: it reuses the same harness shape
(an interchangeable data-feed protocol -> a streaming engine -> a conjunctive
trigger gate -> signals, plus a cost-aware backtest), but the model is the mirror
image. Where mean reversion bets that an extreme *reverts*, Driftwood bets that a
trend *persists* — it rides the price drift rather than fading it.

The name: ``drift`` is the deterministic trend term of a price process; driftwood
is carried by the current. The thesis is time-series momentum (Moskowitz, Ooi &
Pedersen 2012; Jegadeesh & Titman 1993): instruments that have trended recently,
volatility-adjusted, tend to keep trending over the near horizon.

This is a **signal** system. It flags trend opportunities and sizes them; it does
not place trades.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
