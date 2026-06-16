"""Feed protocol shared by all price sources.

The trading-domain analog of mrbet's `OddsProvider`. A feed yields `Snapshot`s —
one timestamp's bar for each tracked instrument — and the engine treats every
feed identically, so a replay of recorded history, a synthetic generator, and a
live exchange/broker API are fully interchangeable. Add a new source here; never
special-case it in the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Protocol, runtime_checkable

from ..models import Bar


@dataclass
class Snapshot:
    """One timestamp: the latest bar for each instrument observed at `asof`.

    A snapshot need not carry every instrument every time (a feed may stream them
    as they print); the engine maintains per-instrument history across snapshots.
    """

    asof: str
    bars: dict[str, Bar] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


@runtime_checkable
class PriceFeed(Protocol):
    """Anything that can stream snapshots for one or more instruments."""

    def snapshots(self) -> Iterator[Snapshot]:
        """Yield snapshots in time order. Live feeds block/sleep between bars;
        replay/synthetic feeds yield their sequence and stop."""
        ...


def collect_series(feed: "PriceFeed") -> dict[str, list[Bar]]:
    """Drain a feed once into per-instrument, time-ordered bar series.

    Works uniformly across every feed (replay, synthetic, live) because it only
    relies on the `snapshots()` stream — the cross-sectional backtest and the
    dashboard both build their universe through this.
    """
    series: dict[str, list[Bar]] = {}
    for snap in feed.snapshots():
        for inst, bar in snap.bars.items():
            series.setdefault(inst, []).append(bar)
    return series


def get_feed(name: str, **kwargs) -> PriceFeed:
    """Factory: build a feed by name. Imported lazily so the synthetic/replay
    paths never pull in any network code."""
    name = name.lower()
    if name in ("replay", "csv", "manual"):
        from .replay import ReplayFeed

        return ReplayFeed(**kwargs)
    if name in ("synthetic", "sim", "demo"):
        from .synthetic import SyntheticFeed

        return SyntheticFeed(**kwargs)
    if name in ("coinbase", "crypto"):
        from .coinbase import CoinbaseFeed

        return CoinbaseFeed(**kwargs)
    if name in ("yahoo", "yf", "equity", "equities", "stocks"):
        from .yahoo import YahooFeed

        return YahooFeed(**kwargs)
    if name in ("polygon",):
        from .polygon import PolygonFeed

        return PolygonFeed(**kwargs)
    raise ValueError(f"unknown feed: {name!r}")
