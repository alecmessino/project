#!/usr/bin/env python3
"""Program A — the market's transfer function on the live game total.

For every play we compute the true change in run expectancy
    ΔRE = runs scored + (RE24_after − RE24_before)      (Tango RE24, base-out tracked)
and the live total's converged move
    ΔBook = line(t+5min) − line(just before)
then the response ratio ΔBook/ΔRE and the bias ΔBook−ΔRE, averaged by event type. This
estimates magnitude (does it move by the right amount?), completeness (+1 vs +5 min),
and asymmetry (does it treat some shocks differently?).

Note on interpretation: this is a SINGLE source (Odds Papi ≈ Pinnacle) at ~1-min cadence,
so a uniform ratio < 1 across all events could be feed lag, not market under-reaction.
The robust signal is the ASYMMETRY — event types whose ratio differs from the rest.

    python the_third_turn/program_a.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get, line_lookup  # noqa: E402
from shared_piping.run_expectancy import re24  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "program_a_cache.json"
BASE = {"1B": 1, "2B": 2, "3B": 3}
LW = {"home_run": 1.40, "triple": 1.03, "double": 0.77, "single": 0.47,
      "walk": 0.31, "hit_by_pitch": 0.34}   # linear-weight sanity check for ΔRE


def _at(fn, t0_iso, dmin):
    try:
        t = datetime.fromisoformat(t0_iso.replace("Z", "+00:00")) + timedelta(minutes=dmin)
    except ValueError:
        return None
    return fn(t.strftime("%Y-%m-%dT%H:%M"))


def game_events(feed, points):
    fn = line_lookup(points)
    plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
    out, total, prev_pitcher, cur_half = [], 0, None, None
    bases = {1: False, 2: False, 3: False}
    outs = 0
    for play in plays:
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        inning, is_top = int(about.get("inning") or 0), bool(about.get("isTopInning"))
        if (inning, is_top) != cur_half:
            cur_half, bases, outs = (inning, is_top), {1: False, 2: False, 3: False}, 0
        b_before = (bases[1], bases[2], bases[3])
        o_before = min(outs, 2)

        aw, hm = res.get("awayScore"), res.get("homeScore")
        new_total = (aw + hm) if aw is not None else total
        runs = new_total - total

        # apply base-out transition from the play's runner movements
        after = dict(bases)
        for r in play.get("runners", []):
            mv = r.get("movement", {})
            s, e = mv.get("originBase"), mv.get("end")
            if s in BASE:
                after[BASE[s]] = False
            if e in BASE:
                after[BASE[e]] = True
        o_after = res.get("outs")
        o_after = int(o_after) if o_after is not None else outs
        re_after = 0.0 if o_after >= 3 else re24(after[1], after[2], after[3], min(o_after, 2))
        dre = runs + (re_after - re24(b_before[0], b_before[1], b_before[2], o_before))

        pid = (match.get("pitcher") or {}).get("id")
        etype = res.get("eventType", "")
        events = [etype] if etype in LW else []
        if prev_pitcher is not None and pid != prev_pitcher:
            events.append("pitching_change")

        t0 = about.get("startTime") or ""
        pre = fn(t0)
        if pre is not None:
            for ev in events:
                d = {str(dm): round(v - pre, 3) for dm in (1, 5)
                     if (v := _at(fn, t0, dm)) is not None}
                if d:
                    out.append({"type": ev, "dre": round(dre, 3), "d": d, "inning": inning})

        bases, outs, total, prev_pitcher = after, o_after, new_total, pid
    return out


def build(refresh=False):
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text())
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    rows = []
    for g in games:
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        rows += game_events(feed, g["points"])
    CACHE.write_text(json.dumps(rows))
    return rows


def main() -> int:
    rows = build(refresh=True)
    by = defaultdict(list)
    for r in rows:
        by[r["type"]].append(r)
    console.rule(f"[bold]Program A · transfer function · {len(rows)} events")
    console.print("[dim]ΔRE = runs + ΔRE24 (Tango). ΔBook = converged (+5min) line move. "
                  "Ratio = ΔBook/ΔRE (1.0 = correct); Bias = ΔBook − ΔRE. Read ASYMMETRY across "
                  "events, not absolute level (single source may attenuate all uniformly).[/]\n")

    t = Table(title="Endpoint table — market elasticity by event")
    for c in ("event", "n", "avg ΔRE", "avg ΔBook +5", "+1min", "ratio", "bias"):
        t.add_column(c, justify="left" if c == "event" else "right")
    for ev in ["home_run", "triple", "double", "single", "walk", "hit_by_pitch", "pitching_change"]:
        recs = by.get(ev, [])
        if len(recs) < 5:
            continue
        dre = np.mean([r["dre"] for r in recs])
        b5 = np.mean([r["d"]["5"] for r in recs if "5" in r["d"]])
        b1 = np.mean([r["d"]["1"] for r in recs if "1" in r["d"]])
        ratio = b5 / dre if abs(dre) > 0.05 else float("nan")
        col = "[green]" if 0.9 <= ratio <= 1.1 else ("[yellow]" if 0.75 <= ratio < 0.9 else "[red]")
        t.add_row(ev, str(len(recs)), f"{dre:+.2f}", f"{b5:+.2f}", f"{b1:+.2f}",
                  f"{col}{ratio:.2f}[/]" if ratio == ratio else "n/a", f"{b5-dre:+.2f}")
    console.print(t)
    console.print("\n[dim]Sanity: avg ΔRE should track linear weights (HR~1.4, 2B~0.77, 1B~0.47, "
                  "BB~0.31). If ratios cluster near 1.0, the sharp market adjusts correctly → historical "
                  "phase complete, pivot to live microstructure.[/]")

    (HERE / "output" / "program_a.json").write_text(json.dumps({
        "n": len(rows),
        "by_type": {ev: {"n": len(rs), "avg_dre": round(float(np.mean([r["dre"] for r in rs])), 3),
                         "avg_book5": round(float(np.mean([r["d"]["5"] for r in rs if "5" in r["d"]])), 3)}
                    for ev, rs in by.items() if len(rs) >= 5}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
