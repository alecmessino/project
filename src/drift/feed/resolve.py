"""Multi-source equity fetch — the single place that defines the data-source chain.

Yahoo's chart API IP-bans cloud runners (GitHub Actions), which silently froze the daily refresh.
Every build path (ledger, equities studies/export, the 40-yr tearsheet) pulls through the same
fallback chain so the whole site stays live: Tiingo (keyed, reliable from CI) -> Stooq (keyless
CSV) -> Yahoo. First source returning enough history for a symbol wins.
"""

from __future__ import annotations

import os
import time
from random import uniform
from typing import Optional, Sequence

from ..models import Bar

# ~40 years of seconds / days, for the long-history (tearsheet) path.
_LONG_SECONDS = 40 * 31_557_600
_LONG_DAYS = 40 * 366


def equity_feeds(*, long_history: bool = False, env: Optional[dict] = None):
    """Ordered ``[(name, feed)]`` chain. Tiingo only if ``TIINGO_API_KEY`` is set; the long path
    requests ~40y of history (Yahoo via explicit epoch bounds, Tiingo via a deep lookback, Stooq
    returns full history by default)."""
    env = env if env is not None else os.environ
    feeds: list[tuple[str, object]] = []
    tok = env.get("TIINGO_API_KEY")
    if tok:
        from .tiingo import TiingoFeed
        feeds.append(("tiingo", TiingoFeed(tok, lookback_days=_LONG_DAYS if long_history else 760)))
    from .stooq import StooqFeed
    feeds.append(("stooq", StooqFeed()))
    from .yahoo import YahooFeed
    if long_history:
        now = int(time.time())
        feeds.append(("yahoo", YahooFeed(interval="1d", period1=now - _LONG_SECONDS, period2=now)))
    else:
        feeds.append(("yahoo", YahooFeed(range="2y", interval="1d")))
    return feeds


def pull_symbol(sym: str, feeds, min_bars: int) -> Optional[list[Bar]]:
    """First source in the chain that returns >= ``min_bars`` for ``sym``; else None."""
    for _name, fd in feeds:
        try:
            bars = fd.fetch(sym)
            if len(bars) >= min_bars:
                return bars
        except Exception:
            continue
    return None


def pull_universe(symbols: Sequence[str], feeds=None, *, min_bars: int = 60,
                  pause: float = 0.0) -> dict[str, list[Bar]]:
    """Pull a universe through the chain, per-symbol fallback; skips symbols no source can serve.
    ``pause`` adds jittered spacing between symbols to dodge burst rate-limiting."""
    if feeds is None:
        feeds = equity_feeds()
    series: dict[str, list[Bar]] = {}
    for i, sym in enumerate(symbols):
        if pause and i:
            time.sleep(uniform(pause, pause * 1.5))
        bars = pull_symbol(sym, feeds, min_bars)
        if bars is not None:
            series[sym] = bars
    return series
