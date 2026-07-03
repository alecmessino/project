#!/usr/bin/env python3
"""The SIMPLE rule, tested on everything — no engineering.

Your rule, stated plainly: the pregame total drops on a slow start; by ~3 innings the
live total is down X% (e.g. 9 → 7). Bet the Over at that dropped number. Does it win
over a large sample?

This tests exactly that and nothing else. No times-through-order, no starter tier, no
bullpen, no edge gate. For every game: take the live total at the end of the 3rd
inning, compare it to the pregame close, and if it dropped by at least the threshold,
bet the Over at that live number and grade on the final. One bucket per threshold,
all games, with Wilson 95% CIs so we can see what's signal and what's sample size.

    python the_third_turn/simple_drop_test.py
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
CACHE = HERE / "output" / "simple_drop_cache.json"
PCT_THRESHOLDS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
RUN_THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5]


def line_after_third(feed, fn):
    """Live total at the end of the 3rd inning (first at-bat of the 4th), and the
    trough line through 3. None if the game never reached the 4th."""
    entering_4th = None
    trough = None
    for play in feed.get("liveData", {}).get("plays", {}).get("allPlays", []):
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        inning = int(about.get("inning") or 0)
        line = fn(about.get("startTime") or "")
        if line is None:
            continue
        if inning <= 3:
            trough = line if trough is None else min(trough, line)
        if inning >= 4 and entering_4th is None:
            entering_4th = line
    return entering_4th, trough


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
            closing = closing_line(g["points"], g.get("start_time", ""))
            e3, trough = line_after_third(feed, fn)
            rec = {"closing": closing, "final": final, "line3": e3, "trough3": trough}
            cache[key] = rec
        if rec["closing"] and rec["final"] is not None and rec["line3"] is not None:
            rows.append(rec)
    CACHE.write_text(json.dumps(cache))
    return rows


def grade(rows, key, thresholds, as_pct):
    """Bet Over at the line3 number for games whose drop clears each threshold."""
    out = []
    for thr in thresholds:
        picks = []
        for r in rows:
            drop = r["closing"] - r[key]
            if drop <= 0:
                continue
            metric = drop / r["closing"] if as_pct else drop
            if metric >= thr:
                picks.append(r)
        n = len(picks)
        wins = sum(1 for r in picks if r["final"] > r[key])
        pushes = sum(1 for r in picks if r["final"] == r[key])
        dec = n - pushes
        hit = wins / dec if dec else 0.0
        lo, hi = wilson_interval(wins, dec) if dec else (0.0, 0.0)
        units = wins * WIN_PAYOUT - (dec - wins)
        # how far the final actually lands vs where we bet, and vs pregame
        margin = sum(r["final"] - r[key] for r in picks) / n if n else 0.0
        vs_close = sum(r["final"] - r["closing"] for r in picks) / n if n else 0.0
        out.append({"thr": thr, "n": n, "dec": dec, "wins": wins, "hit": hit,
                    "lo": lo, "hi": hi, "units": units, "margin": margin, "vs_close": vs_close})
    return out


def render(title, sub, results, as_pct):
    t = Table(title=title, caption=sub)
    for c in ("drop ≥", "games", "Over hit%", "Wilson 95% CI", "units @-110",
              "avg final−bet", "avg final−close"):
        t.add_column(c, justify="right" if c != "drop ≥" else "left")
    for r in results:
        thr = f"{int(r['thr']*100)}%" if as_pct else f"{r['thr']:.1f} runs"
        if r["dec"] == 0:
            t.add_row(thr, "0", "—", "—", "—", "—", "—"); continue
        col = "[green]" if r["lo"] > BREAKEVEN else ("[yellow]" if r["hit"] > BREAKEVEN else "[red]")
        t.add_row(thr, str(r["n"]), f"{col}{100*r['hit']:.1f}%[/]",
                  f"{100*r['lo']:.0f}–{100*r['hi']:.0f}%", f"{r['units']:+.1f}",
                  f"{r['margin']:+.2f}", f"{r['vs_close']:+.2f}")
    console.print(t)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    rows = build(games, args.refresh)
    console.rule(f"[bold]Simple drop rule · {len(rows)} games reached the 4th inning")
    console.print(f"[dim]Bet the Over at the end-of-3rd live total when it dropped ≥ threshold "
                  f"from the pregame close. Breakeven {100*BREAKEVEN:.1f}%. No other filters.[/]\n")
    render("By % drop from pregame close (end of 3rd)",
           "green = CI clears breakeven · yellow = point est only · red = below",
           grade(rows, "line3", PCT_THRESHOLDS, True), True)
    render("By absolute run drop (end of 3rd)", "same games, drop measured in runs",
           grade(rows, "line3", RUN_THRESHOLDS, False), False)
    console.print("\n[dim]avg final−bet = how far the final total landed above/below the number "
                  "you'd bet · avg final−close = final vs the pregame line.[/]")
    (HERE / "output" / "simple_drop_test.json").write_text(json.dumps({
        "n_games": len(rows),
        "by_pct": grade(rows, "line3", PCT_THRESHOLDS, True),
        "by_runs": grade(rows, "line3", RUN_THRESHOLDS, False)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
