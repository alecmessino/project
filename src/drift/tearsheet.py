"""Long-history tearsheets: strategy vs. buy-and-hold, with an honest
in-sample / out-of-sample split.

This is the credibility layer. For each "book" (an equal-weight universe) it:

  1. pulls long history (Yahoo `range=max`),
  2. fits the model's free parameters (`lookback`, `continuation`) on the *first*
     part of the sample and reports performance on the *held-out* remainder, so a
     reader can see how much edge survives out of sample, and
  3. compares the strategy to simply buying and holding the same universe, with a
     full metric block (CAGR, Sharpe, Sortino, Calmar, max-DD) and a
     returns-by-year table.

Everything is pure given the input series; the network pull is isolated in `_pull`.
"""

from __future__ import annotations

import time
from typing import Optional, Sequence

from . import analytics
from .backtest import strategy_steps
from .cross_section import cross_book_streams
from .config import Settings
from .exhibit import _spark
from .models import Bar

GRID_LOOKBACK = (40, 60, 80, 120)
GRID_CONTINUATION = (0.10, 0.25)


def _splice(fund: list[Bar], proxy: list[Bar]) -> list[Bar]:
    """Return-splice a proxy's history onto a fund before the fund's inception.

    The proxy is scaled so its level connects continuously at the fund's first bar,
    so pre-inception *returns* are the proxy's and post-inception returns are the
    fund's. Because the strategy reads returns / log-returns, the trend z-score is
    continuous across the join — exactly the point of a tight-tracking proxy.
    """
    from .models import Bar as _Bar
    if not fund or not proxy:
        return fund
    t0 = fund[0].asof[:10]
    pre = [b for b in proxy if b.asof[:10] < t0]
    if not pre or not pre[-1].close:
        return fund
    factor = fund[0].close / pre[-1].close
    spliced = [_Bar(asof=b.asof, close=b.close * factor,
                    high=(b.high * factor if b.high is not None else None),
                    low=(b.low * factor if b.low is not None else None),
                    volume=b.volume) for b in pre]
    return spliced + fund


def _pull(symbols: Sequence[str], years: float = 40.0, pause: float = 0.2,
          proxies: bool = True) -> tuple[dict[str, list[Bar]], dict[str, str]]:
    """Pull TRUE daily history from Yahoo (keyless), skipping any symbol that fails.

    Uses explicit epoch bounds (not `range=max`, which Yahoo coarsens to monthly)
    so daily annualization (252 bars/yr) is correct. Young pure-factor funds are
    back-filled before inception with their passive proxy (see `universes.PROXY`);
    returns the spliced series plus a map of {fund: proxy} actually applied.
    """
    from .feed.yahoo import YahooFeed
    from .universes import PROXY
    now = int(time.time())
    feed = YahooFeed(interval="1d", period1=now - int(years * 31_557_600), period2=now)

    def _fetch(sym):
        try:
            return feed.fetch(sym)
        except Exception:
            return None

    series: dict[str, list[Bar]] = {}
    applied: dict[str, str] = {}
    for i, sym in enumerate(symbols):
        if pause and i:
            time.sleep(pause)
        bars = _fetch(sym)
        if bars is None:
            continue
        if proxies and sym in PROXY:
            pbars = _fetch(PROXY[sym])
            if pbars and pbars[0].asof[:10] < bars[0].asof[:10]:
                bars = _splice(bars, pbars)
                applied[sym] = PROXY[sym]
        if len(bars) >= 252:           # need at least ~1y of daily history
            series[sym] = bars
    return series, applied


def _clone(settings: Settings, lookback: int, continuation: float) -> Settings:
    s = settings.model_copy(deep=True)
    s.signal.lookback = lookback
    s.signal.continuation = continuation
    return s


def book_streams(series: dict[str, list[Bar]], settings: Settings
                 ) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Equal-weight (strategy, benchmark) dated return streams across a universe.

    Strategy = mean of per-name net strategy returns each date; benchmark = mean of
    the names' own returns each date (equal-weight buy-and-hold, the fair yardstick).
    """
    strat: dict[str, list[float]] = {}
    bench: dict[str, list[float]] = {}
    for inst, bars in series.items():
        for st in strategy_steps(inst, bars, settings):
            strat.setdefault(st.asof, []).append(st.net_ret)
            bench.setdefault(st.asof, []).append(st.asset_ret)
    dates = sorted(strat)
    s = [(d, sum(strat[d]) / len(strat[d])) for d in dates]
    b = [(d, sum(bench[d]) / len(bench[d])) for d in dates]
    return s, b


def _split_date(dated: Sequence[tuple[str, float]], train_frac: float) -> Optional[str]:
    if not dated:
        return None
    idx = min(len(dated) - 1, int(len(dated) * train_frac))
    return dated[idx][0]


def fit_params(series: dict[str, list[Bar]], settings: Settings, split: str
               ) -> tuple[int, float, float]:
    """Grid-fit (lookback, continuation) by maximizing IN-SAMPLE Sharpe (dates <= split)."""
    bpy = settings.engine.bars_per_year
    best: Optional[tuple[float, int, float]] = None
    for L in GRID_LOOKBACK:
        for c in GRID_CONTINUATION:
            strat = cross_book_streams(series, _clone(settings, L, c))
            train = [r for d, r in strat if d <= split]
            sh = analytics.sharpe(train, bpy)
            if best is None or sh > best[0]:
                best = (sh, L, c)
    return best[1], best[2], best[0]


def _market_block(market: list[Bar], dates: list[str], idx: list[int], bpy: float) -> Optional[dict]:
    """Buy-and-hold metrics + equity for a global-market reference, aligned to the
    book's trading dates (so the curves overlay on the same axis)."""
    if not market:
        return None
    mret = {}
    for i in range(1, len(market)):
        if market[i - 1].close:
            mret[market[i].asof[:10]] = market[i].close / market[i - 1].close - 1.0
    dated = [(d, mret.get(d[:10], 0.0)) for d in dates]
    eq = analytics.equity_from_returns([r for _, r in dated])
    return {"label": "Global market (VT)", "summary": analytics.summary(dated, bpy),
            "equity": [round(eq[i], 5) for i in idx]}


def build_book(name: str, series: dict[str, list[Bar]], settings: Settings,
               train_frac: float = 0.6, market: Optional[list[Bar]] = None) -> dict:
    """One book's tearsheet: fit on train, evaluate OOS, benchmark, by-year."""
    bpy = settings.engine.bars_per_year
    # Strategy = the trend-throttled cross-sectional rotation; benchmark = equal-weight
    # buy-and-hold of the same universe.
    base_strat = cross_book_streams(series, settings)
    split = _split_date(base_strat, train_frac)

    lookback, continuation, train_sharpe = fit_params(series, settings, split)
    tuned = _clone(settings, lookback, continuation)
    strat = cross_book_streams(series, tuned)
    _, bench = book_streams(series, tuned)

    train = [(d, r) for d, r in strat if d <= split]
    test = [(d, r) for d, r in strat if d > split]

    by_strat = dict(analytics.returns_by_year(strat))
    by_bench = dict(analytics.returns_by_year(bench))
    years = sorted(set(by_strat) | set(by_bench))

    strat_eq = analytics.equity_from_returns([r for _, r in strat])
    bench_eq = analytics.equity_from_returns([r for _, r in bench])
    n = len(strat_eq)
    idx = list(range(0, n, max(1, n // 120)))

    return {
        "name": name,
        "universe": sorted(series),
        "n_names": len(series),
        "span": [strat[0][0][:10], strat[-1][0][:10]] if strat else ["", ""],
        "fit": {
            "train_frac": train_frac, "split": split[:10] if split else "",
            "lookback": lookback, "continuation": continuation,
        },
        "strategy": analytics.summary(strat, bpy),
        "benchmark": analytics.summary(bench, bpy),
        "market": _market_block(market, [d for d, _ in strat], idx, bpy),
        "oos": {
            "train": analytics.summary(train, bpy),
            "test": analytics.summary(test, bpy),
        },
        "by_year": [{"year": y,
                     "strat": round(by_strat.get(y, 0.0), 4),
                     "bench": round(by_bench.get(y, 0.0), 4)} for y in years],
        "equity": {
            "split_frac": (sum(1 for d, _ in strat if d <= split) / n) if n else 0.0,
            "strat": [round(strat_eq[i], 5) for i in idx],
            "bench": [round(bench_eq[i], 5) for i in idx],
            "market": (_market_block(market, [d for d, _ in strat], idx, bpy) or {}).get("equity"),
        },
    }


# Default books — keyless via Yahoo (equities + crypto both available there).
# The equities book is the curated region × factor universe.
from .universes import CRYPTO as CRYPTO_UNIVERSE, EQUITIES as EQUITY_UNIVERSE  # noqa: E402


def build_tearsheet(settings: Settings, equities: Sequence[str] = EQUITY_UNIVERSE,
                    crypto: Sequence[str] = CRYPTO_UNIVERSE, years: float = 40.0,
                    train_frac: float = 0.6, _series: Optional[dict] = None) -> dict:
    """Assemble the multi-book tearsheet report (pulls long history unless injected)."""
    books = []
    proxied: dict[str, str] = {}
    market = None
    if _series is not None:
        for nm, ser in _series.items():
            if ser:
                books.append(build_book(nm, ser, settings, train_frac))
    else:
        eq, eq_px = _pull(equities, years=years)
        cr, _ = _pull(crypto, years=years)
        proxied.update(eq_px)
        # Global-market reference: VT, extended with VTI before VT's 2008 inception.
        mkt, mkt_px = _pull(["VT"], years=years)
        if mkt.get("VT"):
            market = mkt["VT"]
            proxied.update(mkt_px)
        if eq:
            books.append(build_book("Equities & ETFs", eq, settings, train_frac, market=market))
        if cr:
            books.append(build_book("Crypto", cr, settings, train_frac))
    return {
        "header": {
            "title": "Driftwood — long-history tearsheet",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "method": f"params fit on first {int(train_frac*100)}% (in-sample), "
                      f"reported on the held-out remainder (out-of-sample); benchmark "
                      f"= equal-weight buy-and-hold; net of {settings.sizing.cost_bps_per_side:.0f}bps/side.",
            # Disclose any pre-inception proxy splices, e.g. {"AVEE": "EEMS"}.
            "proxied": proxied,
        },
        "books": books,
    }
