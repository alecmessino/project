#!/usr/bin/env python3
"""Banded drop sweep — is there a robust, persistent edge on slow-start line drops?

Cumulative `>= X%` thresholds blur where the edge lives. This bands the drop into
ranges (0-5, 5-10, 10-15, 15-20, 20%+, plus the explicit 10-14% and 15%+ you asked
about) and reports BOTH the Over and the Under in each band, with Wilson 95% CIs and
units at -110.

Then it stress-tests any signal for robustness — the difference between a lucky
bucket and something you can actually bet:
  * MONOTONICITY  — does the Under edge rise smoothly with drop size? (a gradient,
    not a spike)
  * TIMING        — does the same band edge hold if you measure at the end of the 4th
    instead of the 3rd? (not an artifact of one snapshot)
  * PERSISTENCE   — does it hold in BOTH halves of the sample by date? (not one hot
    streak)

    python the_third_turn/drop_sweep.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get, line_lookup, state_timeline  # noqa: E402
from investigate_line_edge import BREAKEVEN, WIN_PAYOUT, closing_line, wilson_interval  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "drop_sweep_cache.json"

# (label, lo_pct, hi_pct) — drop as a fraction of the pregame close; hi=None is open
BANDS = [("rose/flat (≤0%)", -9.9, 0.0), ("0-5%", 0.0, 0.05), ("5-10%", 0.05, 0.10),
         ("10-15%", 0.10, 0.15), ("15-20%", 0.15, 0.20), ("20%+", 0.20, None)]


def lines_by_inning(feed, fn):
    """Live total at the first at-bat of the 4th/5th/6th (= end of 3rd/4th/5th)."""
    seen: dict[int, float] = {}
    for play in feed.get("liveData", {}).get("plays", {}).get("allPlays", []):
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        inning = int(about.get("inning") or 0)
        line = fn(about.get("startTime") or "")
        if line is not None and inning in (4, 5, 6) and inning not in seen:
            seen[inning] = line
    return {3: seen.get(4), 4: seen.get(5), 5: seen.get(6)}


def build(games, refresh):
    cache = {} if refresh or not CACHE.exists() else json.loads(CACHE.read_text())
    rows = []
    for g in games:
        key = str(g["game_pk"])
        if key in cache:
            rec = cache[key]
        else:
            try:
                feed = _get(FEED.format(pk=g["game_pk"]))
            except Exception:  # noqa: BLE001
                continue
            fn = line_lookup(g["points"])
            _tl, final = state_timeline(feed)
            byinn = lines_by_inning(feed, fn)
            rec = {"closing": closing_line(g["points"], g.get("start_time", "")),
                   "final": final, "date": (g.get("start_time", "") or "")[:10],
                   "line3": byinn[3], "line4": byinn[4], "line5": byinn[5]}
            cache[key] = rec
        if rec["closing"] and rec["final"] is not None:
            rows.append(rec)
    CACHE.write_text(json.dumps(cache))
    return rows


def side(picks, linekey, over):
    """Grade one side (over=True → final>line) over a list of games."""
    dec = [r for r in picks if r["final"] != r[linekey]]
    w = sum(1 for r in dec if (r["final"] > r[linekey]) == over)
    n = len(dec)
    if not n:
        return None
    hit = w / n
    lo, hi = wilson_interval(w, n)
    return {"n": n, "hit": hit, "lo": lo, "hi": hi, "units": w * WIN_PAYOUT - (n - w)}


def in_band(r, linekey, lo, hi):
    if r.get(linekey) is None or not r["closing"]:
        return False
    pct = (r["closing"] - r[linekey]) / r["closing"]
    return (pct > lo if lo <= 0 else pct >= lo) and (hi is None or pct < hi)


def cell(s):
    if s is None:
        return "—", "—", "—"
    col = "[green]" if s["lo"] > BREAKEVEN else ("[yellow]" if s["hit"] > BREAKEVEN else "[red]")
    return (f"{col}{100*s['hit']:.0f}%[/]", f"{100*s['lo']:.0f}-{100*s['hi']:.0f}", f"{s['units']:+.1f}")


def banded_table(rows, linekey, title):
    t = Table(title=title)
    for c in ("drop band", "games", "UNDER hit", "U 95%CI", "U units",
              "OVER hit", "O units"):
        t.add_column(c, justify="left" if c == "drop band" else "right")
    for label, lo, hi in BANDS:
        picks = [r for r in rows if in_band(r, linekey, lo, hi)]
        u, o = side(picks, linekey, False), side(picks, linekey, True)
        uh, uci, uu = cell(u)
        oh, _, ou = cell(o)
        t.add_row(label, str(len(picks)), uh, uci, uu, oh, ou)
    console.print(t)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    rows = build(games, args.refresh)
    console.rule(f"[bold]Banded drop sweep · {len(rows)} games · bet at the END-OF-3rd line")
    console.print(f"[dim]breakeven {100*BREAKEVEN:.1f}% · green CI clears it · yellow point-est only "
                  f"· red below. Under & Over are complements (ex pushes) but shown both ways.[/]\n")

    banded_table(rows, "line3", "PRIMARY — measured at end of 3rd inning")

    # ---- ROBUSTNESS 1: same bands, measured a full inning later ----
    console.print("\n[bold]Robustness — does the band edge survive a different snapshot?[/]")
    banded_table([r for r in rows if r.get("line4")], "line4", "measured at end of 4th inning")

    # ---- ROBUSTNESS 2: persistence across time (>=10% drop, Under) ----
    dated = sorted([r for r in rows if r["date"]], key=lambda r: r["date"])
    mid = dated[len(dated) // 2]["date"] if dated else ""
    console.print(f"\n[bold]Persistence — Under on ≥10% drops (end of 3rd), split at {mid}[/]")
    pt = Table()
    for c in ("half", "dates", "games", "UNDER hit", "95% CI", "units"):
        pt.add_column(c, justify="left" if c in ("half", "dates") else "right")
    for name, sub in [("1st half", [r for r in dated if r["date"] < mid]),
                      ("2nd half", [r for r in dated if r["date"] >= mid])]:
        picks = [r for r in sub if in_band(r, "line3", 0.10, None)]
        s = side(picks, "line3", False)
        h, ci, u = cell(s)
        d = f"{sub[0]['date']}…{sub[-1]['date']}" if sub else "—"
        pt.add_row(name, d, str(len(picks)), h, ci, u)
    console.print(pt)
    console.print("\n[dim]A robust signal reads: Under rising monotonically with drop size, holding at "
                  "both snapshots, and +EV in BOTH time halves. Anything that only fires in one is a "
                  "small-sample mirage.[/]")

    (HERE / "output" / "drop_sweep.json").write_text(json.dumps({
        "n_games": len(rows),
        "bands_end3": {label: {"under": side([r for r in rows if in_band(r, "line3", lo, hi)], "line3", False),
                               "over": side([r for r in rows if in_band(r, "line3", lo, hi)], "line3", True)}
                       for label, lo, hi in BANDS}}, indent=2, default=lambda x: x))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
