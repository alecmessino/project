"""Live equities/ETF/index feed: Yahoo Finance chart API (no API key required).

Endpoint: GET /v8/finance/chart/{symbol}?range={range}&interval={interval}
Returns parallel arrays of timestamps + OHLCV under `chart.result[0]`, plus an
`adjclose` series. We back-adjust the whole bar by the adjusted/raw close ratio so
the OHLC stays internally consistent (the Donchian breakout needs high/low on the
same basis as close) while still being split/dividend-adjusted for the long-horizon
trend signal.

Keyless and comprehensive — the same endpoint serves equities, ETFs, indices, FX,
and crypto — which is why it's the default equities source. The HTTP `session` is
injectable so parsing is unit-tested with no network.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator, Optional, Sequence

from ..models import Bar
from .base import Snapshot
from .replay import ReplayFeed

# Yahoo interval -> bars per year, for the engine's annualization.
INTERVAL_BARS_PER_YEAR = {
    "1d": 252, "5d": 50, "1wk": 52, "1mo": 12,
    "60m": 1_638, "1h": 1_638, "30m": 3_276, "15m": 6_552, "5m": 19_656,
}
# A browser-like UA; Yahoo rejects the default python-requests agent intermittently.
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


class YahooFeed:
    HOSTS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")

    def __init__(
        self,
        instruments: Sequence[str] = ("SPY",),
        range: str = "2y",
        interval: str = "1d",
        session: Optional[object] = None,
    ):
        self.instruments = list(instruments)
        self.range = range
        self.interval = interval
        self._session = session

    @staticmethod
    def parse_chart(payload: dict) -> list[Bar]:
        """Yahoo chart payload -> time-ordered, split/dividend-adjusted Bars."""
        results = (payload.get("chart") or {}).get("result") or []
        if not results:
            return []
        r = results[0]
        ts = r.get("timestamp") or []
        ind = r.get("indicators") or {}
        q = (ind.get("quote") or [{}])[0]
        highs, lows, closes, vols = (q.get("high") or [], q.get("low") or [],
                                     q.get("close") or [], q.get("volume") or [])
        adj_block = ind.get("adjclose") or []
        adj = (adj_block[0].get("adjclose") if adj_block else None) or []

        bars: list[Bar] = []
        for i, t in enumerate(ts):
            c = closes[i] if i < len(closes) else None
            if c is None:
                continue  # Yahoo emits nulls for holidays/halts
            ac = adj[i] if i < len(adj) else None
            factor = (ac / c) if (ac is not None and c) else 1.0
            h = highs[i] if i < len(highs) else None
            lo = lows[i] if i < len(lows) else None
            v = vols[i] if i < len(vols) else None
            bars.append(Bar(
                asof=_iso(t),
                close=round(ac if ac is not None else c, 6),
                high=round(h * factor, 6) if h is not None else None,
                low=round(lo * factor, 6) if lo is not None else None,
                volume=float(v) if v is not None else None,
            ))
        return bars

    def _get(self):
        if self._session is None:
            import requests  # lazy: keep offline paths import-free
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": _UA})
        return self._session

    def fetch(self, instrument: str) -> list[Bar]:
        last_exc: Optional[Exception] = None
        for host in self.HOSTS:                       # fail over query1 -> query2
            try:
                resp = self._get().get(
                    f"{host}/v8/finance/chart/{instrument}",
                    params={"range": self.range, "interval": self.interval},
                    timeout=20,
                )
                resp.raise_for_status()
                return self.parse_chart(resp.json())
            except Exception as exc:
                last_exc = exc
        raise last_exc if last_exc else RuntimeError("yahoo fetch failed")

    def snapshots(self) -> Iterator[Snapshot]:
        series = {inst: self.fetch(inst) for inst in self.instruments}
        yield from ReplayFeed(series).snapshots()
