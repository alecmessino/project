"""Nightly signal persistence + backtest ledger.

Appends one row per (date, symbol) each night so a real, auditable
backtest ledger accumulates over time. No fabricated history.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional


LEDGER_DIR = Path(__file__).resolve().parent / "ledger"
LEDGER_CSV = LEDGER_DIR / "signals.csv"
LEDGER_JSON = LEDGER_DIR / "signals.json"


@dataclass
class SignalRow:
    date: str            # ISO date (nightly snapshot)
    symbol: str
    name: str
    price: float
    market_cap: float
    turnover_pct: float
    erosion_ratio: float
    conviction: int
    signal: str
    # Filled in later by the backtest step once 30/90d have elapsed:
    roi_30d: Optional[float] = None
    roi_90d: Optional[float] = None
    survived: Optional[bool] = None

    def to_dict(self) -> dict:
        return asdict(self)


_FIELDS = ["date", "symbol", "name", "price", "market_cap", "turnover_pct",
           "erosion_ratio", "conviction", "signal", "roi_30d", "roi_90d", "survived"]


def _ensure_dir() -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)


def append_signals(rows: list[SignalRow]) -> int:
    """Append nightly signal rows to the ledger. Returns rows written."""
    if not rows:
        return 0
    _ensure_dir()
    exists = LEDGER_CSV.exists()
    with LEDGER_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r.to_dict())
    _rewrite_json()
    return len(rows)


def load_all() -> list[SignalRow]:
    if not LEDGER_CSV.exists():
        return []
    out = []
    with LEDGER_CSV.open(newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            out.append(SignalRow(
                date=d["date"], symbol=d["symbol"], name=d["name"],
                price=float(d["price"] or 0), market_cap=float(d["market_cap"] or 0),
                turnover_pct=float(d["turnover_pct"] or 0),
                erosion_ratio=float(d["erosion_ratio"] or 0),
                conviction=int(d["conviction"] or 0), signal=d["signal"],
                roi_30d=(float(d["roi_30d"]) if d.get("roi_30d") not in (None, "", "None") else None),
                roi_90d=(float(d["roi_90d"]) if d.get("roi_90d") not in (None, "", "None") else None),
                survived=(d["survived"] == "True" if d.get("survived") not in (None,"","None") else None),
            ))
    return out


def _rewrite_json() -> None:
    rows = load_all()
    # Summary by conviction decile
    deciles: dict[int, dict] = {i: {"count": 0, "survived": 0, "roi_30d": [], "roi_90d": []}
                                for i in range(1, 11)}
    for r in rows:
        if r.conviction is None:
            continue
        dec = max(1, min(10, (r.conviction // 10) + 1))
        d = deciles[dec]
        d["count"] += 1
        if r.survived:
            d["survived"] += 1
        if r.roi_30d is not None:
            d["roi_30d"].append(r.roi_30d)
        if r.roi_90d is not None:
            d["roi_90d"].append(r.roi_90d)

    summary = {
        "total_signals": len(rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "by_decile": {
            str(k): {
                "count": v["count"],
                "survived": v["survived"],
                "win_rate": round(v["survived"] / v["count"], 3) if v["count"] else 0,
                "avg_roi_30d": round(sum(v["roi_30d"]) / len(v["roi_30d"]), 3) if v["roi_30d"] else None,
                "avg_roi_90d": round(sum(v["roi_90d"]) / len(v["roi_90d"]), 3) if v["roi_90d"] else None,
            } for k, v in deciles.items()
        },
        "rows": [r.to_dict() for r in rows],
    }
    with LEDGER_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def update_backtest_results(reference: dict[str, float]) -> int:
    """Backfill roi_30d/roi_90d/survived by comparing entry price to later prices.

    `reference` maps symbol -> current price. For each row whose roi is still
    None and whose snapshot date is >= 30/90 days old, compute ROI.
    Returns number of rows updated.
    """
    rows = load_all()
    if not rows:
        return 0
    today = date.today()
    updated = 0
    for r in rows:
        cur = reference.get(r.symbol.upper())
        if cur is None or r.price in (None, 0):
            continue
        age_days = (today - date.fromisoformat(r.date)).days
        roi = (cur - r.price) / r.price
        if r.roi_30d is None and age_days >= 30:
            r.roi_30d = round(roi * 100, 2)
            updated += 1
        if r.roi_90d is None and age_days >= 90:
            r.roi_90d = round(roi * 100, 2)
            r.survived = cur > 0
            updated += 1
    if updated:
        _ensure_dir()
        with LEDGER_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r.to_dict())
        _rewrite_json()
    return updated
