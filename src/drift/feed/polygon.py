"""Live equities feed: Polygon.io aggregate bars (requires POLYGON_API_KEY).

Endpoint: GET /v2/aggs/ticker/{ticker}/range/{mult}/{timespan}/{from}/{to}
Returns {"results": [{"t": epoch_ms, "o","h","l","c","v"}, ...]}.

The HTTP `session` is injectable so parsing and wiring are unit-tested offline;
the API key is read from the environment (loaded from .env if present) and never
logged.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Iterator, Optional, Sequence

from ..envload import load_env
from ..models import Bar
from .base import Snapshot
from .replay import ReplayFeed

TIMESPAN_BARS_PER_YEAR = {"minute": 98_280, "hour": 1_638, "day": 252, "week": 52, "month": 12}


def _iso_ms(epoch_ms: float) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc).isoformat()


class PolygonFeed:
    BASE = "https://api.polygon.io"

    def __init__(
        self,
        instruments: Sequence[str] = ("SPY",),
        timespan: str = "day",
        multiplier: int = 1,
        start: Optional[str] = None,
        end: Optional[str] = None,
        api_key: Optional[str] = None,
        session: Optional[object] = None,
    ):
        load_env()
        self.instruments = list(instruments)
        self.timespan = timespan
        self.multiplier = multiplier
        self.end = end or date.today().isoformat()
        self.start = start or (date.today() - timedelta(days=730)).isoformat()
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        self._session = session

    @staticmethod
    def parse_aggs(payload: dict) -> list[Bar]:
        """Polygon aggregates payload -> time-ordered Bars (oldest first)."""
        bars: list[Bar] = []
        for r in payload.get("results", []):
            bars.append(Bar(asof=_iso_ms(r["t"]), close=float(r["c"]),
                            high=float(r["h"]), low=float(r["l"]),
                            volume=float(r["v"]) if r.get("v") is not None else None))
        return sorted(bars, key=lambda b: b.asof)

    def _get(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def fetch(self, instrument: str) -> list[Bar]:
        if not self.api_key:
            raise RuntimeError("POLYGON_API_KEY not set (put it in .env or the environment)")
        url = (f"{self.BASE}/v2/aggs/ticker/{instrument}/range/"
               f"{self.multiplier}/{self.timespan}/{self.start}/{self.end}")
        resp = self._get().get(
            url,
            params={"adjusted": "true", "sort": "asc", "limit": 50_000, "apiKey": self.api_key},
            timeout=20,
        )
        resp.raise_for_status()
        return self.parse_aggs(resp.json())

    def snapshots(self) -> Iterator[Snapshot]:
        series = {inst: self.fetch(inst) for inst in self.instruments}
        yield from ReplayFeed(series).snapshots()
