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

from .backtest import current_weight
from .config import Settings
from .models import Bar


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
                  seed: bool = False) -> dict:
    """Append one session to the ledger for the latest date. Idempotent: a date
    already recorded (or no fresh bar) is a no-op."""
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

    # 1) Realize the previously-held book from the prior date to now.
    realized = 0.0
    if prev:
        marks = []
        for i in insts:
            p_prev = _close_on_or_before(series[i], prev["date"])
            p_now = series[i][-1].close
            if p_prev and p_now:
                marks.append(prev_w.get(i, 0.0) * (p_now / p_prev - 1.0))
        realized = sum(marks) / len(marks) if marks else 0.0

    # 2) Decide the new target book to carry forward.
    new_w = {i: round(current_weight(i, series[i], prev_w.get(i, 0.0), settings), 4)
             for i in insts}

    # 3) Cost on the rebalance, equal-weight book accounting.
    turnover = sum(abs(new_w[i] - prev_w.get(i, 0.0)) for i in insts) / len(insts)
    net = realized - cost * turnover
    equity = round(equity * (1.0 + net), 6)

    entries.append({
        "date": latest[:10],
        "weights": new_w,
        "realized_return": round(net, 6),
        "equity": equity,
        "n_long": sum(1 for v in new_w.values() if v > 0),
        "n_short": sum(1 for v in new_w.values() if v < 0),
        "seed": bool(seed),
    })
    ledger["universe"] = insts
    ledger["inception"] = ledger.get("inception") or entries[0]["date"]
    ledger["updated"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return ledger


def seed_ledger(series: dict[str, list[Bar]], settings: Settings, sessions: int = 120) -> dict:
    """Bootstrap a ledger by replaying the last `sessions` trading days walk-forward.

    This is a faithful out-of-sample replay (each step sees only data up to that
    date — no lookahead), so the inception curve is meaningful rather than empty.
    Live runs append the newest day on top via `update_ledger`.
    """
    ledger = new_ledger()
    all_dates = sorted({b.asof[:10] for bars in series.values() for b in bars})
    for d in all_dates[-sessions:]:
        sub = {i: [b for b in bars if b.asof[:10] <= d] for i, bars in series.items()}
        update_ledger(ledger, sub, settings, seed=True)
    return ledger


def build_ledger_state(ledger: dict) -> dict:
    """Shape the ledger into the dashboard/exhibit state."""
    entries = ledger.get("entries", [])
    if not entries:
        return {"header": {"days": 0, "inception": "", "total_return": 0.0,
                           "universe": ledger.get("universe", [])},
                "equity": [], "dates": [], "positions": [], "recent": []}
    eq = [e["equity"] for e in entries]
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
            "universe": ledger.get("universe", []),
            "n_long": last["n_long"],
            "n_short": last["n_short"],
        },
        "equity": [round(eq[i], 5) for i in idx],
        "dates": [entries[i]["date"] for i in idx],
        "split_frac": ((n - live) / n) if n else 0.0,
        "positions": positions,
        "recent": [{"date": e["date"], "realized_return": e["realized_return"],
                    "equity": e["equity"]} for e in entries[-20:]][::-1],
    }
