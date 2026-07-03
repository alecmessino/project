#!/usr/bin/env python3
"""Vector 2 — the early-runs "anchoring bias" test.

When 2+ runs score in the 1st, the live total jumps (pregame 9.0 → 10.5). Does the
market UNDER-react (early explosion → early bullpen → cascading scoring → Over cashes)
or OVER-react (fluky sequencing settles down → Under cashes)? And does the answer split
by CAUSE — real contact (hits) vs cheap runs (walks/errors)?

We bet at the live total at the END OF THE 1st and grade on the final. Sliced by cause,
with a no-explosion control and the standard robustness note.

    python the_third_turn/v2_early_runs.py
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


def grade(rows, over):
    dec = [r for r in rows if r["final"] != r["line1"]]
    w = sum(1 for r in dec if (r["final"] > r["line1"]) == over)
    n = len(dec)
    if not n:
        return None
    lo, hi = wilson_interval(w, n)
    return {"n": n, "hit": w / n, "lo": lo, "hi": hi, "units": w * WIN_PAYOUT - (n - w),
            "climb": sum(r["line1"] - r["closing"] for r in rows) / len(rows),
            "resid": sum(r["final"] - r["line1"] for r in rows) / len(rows)}


def row(t, label, r):
    if r is None:
        t.add_row(label, "0", "—", "—", "—", "—", "—"); return
    col = "[green]" if r["lo"] > BREAKEVEN else ("[yellow]" if r["hit"] > BREAKEVEN else "[red]")
    t.add_row(label, str(r["n"]), f"{col}{100*r['hit']:.0f}%[/]",
              f"{100*r['lo']:.0f}-{100*r['hi']:.0f}", f"{r['units']:+.1f}",
              f"{r['climb']:+.2f}", f"{r['resid']:+.2f}")


def main() -> int:
    cache = build()
    recs = []
    for r in cache.values():
        line1 = r.get("line_by_inn", {}).get("1")
        if r.get("final") is None or line1 is None or not r.get("closing"):
            continue
        recs.append({**r, "line1": line1})

    explosion = [r for r in recs if r["first_inning_runs"] >= 2]
    quiet = [r for r in recs if r["first_inning_runs"] < 2]
    # cause split within the explosion set: were the early runs mostly real contact?
    hit_driven = [r for r in explosion if r["cause1"]["hit"] > (r["cause1"]["walk"] + r["cause1"]["error"])]
    cheap = [r for r in explosion if r["cause1"]["hit"] <= (r["cause1"]["walk"] + r["cause1"]["error"])]

    console.rule(f"[bold]Vector 2 · early-runs anchoring · {len(recs)} games "
                 f"({len(explosion)} with 2+ in the 1st)")
    console.print(f"[dim]Bet at the live total at the END of the 1st. breakeven {100*BREAKEVEN:.1f}%. "
                  f"climb = how much the line rose vs pregame · resid = final − the line you bet "
                  f"(+ = market set it too low → Over; − = too high → Under).[/]\n")

    t = Table(title="OVER vs UNDER at the post-1st line")
    for c in ("segment", "games", "OVER hit", "O CI", "O units", "avg climb", "avg resid"):
        t.add_column(c, justify="left" if c == "segment" else "right")
    row(t, "2+ runs (all)", grade(explosion, True))
    row(t, "  ├ hit-driven", grade(hit_driven, True))
    row(t, "  └ cheap (walk/err)", grade(cheap, True))
    row(t, "control: <2 runs", grade(quiet, True))
    console.print(t)

    t2 = Table(title="…same segments, the UNDER side")
    for c in ("segment", "games", "UNDER hit", "U CI", "U units", "avg climb", "avg resid"):
        t2.add_column(c, justify="left" if c == "segment" else "right")
    row(t2, "2+ runs (all)", grade(explosion, False))
    row(t2, "  ├ hit-driven", grade(hit_driven, False))
    row(t2, "  └ cheap (walk/err)", grade(cheap, False))
    row(t2, "control: <2 runs", grade(quiet, False))
    console.print(t2)

    console.print("\n[dim]Under-reaction (bet Over) shows as resid > 0 AND Over hit > breakeven; "
                  "over-reaction (bet Under) as resid < 0 AND Under hit > breakeven. Small n per "
                  "cause slice — read the CIs.[/]")

    (Path(CACHE).parent / "v2_early_runs.json").write_text(json.dumps({
        "explosion": grade(explosion, True), "hit_driven": grade(hit_driven, True),
        "cheap": grade(cheap, True), "control": grade(quiet, True)}, indent=2, default=lambda x: x))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
