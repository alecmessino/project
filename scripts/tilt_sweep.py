"""Continuous-tilt validation sweep — INTERNAL R&D.

Does it make more sense to hold the WHOLE ETF matrix and tilt weights by signal strength —
rebalancing gently and letting tax-loss harvesting work — than to concentrate in the trending
top half? Concentration captures more of the momentum premium but turns the book over ~13×/yr at
~95% short-term gains, which is exactly the structure the firm's own tax thesis argues against.

This runs the cross-sectional book over a long history four ways on the IDENTICAL series — only the
selection rule changes — and reports the return-vs-tax frontier: pre-tax, AFTER-TAX, Sharpe, max
drawdown, turnover, short-term-gain share, and average names held.

    python scripts/tilt_sweep.py                 # synthetic 18-ticker matrix (mechanism check)
    TILT_SWEEP_REAL=1 python scripts/tilt_sweep.py   # real 40y proxy-spliced matrix (the real test)

IMPORTANT — research artifact, not a result to ship. The tilt overlay (cross_section.tilt_overlay)
is OFF in every committed config; nothing here is wired into the live signal. The synthetic run only
proves the mechanism discriminates; promote a variant to a real sleeve ONLY if the real run shows a
better after-tax, risk-adjusted profile across sub-periods.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import replace
from datetime import date, timedelta

from drift import analytics
from drift.config import Settings
from drift.cross_section import cross_book_entries
from drift.feed.synthetic import SyntheticFeed
from drift.tax import after_tax_track, gain_profile
from drift.universes import MATRIX

BPY = 252.0
YEARS = 40
N_BARS = YEARS * int(BPY)


def synthetic_universe() -> dict:
    """18-ticker matrix with rotating cross-sectional leadership (phase-shifted multi-year drift
    cycles), so the momentum ranking genuinely rotates over four decades. Deterministic; a
    proof-of-mechanism, NOT real history. ISO date stamps so cross_book_entries sorts chronologically."""
    tickers = list(MATRIX)
    block = int(BPY) // 2
    n_blocks = N_BARS // block + 1
    cycle = 8
    start = date(1985, 1, 1)
    stamps = [(start + timedelta(days=k)).isoformat() for k in range(N_BARS)]
    series: dict = {}
    for t, tkr in enumerate(tickers):
        phase = 2 * math.pi * t / len(tickers)
        regimes = [(block, 0.16 * math.sin(2 * math.pi * k / cycle + phase) + 0.04) for k in range(n_blocks)]
        feed = SyntheticFeed(instruments=(tkr,), n_bars=N_BARS, bar_vol=0.011,
                             bars_per_year=BPY, regimes=regimes, seed=17 + t)
        series[tkr] = [replace(b, asof=stamps[k]) for k, b in enumerate(feed.series(tkr))]
    return series


def real_universe() -> dict:
    """Best-effort 40-year proxy-spliced history from the Yahoo feed (the real test)."""
    from drift.tearsheet import _pull
    series, applied = _pull(list(MATRIX), years=float(YEARS), proxies=True)
    if applied:
        print(f"  (proxy-spliced: {', '.join(f'{k}<-{v}' for k, v in applied.items())})")
    return series


def _tilt(base: Settings, k: float, **extra) -> Settings:
    """The live book reconfigured as a full-universe continuous tilt of strength k, plus any extra
    cross-section overrides (the hybrid layers the Tax-Managed Core levers on top)."""
    cs = base.cross_section.model_copy(update={"tilt_overlay": True, "tilt_strength": k, **extra})
    return base.model_copy(update={"cross_section": cs})


def _band(base: Settings, k: float) -> Settings:
    """Tilt + the tax-aware no-trade band only (isolates the band's contribution)."""
    return _tilt(base, k, tax_aware=True, no_trade_band=0.03)


def _hybrid(base: Settings, k: float) -> Settings:
    """The hybrid: continuous tilt + BOTH Tax-Managed Core levers (no-trade band + lot protection)."""
    return _tilt(base, k, tax_aware=True, no_trade_band=0.03, lot_protect=True)


def variants() -> list[tuple[str, Settings]]:
    fast = Settings.load("config/drift.yaml")    # Unconstrained Core Alpha (concentrated, the live book)
    slow = Settings.load("config/slow.yaml")     # Tax-Managed Core (the slow 40/60 predecessor)
    return [
        ("Unconstrained Core", fast),
        ("Tax-Managed Core (slow)", slow),
        ("Tilt k=0.5", _tilt(fast, 0.5)),
        ("Tilt k=0.5 +band", _band(fast, 0.5)),
        ("Tilt k=0.5 +band+lots", _hybrid(fast, 0.5)),
        ("Tilt k=1.0 +band+lots", _hybrid(fast, 1.0)),
    ]


def row(name: str, settings: Settings, series: dict) -> dict:
    entries = cross_book_entries(series, settings)
    at = after_tax_track(entries, settings.tax, BPY)
    gp = gain_profile(entries, settings.tax.lt_holding_bars, BPY)
    if at is None or gp is None:
        return {"name": name, "ok": False}
    eq = [e["equity"] for e in entries]
    rets = [e["realized_return"] for e in entries]
    names = [sum(1 for w in e["weights"].values() if w > 0) for e in entries]
    return {
        "name": name, "ok": True,
        "pretax": at.pretax_return, "aftertax": at.after_tax_return,
        "retention": (at.after_tax_return / at.pretax_return) if at.pretax_return else float("nan"),
        "sharpe": analytics.sharpe(rets, BPY), "maxdd": analytics.max_drawdown(eq),
        "turnover": at.annual_turnover, "st_share": at.short_term_share,
        "avg_names": (sum(names) / len(names)) if names else 0.0,
    }


def main() -> int:
    use_real = os.environ.get("TILT_SWEEP_REAL") == "1"
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
        src = "synthetic (deterministic, rotating leadership — mechanism check, NOT evidence)"

    yrs = max(len(v) for v in series.values()) / BPY
    print(f"\nUniverse: {len(series)} tickers · ~{yrs:.0f}y · source = {src}\n")

    hdr = (f"{'variant':<26}{'pre-tax':>10}{'after-tax':>11}{'retain':>9}{'sharpe':>8}"
           f"{'maxDD':>8}{'turnov':>9}{'ST%':>7}{'names':>7}")
    print(hdr)
    print("-" * len(hdr))
    for name, s in variants():
        r = row(name, s, series)
        if not r["ok"]:
            print(f"{r['name']:<26}  (no after-tax — prices missing)")
            continue
        print(f"{r['name']:<26}"
              f"{r['pretax']*100:>9.1f}%"
              f"{r['aftertax']*100:>10.1f}%"
              f"{r['retention']*100:>8.1f}%"
              f"{r['sharpe']:>8.2f}"
              f"{r['maxdd']*100:>7.1f}%"
              f"{r['turnover']*100:>8.0f}%"
              f"{r['st_share']*100:>6.0f}%"
              f"{r['avg_names']:>7.1f}")
    print("\nRead: 'retain' = after-tax / pre-tax (higher = more tax-efficient). The hybrid "
          "(tilt +band +lots) should keep the broad tilt's Sharpe / shallow drawdown while the band "
          "and lot-protection cut ST% and lift retention toward the Tax-Managed Core — bridging the "
          "risk-vs-tax gap. The +band row isolates the no-trade band; +lots adds lot protection.")
    if not use_real:
        print("SYNTHETIC RUN — proves the mechanism discriminates; NOT evidence on real ETFs.")
    print("Research only — tilt_overlay is OFF in every shipped config and not wired into the live signal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
