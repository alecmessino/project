#!/usr/bin/env python3
"""Conditional under-reaction — does the Over edge appear only in hitter-friendly context?

Our context-FREE tests found the early-explosion and drop-reversion Over patterns ~break-
even. But bets aren't placed blind: weather (wind out / heat) and park drive scoring, and
books may not fully price them live. This splits both patterns by hitter-friendly context
(wind blowing out, temp >= 85F, or park factor >= 103) and grades the Over at the real
live line. If the edge concentrates in the hitter-friendly slice, that's a conditional
calibration error the context-free tests washed out.

    python the_third_turn/context_study.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from features import CACHE, build  # noqa: E402
from investigate_line_edge import BREAKEVEN, WIN_PAYOUT, wilson_interval  # noqa: E402

console = Console()


def hitter_friendly(r):
    w = r.get("weather", {}) or {}
    return (w.get("wind_signed", 0) > 0) or (w.get("temp") or 0) >= 85 or r.get("park_factor", 100) >= 103


def over_row(t, label, games, linekey):
    picks = [r for r in games if r.get(linekey) is not None and r["final"] != r[linekey]]
    n = len(picks)
    w = sum(1 for r in picks if r["final"] > r[linekey])
    if not n:
        t.add_row(label, "0", "—", "—", "—"); return
    hit = w / n
    lo, hi = wilson_interval(w, n)
    col = "[green]" if lo > BREAKEVEN else ("[yellow]" if hit > BREAKEVEN else "[red]")
    t.add_row(label, str(n), f"{col}{100*hit:.0f}%[/]", f"{100*lo:.0f}-{100*hi:.0f}",
              f"{w*WIN_PAYOUT-(n-w):+.1f}")


def main() -> int:
    cache = build()
    recs = []
    for r in cache.values():
        if r.get("final") is None or not r.get("closing"):
            continue
        r["line1"] = r.get("line_by_inn", {}).get("1")
        r["line3"] = r.get("line_by_inn", {}).get("3")
        r["hf"] = hitter_friendly(r)
        recs.append(r)
    hf = [r for r in recs if r["hf"]]
    console.rule(f"[bold]Conditional under-reaction · {len(recs)} games "
                 f"({len(hf)} hitter-friendly: wind-out / ≥85°F / park≥103)")
    console.print(f"[dim]Bet the Over at the real live line. green = CI clears breakeven "
                  f"({100*BREAKEVEN:.1f}%). If the edge lives in the hitter-friendly split, the "
                  f"context-free wash was hiding it.[/]\n")

    # sanity: does hitter-friendly context alone beat the live line? (all games)
    t0 = Table(title="Baseline — Over at end-of-1st line, ALL games")
    for c in ("split", "games", "Over hit%", "95% CI", "units"):
        t0.add_column(c, justify="left" if c == "split" else "right")
    over_row(t0, "hitter-friendly", [r for r in recs if r["hf"]], "line1")
    over_row(t0, "neutral/pitcher", [r for r in recs if not r["hf"]], "line1")
    console.print(t0)

    t1 = Table(title="Early explosion (2+ runs in 1st) → Over at post-1st line, by context")
    for c in ("split", "games", "Over hit%", "95% CI", "units"):
        t1.add_column(c, justify="left" if c == "split" else "right")
    exp = [r for r in recs if r["first_inning_runs"] >= 2]
    over_row(t1, "hitter-friendly", [r for r in exp if r["hf"]], "line1")
    over_row(t1, "neutral/pitcher", [r for r in exp if not r["hf"]], "line1")
    console.print(t1)

    t2 = Table(title="Drop-reversion (line fell by 3rd) → Over at end-of-3rd line, by context")
    for c in ("split", "games", "Over hit%", "95% CI", "units"):
        t2.add_column(c, justify="left" if c == "split" else "right")
    drop = [r for r in recs if r["line3"] is not None and r["line3"] < r["closing"]]
    over_row(t2, "hitter-friendly", [r for r in drop if r["hf"]], "line3")
    over_row(t2, "neutral/pitcher", [r for r in drop if not r["hf"]], "line3")
    console.print(t2)

    console.print("\n[dim]Small subsets — read the CIs. A green (CI clears breakeven) hitter-friendly "
                  "cell would be the first conditional edge; anything else says the market prices the "
                  "context too.[/]")
    (Path(CACHE).parent / "context_study.json").write_text(json.dumps({
        "n": len(recs), "n_hf": len(hf)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
