"""Tiingo daily EOD feed (keyed) — the reliable source from cloud/CI IPs.

Yahoo's chart API IP-bans GitHub Actions runners (429 on the first call), so the daily refresh
silently served stale data. Tiingo's daily endpoint authenticates with a free API token and does
not IP-block, so it is the dependable primary when ``TIINGO_API_KEY`` is present. Same
``fetch(instrument) -> list[Bar]`` interface; the HTTP ``session`` is injectable for offline tests.

Endpoint: GET /tiingo/daily/{ticker}/prices?startDate=YYYY-MM-DD&token=...&format=json
Returns rows with adjusted OHLC (adjClose/adjHigh/adjLow/adjVolume) — we use the adjusted series
so it matches Yahoo's adjusted-close basis.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ..models import Bar
from ._retry import with_retries


def _f(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


class TiingoFeed:
    BASE = "https://api.tiingo.com/tiingo/daily"

    def __init__(self, token: str, *, lookback_days: int = 760,
                 session: Optional[object] = None, retries: int = 3, backoff: float = 1.0):
        self.token = token
        self.lookback_days = lookback_days  # ~2y of calendar days
        self._session = session
        self.retries = retries
        self.backoff = backoff

    @staticmethod
    def parse_json(rows) -> list[Bar]:
        bars: list[Bar] = []
        for r in rows or []:
            c = r.get("adjClose")
            if c is None:
                c = r.get("close")
            if c is None:
                continue
            h = r.get("adjHigh", r.get("high"))
            lo = r.get("adjLow", r.get("low"))
            v = r.get("adjVolume", r.get("volume"))
            bars.append(Bar(asof=(r.get("date") or "")[:10], close=round(float(c), 6),
                            high=(lambda x: round(x, 6) if x is not None else None)(_f(h)),
                            low=(lambda x: round(x, 6) if x is not None else None)(_f(lo)),
                            volume=_f(v)))
        return bars

    def _get(self):
        if self._session is None:
            import requests  # lazy
            self._session = requests.Session()
        return self._session

    def fetch(self, instrument: str) -> list[Bar]:
        start = (date.today() - timedelta(days=self.lookback_days)).isoformat()

        def _attempt(i: int) -> list[Bar]:
            resp = self._get().get(
                f"{self.BASE}/{instrument}/prices",
                params={"startDate": start, "token": self.token, "format": "json"},
                timeout=20,
            )
            resp.raise_for_status()
            return self.parse_json(resp.json())
        return with_retries(_attempt, attempts=self.retries, backoff=self.backoff)
