"""Live crypto feed: Coinbase Exchange public candles (no API key required).

Endpoint: GET /products/{product}/candles?granularity={seconds}
Each row is [time, low, high, open, close, volume], newest-first, up to 300 bars.

The HTTP `session` is injectable so the parser and snapshot wiring are unit-tested
without any network call; pass nothing and a `requests.Session` is created lazily.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator, Optional, Sequence

from ..models import Bar
from ._retry import with_retries
from .base import Snapshot
from .replay import ReplayFeed

# Granularity (seconds) -> bars per year, for the engine's annualization.
GRANULARITY_BARS_PER_YEAR = {
    60: 525_600, 300: 105_120, 900: 35_040, 3600: 8_760, 21_600: 1_460, 86_400: 365,
}


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


class CoinbaseFeed:
    BASE = "https://api.exchange.coinbase.com"

    def __init__(
        self,
        instruments: Sequence[str] = ("BTC-USD",),
        granularity: int = 86_400,
        session: Optional[object] = None,
        retries: int = 4,
        backoff: float = 1.0,
    ):
        self.instruments = list(instruments)
        self.granularity = granularity
        self._session = session
        self.retries = retries
        self.backoff = backoff

    @staticmethod
    def parse_candles(rows: Sequence[Sequence[float]]) -> list[Bar]:
        """Coinbase candle rows -> time-ordered Bars (oldest first)."""
        bars: list[Bar] = []
        for row in sorted(rows, key=lambda r: r[0]):
            t, low, high, _open, close, volume = row[:6]
            bars.append(Bar(asof=_iso(t), close=float(close),
                            high=float(high), low=float(low), volume=float(volume)))
        return bars

    def _get(self):
        if self._session is None:
            import requests  # lazy: keep offline paths import-free
            self._session = requests.Session()
        return self._session

    def fetch(self, instrument: str) -> list[Bar]:
        def _attempt(_i: int) -> list[Bar]:
            resp = self._get().get(
                f"{self.BASE}/products/{instrument}/candles",
                params={"granularity": self.granularity},
                timeout=15,
            )
            resp.raise_for_status()
            return self.parse_candles(resp.json())
        return with_retries(_attempt, attempts=self.retries, backoff=self.backoff)

    def snapshots(self) -> Iterator[Snapshot]:
        series = {inst: self.fetch(inst) for inst in self.instruments}
        yield from ReplayFeed(series).snapshots()
