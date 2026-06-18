"""Run the model across a set of backtest case studies and assemble a report.

The studies are chosen to show the strategy honestly — not just a single flattering
curve, but how it behaves across instruments, across parameters, against cost, and
against a no-trend null:

1. Trend-following (time-series) — each instrument on its own trend, equal-weighted.
2. Relative-strength (cross-sectional) — long strongest / short weakest.
3. Lookback sensitivity — is the edge robust to the window, or curve-fit to one?
4. Transaction-cost sensitivity — where does the net edge decay to zero?
5. Trend vs. random walk — the control: momentum should profit on a trend and
   make ~nothing (net of cost) on a driftless walk.

Everything here is pure given the input series, so it is fully unit-testable; the
live equities pull is isolated in `equity_universe`.
"""

from __future__ import annotations

import time
from typing import Optional, Sequence

from .backtest import backtest
from .config import Settings
from .cross_section import cross_backtest
from .exhibit import _spark
from .feed.synthetic import SyntheticFeed
from .models import Bar


def equity_universe(symbols: Sequence[str], source: str = "yahoo",
                    pause: float = 0.0) -> dict[str, list[Bar]]:
    """Pull an equities universe, skipping any symbol that fails.

    `source="yahoo"` (default) is keyless and comprehensive; `source="polygon"`
    uses Polygon (needs POLYGON_API_KEY) — with no key its fetches raise and are
    skipped, so the report degrades gracefully to the synthetic control only.
    `pause` seconds between fetches is light insurance against burst rate-limiting.
    """
    import time
    if source == "polygon":
        from .feed.polygon import PolygonFeed
        feed = PolygonFeed()
    else:
        from .feed.yahoo import YahooFeed
        feed = YahooFeed()
    series: dict[str, list[Bar]] = {}
    for i, sym in enumerate(symbols):
        if pause and i:
            time.sleep(pause)
        try:
            bars = feed.fetch(sym)
        except Exception:
            continue
        if len(bars) >= 60:
            series[sym] = bars
    return series


def _clone(settings: Settings, *, lookback: Optional[int] = None,
           cost: Optional[float] = None) -> Settings:
    s = settings.model_copy(deep=True)
    if lookback is not None:
        s.signal.lookback = lookback
    if cost is not None:
        s.sizing.cost_bps_per_side = cost
    return s


def _tone(x: float) -> str:
    return "pos" if x > 0 else "neg" if x < 0 else "neutral"


def _metric(label: str, value: str, tone: str = "neutral") -> dict:
    return {"label": label, "value": value, "tone": tone}


def _equal_weight_equity(curves: list[list[float]]) -> list[float]:
    """Equal-weight, rebalanced-each-bar portfolio equity from per-name curves."""
    curves = [c for c in curves if len(c) > 1]
    if not curves:
        return []
    length = min(len(c) for c in curves)
    rets = [[(c[i] / c[i - 1] - 1.0) if c[i - 1] else 0.0 for i in range(1, length)] for c in curves]
    eq = [1.0]
    for t in range(length - 1):
        avg = sum(r[t] for r in rets) / len(rets)
        eq.append(eq[-1] * (1.0 + avg))
    return eq


def study_timeseries(series: dict[str, list[Bar]], settings: Settings) -> dict:
    rows, curves, nets = [], [], []
    for inst, bars in sorted(series.items()):
        bt = backtest(inst, bars, settings)
        rows.append([inst, f"{bt.net_return*100:+.1f}%", f"{bt.sharpe:.2f}",
                     f"{bt.max_drawdown*100:.1f}%", str(bt.n_trades)])
        curves.append(bt.equity_curve)
        nets.append(bt.net_return)
    eq = _equal_weight_equity(curves)
    agg_net = (eq[-1] - 1.0) if eq else 0.0
    win = sum(1 for n in nets if n > 0)
    return {
        "name": "Trend-following (time-series)",
        "description": "Each instrument traded on its own absolute, vol-normalized "
                       "trend; breakout-confirmed; shown as an equal-weight book.",
        "metrics": [
            _metric("Equal-weight net", f"{agg_net*100:+.1f}%", _tone(agg_net)),
            _metric("Profitable names", f"{win}/{len(nets)}"),
            _metric("Best name", f"{max(nets)*100:+.1f}%" if nets else "—", "pos"),
            _metric("Worst name", f"{min(nets)*100:+.1f}%" if nets else "—", "neg"),
        ],
        "table": {"columns": ["Instrument", "Net", "Sharpe", "Max DD", "Trades"], "rows": rows},
        "equity": _spark(eq),
    }


def study_cross(series: dict[str, list[Bar]], settings: Settings) -> dict:
    xbt = cross_backtest(series, settings)
    return {
        "name": "Relative-strength (cross-sectional)",
        "description": "Rank the universe each bar; long the strongest, short the "
                       "weakest (dollar-neutral). Bets on dispersion, not market level.",
        "metrics": [
            _metric("Net return", f"{xbt.net_return*100:+.1f}%", _tone(xbt.net_return)),
            _metric("Gross", f"{xbt.gross_return*100:+.1f}%", _tone(xbt.gross_return)),
            _metric("Sharpe", f"{xbt.sharpe:.2f}", _tone(xbt.sharpe)),
            _metric("Max DD", f"{xbt.max_drawdown*100:.1f}%", "neg"),
            _metric("Turnover", f"{xbt.turnover:.1f}"),
        ],
        "table": None,
        "equity": _spark(xbt.equity_curve),
    }


def study_cross_neutral(series: dict[str, list[Bar]], settings: Settings,
                        dim: str = "region") -> dict:
    """Cross-sectional, but neutral to `dim` (region/factor): demean trend scores
    within each group so the book bets on within-group leadership only."""
    s = settings.model_copy(deep=True)
    s.cross_section.neutralize = dim
    xbt = cross_backtest(series, s)
    other = "style" if dim == "region" else "region"
    return {
        "name": f"{dim.capitalize()}-neutral relative-strength",
        "description": f"The cross-section with each {dim}'s mean trend removed, so it "
                       f"bets purely on which {other} is leading WITHIN every {dim} — "
                       f"isolating {other} rotation from {dim} rotation.",
        "metrics": [
            _metric("Net return", f"{xbt.net_return*100:+.1f}%", _tone(xbt.net_return)),
            _metric("Sharpe", f"{xbt.sharpe:.2f}", _tone(xbt.sharpe)),
            _metric("Max DD", f"{xbt.max_drawdown*100:.1f}%", "neg"),
            _metric("Turnover", f"{xbt.turnover:.1f}"),
        ],
        "table": None,
        "equity": _spark(xbt.equity_curve),
    }


def study_lookback_sensitivity(series: dict[str, list[Bar]], settings: Settings,
                               lookbacks=(20, 40, 60, 120)) -> dict:
    inst, bars = max(series.items(), key=lambda kv: len(kv[1]))
    rows, best = [], None
    for L in lookbacks:
        if len(bars) <= L + settings.signal.vol_window:
            continue
        bt = backtest(inst, bars, _clone(settings, lookback=L))
        rows.append([str(L), f"{bt.net_return*100:+.1f}%", f"{bt.sharpe:.2f}", str(bt.n_trades)])
        if best is None or bt.sharpe > best[1]:
            best = (L, bt.sharpe)
    return {
        "name": f"Lookback sensitivity ({inst})",
        "description": "Net result as the trend window varies. A robust edge is "
                       "stable across windows; a single sweet spot signals overfitting.",
        "metrics": [_metric("Best window", f"{best[0]} bars" if best else "—"),
                    _metric("Best Sharpe", f"{best[1]:.2f}" if best else "—",
                            _tone(best[1] if best else 0))],
        "table": {"columns": ["Lookback", "Net", "Sharpe", "Trades"], "rows": rows},
        "equity": None,
    }


def study_cost_sensitivity(series: dict[str, list[Bar]], settings: Settings,
                           costs=(1.0, 5.0, 10.0, 25.0)) -> dict:
    rows = []
    for c in costs:
        xbt = cross_backtest(series, _clone(settings, cost=c))
        rows.append([f"{c:.0f} bps", f"{xbt.net_return*100:+.1f}%",
                     f"{xbt.sharpe:.2f}", f"{xbt.turnover:.0f}"])
    return {
        "name": "Transaction-cost sensitivity (cross-sectional)",
        "description": "The decisive test for a short-horizon strategy: how fast the "
                       "net edge erodes as per-side cost rises. Where it crosses zero "
                       "is the real capacity limit.",
        "metrics": [_metric("Cost levels", f"{len(costs)} tested")],
        "table": {"columns": ["Cost/side", "Net", "Sharpe", "Turnover"], "rows": rows},
        "equity": None,
    }


def study_trend_vs_noise(settings: Settings) -> dict:
    """Synthetic control: profit on a real trend, ~nothing on a driftless walk."""
    cfg = _clone(settings, lookback=min(settings.signal.lookback, 40))
    trend = SyntheticFeed(instruments=("TREND",), n_bars=500,
                          regimes=[(500, 0.55)], seed=21).series("TREND")
    walk = SyntheticFeed(instruments=("WALK",), n_bars=500,
                         regimes=[(500, 0.0)], seed=21).series("WALK")
    bt_t = backtest("TREND", trend, cfg)
    bt_w = backtest("WALK", walk, cfg)
    return {
        "name": "Trend vs. random walk (synthetic control)",
        "description": "Sanity check on identical parameters: a trend-follower should "
                       "make money on a genuine trend and roughly break even (or lose "
                       "to cost) on a no-trend random walk. If the walk pays, it's a bug.",
        "metrics": [
            _metric("Trend net", f"{bt_t.net_return*100:+.1f}%", _tone(bt_t.net_return)),
            _metric("Walk net", f"{bt_w.net_return*100:+.1f}%", _tone(bt_w.net_return)),
            _metric("Trend Sharpe", f"{bt_t.sharpe:.2f}", _tone(bt_t.sharpe)),
            _metric("Walk Sharpe", f"{bt_w.sharpe:.2f}", _tone(bt_w.sharpe)),
        ],
        "table": {"columns": ["Series", "Net", "Sharpe", "Max DD", "Trades"], "rows": [
            ["Trend", f"{bt_t.net_return*100:+.1f}%", f"{bt_t.sharpe:.2f}",
             f"{bt_t.max_drawdown*100:.1f}%", str(bt_t.n_trades)],
            ["Random walk", f"{bt_w.net_return*100:+.1f}%", f"{bt_w.sharpe:.2f}",
             f"{bt_w.max_drawdown*100:.1f}%", str(bt_w.n_trades)],
        ]},
        "equity": None,
    }


def build_report(series: dict[str, list[Bar]], settings: Settings, source: str = "—") -> dict:
    """Assemble the full case-studies report from a universe of price series."""
    studies = []
    if series:
        studies.append(study_timeseries(series, settings))
        if len(series) >= settings.cross_section.min_universe:
            studies.append(study_cross(series, settings))
            # Region-neutral variant, only when the universe spans >=2 known regions.
            from .universes import REGION_OF
            regions = {REGION_OF[i] for i in series if i in REGION_OF}
            if len(regions) >= 2:
                studies.append(study_cross_neutral(series, settings, dim="region"))
        studies.append(study_lookback_sensitivity(series, settings))
        if len(series) >= settings.cross_section.min_universe:
            studies.append(study_cost_sensitivity(series, settings))
    studies.append(study_trend_vs_noise(settings))
    n_bars = max((len(b) for b in series.values()), default=0)
    return {
        "header": {
            "title": "Driftwood — backtest case studies",
            "source": source,
            "universe": ", ".join(sorted(series)) or "synthetic only",
            "n_instruments": len(series),
            "n_bars": n_bars,
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "model": f"lookback {settings.signal.lookback} · vol {settings.signal.vol_window} "
                     f"· channel {settings.signal.breakout_channel} · "
                     f"cost {settings.sizing.cost_bps_per_side:.0f}bps/side",
        },
        "studies": studies,
    }
