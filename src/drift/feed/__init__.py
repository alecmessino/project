"""Price feeds: interchangeable data sources behind the `PriceFeed` protocol.

Offline: `ReplayFeed` (CSV / in-memory) and `SyntheticFeed` (seeded GBM).
Live: `YahooFeed` (equities/ETFs, keyless) and `PolygonFeed` (equities, keyed).
"""

from __future__ import annotations

from .base import PriceFeed, Snapshot, get_feed
from .replay import ReplayFeed
from .synthetic import SyntheticFeed

__all__ = [
    "PriceFeed",
    "Snapshot",
    "get_feed",
    "ReplayFeed",
    "SyntheticFeed",
]
