"""Forward paper-trade ledger: an append-only, out-of-sample track record.

A backtest can always be overfit; a forward record cannot. Each session the
ledger (a) marks the positions it held from the prior session to now against the
prices that actually printed, (b) advances a cumulative equity, and (c) records
the new target positions to carry forward. It only ever appends — history is never
recomputed — which is exactly what makes it credible.

The book is the equal-weight combination of the per-instrument trend positions
(the same construction the tearsheet benchmarks), marked daily. Weekends/holidays
fall out naturally: an instrument is marked from its last close on-or-before the
prior ledger date to its latest close, so a Friday→Monday move lands on the next
run.
"""

from __future__ import annotations

import time
from typing import Optional, Sequence

from . import analytics
from . import signal as sig
from . import sizing
from .config import Settings
from .cross_section import _groups_for, rank_weights
from .models import Bar
from .universes import REGION_OF, SIZE_OF, STYLE_OF


def _latest_date(series: dict[str, list[Bar]]) -> str:
    return max((bars[-1].asof for bars in series.values() if bars), default="")


def _close_on_or_before(bars: Sequence[Bar], date10: str) -> Optional[float]:
    """Close of the last bar whose date is <= `date10` (YYYY-MM-DD)."""
    found = None
    for b in bars:
        if b.asof[:10] <= date10:
            found = b.close
        else:
            break
    return found


def new_ledger() -> dict:
    return {"entries": [], "universe": [], "inception": "", "updated": ""}


def update_ledger(ledger: dict, series: dict[str, list[Bar]], settings: Settings,
                  seed: bool = False, benchmark_bars: Optional[list[Bar]] = None) -> dict:
    """Append one session to the ledger for the latest date. Idempotent: a date
    already recorded (or no fresh bar) is a no-op. `benchmark_bars` (e.g. VT) is
    marked buy-and-hold alongside the book for an apples-to-apples comparison."""
    cost = settings.sizing.cost_bps_per_side / 1e4
    insts = sorted(i for i, b in series.items() if len(b) >= settings.signal.min_history)
    if not insts:
        return ledger
    latest = _latest_date({i: series[i] for i in insts})
    entries = ledger.setdefault("entries", [])
    if entries and entries[-1]["date"] >= latest[:10]:
        return ledger  # nothing new to mark

    prev = entries[-1] if entries else None
    prev_w: dict[str, float] = prev["weights"] if prev else {}
    equity = prev["equity"] if prev else 1.0
    bench_equity = (prev.get("bench_equity") if prev else 1.0) or 1.0

    # 1) Realize the previously-held cross-sectional book (weights sum to exposure,
    #    so the portfolio return is the weighted sum — not an average).
    realized = 0.0
    if prev:
        for i in insts:
            p_prev = _close_on_or_before(series[i], prev["date"])
            p_now = series[i][-1].close
            if p_prev and p_now:
                realized += prev_w.get(i, 0.0) * (p_now / p_prev - 1.0)

    # 2) New target = the trend-throttled cross-sectional rotation, re-ranked on the
    #    rebalance cadence (held between rebalances so turnover stays low).
    cs = settings.cross_section
    n_prior = len(entries)
    if prev and (n_prior % max(1, cs.rebalance_bars) != 0):
        new_w = {i: round(prev_w.get(i, 0.0), 4) for i in insts}
    else:
        sg = settings.signal
        scores, vols = {}, {}
        for i in insts:
            cl = [b.close for b in series[i]]
            scores[i] = sig.momentum_score(cl, sg.lookback, sg.vol_window)
            vols[i] = sizing.annualize_vol(sig.realized_vol(cl, sg.vol_window),
                                           settings.engine.bars_per_year)
        raw = rank_weights(scores, vols, cs, _groups_for(cs))
        new_w = {i: round(raw.get(i, 0.0), 4) for i in insts}

    # 3) Cost on rebalance turnover (weights are at portfolio scale).
    turnover = sum(abs(new_w[i] - prev_w.get(i, 0.0)) for i in insts)
    net = realized - cost * turnover
    equity = round(equity * (1.0 + net), 6)

    # 4) Mark the buy-and-hold benchmark over the same span (if provided).
    bench_ret = 0.0
    if prev and benchmark_bars:
        bp = _close_on_or_before(benchmark_bars, prev["date"])
        bn = _close_on_or_before(benchmark_bars, latest[:10])
        if bp and bn:
            bench_ret = bn / bp - 1.0
    bench_equity = round(bench_equity * (1.0 + bench_ret), 6)

    entries.append({
        "date": latest[:10],
        "weights": new_w,
        "realized_return": round(net, 6),
        "equity": equity,
        "bench_equity": bench_equity if benchmark_bars else None,
        "n_long": sum(1 for v in new_w.values() if v > 0),
        "n_short": sum(1 for v in new_w.values() if v < 0),
        "seed": bool(seed),
    })
    ledger["universe"] = insts
    ledger["inception"] = ledger.get("inception") or entries[0]["date"]
    ledger["updated"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return ledger


def seed_ledger(series: dict[str, list[Bar]], settings: Settings, sessions: int = 120,
                benchmark_bars: Optional[list[Bar]] = None) -> dict:
    """Bootstrap a ledger by replaying the last `sessions` trading days walk-forward.

    This is a faithful out-of-sample replay (each step sees only data up to that
    date — no lookahead), so the inception curve is meaningful rather than empty.
    Live runs append the newest day on top via `update_ledger`.
    """
    ledger = new_ledger()
    all_dates = sorted({b.asof[:10] for bars in series.values() for b in bars})
    for d in all_dates[-sessions:]:
        sub = {i: [b for b in bars if b.asof[:10] <= d] for i, bars in series.items()}
        bench = [b for b in benchmark_bars if b.asof[:10] <= d] if benchmark_bars else None
        update_ledger(ledger, sub, settings, seed=True, benchmark_bars=bench)
    return ledger


_REGION_NAME = {"US": "United States", "DEV": "Developed intl", "EM": "Emerging mkts"}


def _exposure(weights: dict[str, float]) -> dict:
    """Region / size / style breakdown + 3x3 style box of the current long book,
    as shares of invested gross. For the box, intl/EM 'large/mid' maps to Large."""
    pos = {i: w for i, w in weights.items() if w > 0}
    total = sum(pos.values()) or 1.0
    region: dict[str, float] = {}
    style: dict[str, float] = {}
    box: dict[str, float] = {}
    for i, w in pos.items():
        r, sz, st = REGION_OF.get(i, "?"), SIZE_OF.get(i, "?"), STYLE_OF.get(i, "?")
        region[r] = region.get(r, 0.0) + w
        style[st] = style.get(st, 0.0) + w
        bsz = "large" if sz == "largemid" else sz
        box[f"{bsz}|{st}"] = box.get(f"{bsz}|{st}", 0.0) + w
    return {
        "gross": round(total, 4),
        "by_region": {_REGION_NAME.get(k, k): round(v / total, 4) for k, v in region.items()},
        "by_style": {k: round(v / total, 4) for k, v in style.items()},
        "style_box": {k: round(v / total, 4) for k, v in box.items()},
    }


def build_ledger_state(ledger: dict, bars_per_year: float = 252.0) -> dict:
    """Shape the ledger into the dashboard/exhibit state."""
    entries = ledger.get("entries", [])
    if not entries:
        return {"header": {"days": 0, "inception": "", "total_return": 0.0,
                           "universe": ledger.get("universe", [])},
                "equity": [], "bench": [], "dates": [], "positions": [], "recent": [],
                "exposure": None}
    eq = [e["equity"] for e in entries]
    rets = [e["realized_return"] for e in entries]
    has_bench = entries[-1].get("bench_equity") is not None
    beq = [e.get("bench_equity") or 1.0 for e in entries] if has_bench else []
    n = len(eq)
    idx = list(range(0, n, max(1, n // 160)))
    last = entries[-1]
    positions = sorted(
        ({"instrument": i, "weight": w,
          "leg": "LONG" if w > 0 else "SHORT" if w < 0 else "—"}
         for i, w in last["weights"].items()),
        key=lambda r: -r["weight"])
    live = sum(1 for e in entries if not e.get("seed"))
    return {
        "header": {
            "days": n,
            "live_days": live,
            "seeded_days": n - live,
            "inception": ledger.get("inception", entries[0]["date"]),
            "updated": ledger.get("updated", ""),
            "total_return": round(eq[-1] - 1.0, 6),
            "bench_label": ledger.get("benchmark"),
            "bench_return": round(beq[-1] - 1.0, 6) if has_bench else None,
            "sharpe": round(analytics.sharpe(rets, bars_per_year), 2),
            "max_drawdown": round(analytics.max_drawdown(eq), 4),
            "hit_rate": round(analytics.hit_rate(rets), 3),
            "universe": ledger.get("universe", []),
            "n_long": last["n_long"],
            "n_short": last["n_short"],
        },
        "equity": [round(eq[i], 5) for i in idx],
        "bench": [round(beq[i], 5) for i in idx] if has_bench else [],
        "dates": [entries[i]["date"] for i in idx],
        "split_frac": ((n - live) / n) if n else 0.0,
        "positions": positions,
        "exposure": _exposure(last["weights"]),
        "recent": [{"date": e["date"], "realized_return": e["realized_return"],
                    "equity": e["equity"]} for e in entries[-20:]][::-1],
    }
