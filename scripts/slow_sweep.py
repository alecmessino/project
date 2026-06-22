"""Slow-sleeve validation sweep: fast book vs slow 40/60 vs slow 35/65.

Runs the cross-sectional book over a long history three ways and reports the after-tax
profile of each, so we can see whether the natively-slow sleeve actually retains more
after-tax return than the fast book — and which buy/hold boundary does best.

Universe: the real 40-year proxy-spliced matrix if the network allows (set SLOW_SWEEP_REAL=1),
otherwise a deterministic synthetic matrix over the same 18 region/size/style tickers with
rotating leadership (a proof-of-mechanism, not real history). Either way the comparison is
apples-to-apples: identical series, only the sleeve config changes.

    python scripts/slow_sweep.py
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import replace
from datetime import date, timedelta

from drift.config import Settings
from drift.cross_section import cross_book_entries
from drift.feed.synthetic import SyntheticFeed
from drift.tax import after_tax_track, gain_profile
from drift.universes import MATRIX

BPY = 252.0
YEARS = 40
N_BARS = YEARS * int(BPY)


def synthetic_universe() -> dict:
    """18-ticker matrix with rotating cross-sectional leadership.

    Each ticker gets a multi-year drift cycle, phase-shifted across the universe, so the
    momentum ranking genuinely rotates over four decades — exactly the regime a fast 60-bar
    signal trades far more often than a 252-bar one."""
    tickers = list(MATRIX)
    block = int(BPY) // 2                 # 6-month regime blocks
    n_blocks = N_BARS // block + 1
    cycle = 8                             # ~4-year leadership cycle
    start = date(1985, 1, 1)
    # Sequential ISO dates so the entries sort chronologically (cross_book_entries sorts
    # asof as strings; SyntheticFeed's default integer-string asofs would scramble the
    # timeline lexicographically — "1002" < "10020" < "1003").
    stamps = [(start + timedelta(days=k)).isoformat() for k in range(N_BARS)]
    series: dict = {}
    for t, tkr in enumerate(tickers):
        phase = 2 * math.pi * t / len(tickers)
        regimes = []
        for k in range(n_blocks):
            drift = 0.16 * math.sin(2 * math.pi * k / cycle + phase) + 0.04
            regimes.append((block, drift))
        feed = SyntheticFeed(instruments=(tkr,), n_bars=N_BARS, bar_vol=0.011,
                             bars_per_year=BPY, regimes=regimes, seed=17 + t)
        series[tkr] = [replace(b, asof=stamps[k]) for k, b in enumerate(feed.series(tkr))]
    return series


def real_universe() -> dict:
    """Best-effort 40-year proxy-spliced history from the Yahoo feed."""
    from drift.tearsheet import _pull
    series, applied = _pull(list(MATRIX), years=float(YEARS), proxies=True)
    if applied:
        print(f"  (proxy-spliced: {', '.join(f'{k}<-{v}' for k, v in applied.items())})")
    return series


def variants(real: bool) -> list[tuple[str, Settings]]:
    fast = Settings.load("config/drift.yaml")
    slow = Settings.load("config/slow.yaml")
    cs35 = slow.cross_section.model_copy(update={"buy_quantile": 0.35, "hold_quantile": 0.65})
    slow35 = slow.model_copy(update={"cross_section": cs35})
    return [("Fast book (vanilla)", fast),
            ("Slow sleeve 40/60", slow),
            ("Slow sleeve 35/65", slow35)]


def row(name: str, settings: Settings, series: dict) -> dict:
    entries = cross_book_entries(series, settings)
    at = after_tax_track(entries, settings.tax, BPY)
    gp = gain_profile(entries, settings.tax.lt_holding_bars, BPY)
    if at is None or gp is None:
        return {"name": name, "ok": False}
    retention = (at.after_tax_return / at.pretax_return) if at.pretax_return else float("nan")
    return {
        "name": name, "ok": True,
        "pretax": at.pretax_return, "aftertax": at.after_tax_return,
        "retention": retention, "drag": at.tax_drag,
        "turnover": at.annual_turnover, "st_share": at.short_term_share,
        "hold_days": at.avg_holding_days or float("nan"),
        "st_real": gp.st_realized, "lt_real": gp.lt_realized,
        "n_entries": len(entries),
    }


def main() -> int:
    use_real = os.environ.get("SLOW_SWEEP_REAL") == "1"
    src = "real (Yahoo, proxy-spliced)"
    series = None
    if use_real:
        try:
            print("Pulling real 40-year history …")
            series = real_universe()
            if not series or len(series) < 8:
                print(f"  only {len(series or {})} names returned — falling back to synthetic")
                series = None
        except Exception as e:  # noqa: BLE001 — network is best-effort
            print(f"  real pull failed ({e!r}) — falling back to synthetic")
            series = None
    if series is None:
        series = synthetic_universe()
        src = "synthetic (deterministic, rotating leadership)"

    yrs = max(len(v) for v in series.values()) / BPY
    print(f"\nUniverse: {len(series)} tickers · ~{yrs:.0f}y · source = {src}\n")

    rows = [row(name, s, series) for name, s in variants(use_real)]

    hdr = f"{'variant':<22}{'pre-tax':>10}{'after-tax':>11}{'retain':>9}{'drag':>8}{'turnov':>9}{'ST%':>7}{'hold(d)':>9}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        if not r["ok"]:
            print(f"{r['name']:<22}  (no after-tax — prices missing)")
            continue
        print(f"{r['name']:<22}"
              f"{r['pretax']*100:>9.1f}%"
              f"{r['aftertax']*100:>10.1f}%"
              f"{r['retention']*100:>8.1f}%"
              f"{r['drag']*100:>7.1f}%"
              f"{r['turnover']*100:>8.0f}%"
              f"{r['st_share']*100:>6.0f}%"
              f"{r['hold_days']:>9.0f}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
