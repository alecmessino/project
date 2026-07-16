"""One canonical, dated portfolio state, every research page projects from this.

The Model Portfolio ledger (`docs/ledger.json`, append-only) is the single source of truth for the
**Core Alpha** book. This module turns it into ONE object; the operational dashboard (`equities.html`)
and the historical ledger page (`ledger.html`) are both thin projections of it, so their universe,
date, holdings and weights agree **by construction**, no more three-universes / three-weights /
"held 8 vs 9" contradictions.

Three DISTINCT weight-like fields, never conflated (the old code reused the word "weight" for all three):

  * ``portfolio_weight``, the allocation the book actually holds (``entries[-1].weights``).
  * ``signal_strength`` , the volatility-normalized trend z-score (the ranking); context, not allocation.
  * ``target_weight``   , per-name single-name sizing; a research-only concept, NOT surfaced here.

``signal_strength`` is single-sourced from the ledger: preferring a persisted ``entry["signals"]`` when
present, else reconstructed from the ledger's own per-session marking ``prices``, so it is computed over
exactly the book's universe and dates, with no independent data fetch.
"""

from __future__ import annotations

from typing import Optional

from . import signal as sig
from . import sizing
from .config import Settings, TaxSettings
from .exhibit import blotter_from_entries
from .ledger import build_ledger_state

CANON_VERSION = 1

# The six operational statuses an advisor reads off the book. Membership-driven (never a fresh
# recompute), so a name can never read both "held" and "waiting".
#   in book  + last-turn action  -> Buy(NEW) / Increase(ADD) / Reduce(TRIM) / Hold(untouched)
#   not held + EXIT              -> Sell (it just left the book; shown in the rebalance panel)
#   not held +,                 -> Waiting (a universe member below the cut)
_IN_BOOK_STATUS = {"NEW": "Buy", "ADD": "Increase", "TRIM": "Reduce"}


def _status(action: Optional[str], in_book: bool) -> str:
    if in_book:
        return _IN_BOOK_STATUS.get(action or "", "Hold")
    return "Sell" if action == "EXIT" else "Waiting"


def _reconstruct_closes(entries: list[dict], universe: list[str]) -> dict[str, list[float]]:
    """Per-name close series from the ledger's persisted marking prices (offline, no data fetch)."""
    closes: dict[str, list[float]] = {i: [] for i in universe}
    for e in entries:
        pr = e.get("prices") or {}
        for i in universe:
            v = pr.get(i)
            if v is not None:
                closes[i].append(v)
    return closes


def _signal_map(ledger: dict, settings: Settings) -> dict[str, tuple[float, Optional[float]]]:
    """{instrument: (signal_strength z, annualized_vol)} over the book's own universe/dates.

    Prefers a persisted ``entries[-1]["signals"]`` (exact, written at ledger-build time); falls back
    to reconstructing the trend z from the ledger's marking ``prices`` so a pre-``signals`` ledger
    still renders.
    """
    entries = ledger.get("entries", [])
    universe = list(ledger.get("universe", []))
    last = entries[-1] if entries else {}
    persisted = last.get("signals") or {}
    sg = settings.signal
    bpy = settings.engine.bars_per_year
    if persisted:
        return {i: (round(persisted[i].get("z", 0.0), 4), persisted[i].get("vol"))
                for i in universe if i in persisted}
    closes = _reconstruct_closes(entries, universe)
    out: dict[str, tuple[float, Optional[float]]] = {}
    for i in universe:
        cl = closes.get(i, [])
        z = sig.momentum_score(cl, sg.lookback, sg.vol_window) if len(cl) > sg.lookback else 0.0
        vol = (sizing.annualize_vol(sig.realized_vol(cl, sg.vol_window), bpy)
               if len(cl) > 2 else None)
        out[i] = (round(z, 4), round(vol, 4) if vol else None)
    return out


def build_portfolio_state(ledger: dict, settings: Settings,
                          tax: Optional[TaxSettings] = None) -> dict:
    """The one canonical object every research page projects from. Pure; no network, no series fetch."""
    entries = ledger.get("entries", [])
    universe = list(ledger.get("universe", []))
    last = entries[-1] if entries else {}
    weights = last.get("weights", {}) or {}
    sigmap = _signal_map(ledger, settings)
    # The full dated track needs the marking fields (realized_return/equity). A partial/legacy ledger
    # (e.g. weights-only) still projects its holdings + rebalance; it just carries no performance chart.
    if entries and "realized_return" in entries[-1]:
        performance = build_ledger_state(ledger, settings.engine.bars_per_year, tax)
    else:
        performance = {"header": {}, "equity": [], "dates": [], "benchmarks": [], "exposure": None}

    blot = blotter_from_entries(entries)
    action_by = {t["instrument"]: t["action"] for t in (blot["trades"] if blot else [])}
    if blot:                                    # annotate each trade with its operational status
        for t in blot["trades"]:
            t["status"] = _status(t["action"], weights.get(t["instrument"], 0.0) > 0)
        blot.setdefault("book", "ledger")

    holdings, watch = [], []
    for i in universe:
        w = round(weights.get(i, 0.0), 4)
        z, vol = sigmap.get(i, (0.0, None))
        in_book = w > 0
        row = {"instrument": i, "portfolio_weight": w, "signal_strength": z,
               "ann_vol": vol, "leg": "LONG" if w > 0 else ("SHORT" if w < 0 else "—"),
               "status": _status(action_by.get(i), in_book)}
        (holdings if in_book else watch).append(row)
    holdings.sort(key=lambda r: -r["portfolio_weight"])
    watch.sort(key=lambda r: -r["signal_strength"])

    cost_side = ledger.get("cost_bps_per_side")
    return {
        "version": CANON_VERSION,
        "date": last.get("date", ""),
        "universe": universe,
        "holdings": holdings,
        "watch": watch,
        "rebalance": blot,
        "performance": performance,
        "cost": {
            "bps_per_side": cost_side,
            "bps_roundtrip": (round(cost_side * 2, 1) if cost_side is not None else None),
            "rebalance_bars": ledger.get("rebalance_bars"),
        },
    }


def dashboard_projection(canon: dict) -> dict:
    """Operational OMS view (`equities.html`): current holdings + signals + status, the last
    rebalance in/out, and one dated performance chart. Nothing an advisor doesn't act on."""
    perf = canon["performance"]
    ph = perf.get("header", {})
    return {
        "version": canon["version"],
        "date": canon["date"],
        "header": {
            "n_universe": len(canon["universe"]),
            "n_held": len(canon["holdings"]),
            "data_through": canon["date"],
            "generated": ph.get("updated", ""),
            "rebalance_bars": canon["cost"].get("rebalance_bars"),
            "cost_bps_roundtrip": canon["cost"].get("bps_roundtrip"),
        },
        "holdings": canon["holdings"],
        "watch": canon["watch"],
        "rebalance": canon["rebalance"],
        # `blotter` alias: the single-sourced "trades the book just made" (book == "ledger").
        "blotter": canon["rebalance"],
        "performance": {
            "equity": perf.get("equity", []),
            "dates": perf.get("dates", []),
            "benchmarks": perf.get("benchmarks", []),
            "header": ph,
        },
        "exposure": perf.get("exposure"),
        "cost": canon["cost"],
    }
