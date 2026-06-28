"""Modern-era cost & capacity optimization — INTERNAL R&D.

Sweeps the tilt + lot-protection HYBRID over (k × no-trade-band) on the 2006-present full-universe
window (when all 18 ETFs exist), net of realistic and stressed transaction costs, to find the
(k, band) that maximizes after-tax return and Sharpe while keeping turnover and short-term churn
defensible. Runs OFFLINE from the committed cache (tests/data/matrix_history.json) built by
scripts/tilt_sweep.py — no network.

    python scripts/tilt_optimize.py

Determinism: re-execs with PYTHONHASHSEED=0 so the grid and the chosen optimum are bit-stable (the
lot-protection redistribution iterates sets). Capacity is proxied by elevated flat cost (the engine
has no size-dependent market-impact model). The hybrid flags are research-only and OFF in every
shipped config — nothing here touches the live signal.
"""

from __future__ import annotations

import json
import os
import sys

# Pin the hash seed BEFORE importing the engine, so set-iteration order (and the optimum) is stable.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

from drift import analytics
from drift.config import Settings
from drift.cross_section import cross_book_entries
from drift.models import Bar
from drift.tax import after_tax_track, gain_profile

BPY = 252.0
CACHE_PATH = "tests/data/matrix_history.json"
START = "2006-06"                       # the full-18-ticker (modern ETF) era
K_GRID = [0.3, 0.5, 0.75, 1.0]
BAND_GRID = [0.02, 0.04, 0.06, 0.08, 0.10]
REALISTIC = 5.0                         # bps/side — the shipped, defensible cost for liquid ETFs
STRESS = [5.0, 10.0, 15.0]              # realistic -> larger size / less-liquid (capacity proxy)


def load_cache() -> dict:
    with open(CACHE_PATH) as fh:
        payload = json.load(fh)
    return {t: [Bar(asof=a, close=c) for a, c in zip(d["asof"], d["close"])]
            for t, d in payload["series"].items()}


def slice_from(series: dict, start: str) -> dict:
    return {t: [b for b in bars if b.asof >= start] for t, bars in series.items()}


def _hybrid(k: float, band: float, cost: float) -> Settings:
    fast = Settings.load("config/drift.yaml")
    cs = fast.cross_section.model_copy(update={"tilt_overlay": True, "tilt_strength": k,
                                               "lot_protect": True, "tax_aware": True,
                                               "no_trade_band": band})
    sz = fast.sizing.model_copy(update={"cost_bps_per_side": cost})
    return fast.model_copy(update={"cross_section": cs, "sizing": sz})


def _bench(which: str, cost: float) -> Settings:
    s = Settings.load("config/slow.yaml" if which == "slow" else "config/drift.yaml")
    sz = s.sizing.model_copy(update={"cost_bps_per_side": cost})
    return s.model_copy(update={"sizing": sz})


def metrics(settings: Settings, series: dict) -> dict | None:
    entries = cross_book_entries(series, settings)
    at = after_tax_track(entries, settings.tax, BPY)
    gp = gain_profile(entries, settings.tax.lt_holding_bars, BPY)
    if at is None or gp is None:
        return None
    eq = [e["equity"] for e in entries]
    rets = [e["realized_return"] for e in entries]
    names = [sum(1 for w in e["weights"].values() if w > 0) for e in entries]
    return {"aftertax": at.after_tax_return,
            "retention": (at.after_tax_return / at.pretax_return) if at.pretax_return else float("nan"),
            "sharpe": analytics.sharpe(rets, BPY), "maxdd": analytics.max_drawdown(eq),
            "turnover": at.annual_turnover, "st_share": at.short_term_share,
            "avg_names": (sum(names) / len(names)) if names else 0.0}


def _grid_block(grid: dict, key: str, label: str, scale: float, fmt: str) -> None:
    print(f"--- {label} (rows = k, cols = no-trade band) ---")
    print("  k \\ band" + "".join(f"{b*100:>8.0f}%" for b in BAND_GRID))
    for k in K_GRID:
        cells = []
        for band in BAND_GRID:
            m = grid[(k, band)]
            cells.append(fmt.format(m[key] * scale) if m else "--")
        print(f"{k:>8}  " + "".join(f"{c:>9}" for c in cells))
    print()


def main() -> int:
    series = slice_from(load_cache(), START)
    yrs = max(len(v) for v in series.values()) / BPY
    print(f"Modern-era optimization · window {START} -> present · {len(series)} tickers · ~{yrs:.1f}y")
    print("Deterministic (PYTHONHASHSEED=0). Hybrid = continuous tilt + lot protection + tax-aware band.")
    print("Capacity proxied by cost stress (no impact model). Research only.\n")

    # Full (k × band) grid at the realistic cost.
    grid = {(k, band): metrics(_hybrid(k, band, REALISTIC), series)
            for k in K_GRID for band in BAND_GRID}
    # Benchmarks at every cost level.
    bench = {c: {"fast": metrics(_bench("fast", c), series),
                 "slow": metrics(_bench("slow", c), series)} for c in STRESS}
    sb = bench[REALISTIC]["slow"]
    fb = bench[REALISTIC]["fast"]

    print(f"=== Benchmarks on this window (cost {REALISTIC:.0f} bps/side) ===")
    for nm, m in (("Unconstrained Core (live)", fb), ("Tax-Managed Core (slow)", sb)):
        print(f"  {nm:<27} after-tax {m['aftertax']*100:7.1f}%  retain {m['retention']*100:5.1f}%  "
              f"sharpe {m['sharpe']:.2f}  maxDD {m['maxdd']*100:4.1f}%  turn {m['turnover']*100:4.0f}%  "
              f"ST {m['st_share']*100:3.0f}%  names {m['avg_names']:.1f}")
    print()

    _grid_block(grid, "aftertax", "AFTER-TAX RETURN %", 100.0, "{:.0f}%")
    _grid_block(grid, "sharpe", "SHARPE", 1.0, "{:.2f}")
    _grid_block(grid, "turnover", "TURNOVER %", 100.0, "{:.0f}%")
    _grid_block(grid, "st_share", "SHORT-TERM SHARE %", 100.0, "{:.0f}%")

    # Selection: max after-tax subject to turnover <= slow book and ST% <= 50%; sharpe tiebreak.
    cells = [(k, b, m) for (k, b), m in grid.items() if m]
    defensible = [c for c in cells if c[2]["turnover"] <= sb["turnover"] and c[2]["st_share"] <= 0.50]
    chosen = max(defensible, key=lambda c: (c[2]["aftertax"], c[2]["sharpe"])) if defensible else None
    max_at = max(cells, key=lambda c: c[2]["aftertax"])
    max_sh = max(cells, key=lambda c: c[2]["sharpe"])

    print("=== OPTIMUM (cost 5 bps/side) ===")
    print(f"  Rule: max after-tax  s.t.  turnover <= slow ({sb['turnover']*100:.0f}%)  and  ST% <= 50%;  sharpe tiebreak.")
    if chosen:
        k, b, m = chosen
        print(f"  CHOSEN  k={k}  band={b*100:.0f}%  ->  after-tax {m['aftertax']*100:.1f}%  "
              f"sharpe {m['sharpe']:.2f}  maxDD {m['maxdd']*100:.1f}%  turn {m['turnover']*100:.0f}%  "
              f"ST {m['st_share']*100:.0f}%  names {m['avg_names']:.1f}")
        print(f"    vs Tax-Managed Core (slow): after-tax {sb['aftertax']*100:.1f}%  sharpe {sb['sharpe']:.2f}  "
              f"turn {sb['turnover']*100:.0f}%  ST {sb['st_share']*100:.0f}%")
    else:
        print("  No cell satisfies the defensibility constraints.")
    print(f"  frontier · max after-tax: k={max_at[0]} band={max_at[1]*100:.0f}% -> {max_at[2]['aftertax']*100:.1f}% "
          f"(turn {max_at[2]['turnover']*100:.0f}%, ST {max_at[2]['st_share']*100:.0f}%)")
    print(f"  frontier · max sharpe   : k={max_sh[0]} band={max_sh[1]*100:.0f}% -> {max_sh[2]['sharpe']:.2f} "
          f"(after-tax {max_sh[2]['aftertax']*100:.1f}%)")
    print()

    # Does the chosen cell's edge survive elevated (capacity-stress) cost?
    if chosen:
        k, b, _ = chosen
        print(f"=== Cost / capacity survival of the chosen cell (k={k}, band={b*100:.0f}%) ===")
        print(f"{'cost bps/side':<15}{'after-tax':>11}{'sharpe':>9}{'turn':>7}{'Δ after-tax vs slow':>22}")
        for c in STRESS:
            m = grid[(k, b)] if c == REALISTIC else metrics(_hybrid(k, b, c), series)
            sm = bench[c]["slow"]
            print(f"{c:<15.0f}{m['aftertax']*100:>10.1f}%{m['sharpe']:>9.2f}{m['turnover']*100:>6.0f}%"
                  f"{(m['aftertax']-sm['aftertax'])*100:>21.1f}%")
    print("\nResearch only — tilt_overlay / lot_protect are OFF in every shipped config and not wired "
          "into the live signal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
