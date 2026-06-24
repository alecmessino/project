"""Stooq daily EOD feed — keyless CSV source used as a fallback for the live ledger.

Yahoo's chart API persistently rate-limits (HTTP 429) cloud IP ranges such as GitHub Actions,
which silently froze the daily ledger. Stooq serves a plain daily CSV and is generally tolerant
of automated/cloud access, so it is tried alongside Yahoo. Same `fetch(instrument) -> list[Bar]`
interface; the HTTP `session` is injectable for offline unit tests.

CSV shape: ``Date,Open,High,Low,Close,Volume`` (split-adjusted). If the response is not a CSV
header (e.g. an anti-bot challenge page), parsing yields no bars so the caller falls back cleanly.
"""

from __future__ import annotations

from typing import Optional

from ..models import Bar
from ._retry import with_retries

_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def _f(x: Optional[str]):
    if x is None or x in ("", "N/D"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


class StooqFeed:
    BASE = "https://stooq.com/q/d/l/"

    def __init__(self, *, suffix: str = ".us", session: Optional[object] = None,
                 retries: int = 3, backoff: float = 1.0):
        self.suffix = suffix
        self._session = session
        self.retries = retries
        self.backoff = backoff

    @staticmethod
    def parse_csv(text: str) -> list[Bar]:
        lines = [ln for ln in (text or "").strip().splitlines() if ln]
        if not lines or not lines[0].lower().startswith("date"):
            return []  # HTML/challenge/empty -> no bars; caller falls back to another source
        bars: list[Bar] = []
        for row in lines[1:]:
            p = row.split(",")
            if len(p) < 5:
                continue
            close = _f(p[4])
            if close is None:
                continue
            bars.append(Bar(asof=p[0], close=round(close, 6),
                            high=(lambda h: round(h, 6) if h is not None else None)(_f(p[2])),
                            low=(lambda lo: round(lo, 6) if lo is not None else None)(_f(p[3])),
                            volume=_f(p[5]) if len(p) > 5 else None))
        return bars

    def _get(self):
        if self._session is None:
            import requests  # lazy
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": _UA})
        return self._session

    def fetch(self, instrument: str) -> list[Bar]:
        ticker = instrument.lower()
        if self.suffix and "." not in ticker:
            ticker += self.suffix

        def _attempt(i: int) -> list[Bar]:
            resp = self._get().get(self.BASE, params={"s": ticker, "i": "d"}, timeout=20)
            resp.raise_for_status()
            return self.parse_csv(resp.text)
        return with_retries(_attempt, attempts=self.retries, backoff=self.backoff)
