"""Price feeds: interchangeable data sources behind the `PriceFeed` protocol."""

from __future__ import annotations

from .base import PriceFeed, Snapshot, get_feed

__all__ = ["PriceFeed", "Snapshot", "get_feed"]
