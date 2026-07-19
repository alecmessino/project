#!/usr/bin/env python3
"""Book Characterization — measure each book as an *instrument*, not as a signal.

No inference. No trading conclusions. Just: how does each book behave — menu breadth,
update cadence, staleness, pricing consistency, line noise, and a *deliberately caveated*
first-arrival lead/lag (which is confounded by granularity — see the report).

    python3 the_third_turn/book_characterization.py

Reads output/book_panel.jsonl (ts, game, book, line, over_odds, under_odds, live).
Pure measurement; safe to run any time. Prints a report; writes nothing.
"""

from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE / "output" / "book_panel.jsonl"


def implied(odds: float) -> float:
    """American odds -> implied probability (with vig)."""
    o = float(odds)
    return (-o) / ((-o) + 100) if o < 0 else 100.0 / (o + 100)


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def load() -> list[dict]:
    rows = [json.loads(l) for l in PANEL.read_text().splitlines() if l.strip()]
    for r in rows:
        r["_t"] = _epoch(r["ts"])
    return rows


def quote_key(r: dict) -> tuple:
    return (r["line"], r["over_odds"], r["under_odds"])


def main() -> int:
    rows = load()
    books = sorted({r["book"] for r in rows})
    live = [r for r in rows if r.get("live")]
    print(f"rows={len(rows)}  live={len(live)}  books={books}")
    print(f"span {min(r['ts'] for r in rows)[:10]} -> {max(r['ts'] for r in rows)[:10]}\n")

    print("MENU BREADTH")
    for b in books:
        br = [r for r in rows if r["book"] == b]
        bl = [r for r in br if r.get("live")]
        print(f"  {b:9s} games={len(set(r['game'] for r in br)):3d}  "
              f"live_games={len(set(r['game'] for r in bl)):3d}  rows={len(br):6d}  live={len(bl):6d}")

    print("\nUPDATE CADENCE & STALENESS (live)")
    for b in books:
        bl = sorted((r for r in live if r["book"] == b), key=lambda r: (r["game"], r["_t"]))
        per = defaultdict(list)
        for r in bl:
            per[r["game"]].append(r)
        gaps, changes, polls, states = [], 0, 0, []
        for rs in per.values():
            polls += len(rs)
            last = None
            seen = set()
            for r in rs:
                seen.add(quote_key(r))
                if last is not None and quote_key(r) != quote_key(last):
                    dt = r["_t"] - last["_t"]
                    if 0 < dt < 3600:
                        gaps.append(dt)
                    changes += 1
                last = r
            states.append(len(seen))
        if not bl:
            print(f"  {b:9s} no live rows")
            continue
        print(f"  {b:9s} live_games={len(per):3d}  polls={polls:6d}  changes={changes:5d}  "
              f"change_rate={changes / max(polls, 1):.3f}  "
              f"med_sec_between_changes={st.median(gaps) if gaps else float('nan'):6.0f}  "
              f"med_states/game={st.median(states):.0f}")

    print("\nPRICING CONSISTENCY (overround = p_over + p_under - 1)")
    for b in books:
        br = [r for r in rows if r["book"] == b and r.get("over_odds") is not None
              and r.get("under_odds") is not None]
        vigs = [implied(r["over_odds"]) + implied(r["under_odds"]) - 1 for r in br]
        vigs = sorted(v for v in vigs if -0.02 < v < 0.20)
        if not vigs:
            print(f"  {b:9s} no priced rows")
            continue
        iqr = vigs[int(.75 * len(vigs))] - vigs[int(.25 * len(vigs))]
        print(f"  {b:9s} n={len(vigs):6d}  median_vig={st.median(vigs) * 100:5.2f}%  "
              f"IQR={iqr * 100:4.2f}pp")

    print("\nLINE REVERSAL (noise proxy: move then move back)")
    for b in books:
        per = defaultdict(list)
        for r in sorted((r for r in live if r["book"] == b), key=lambda r: (r["game"], r["_t"])):
            per[r["game"]].append(r["line"])
        revs = moves = 0
        for ls in per.values():
            seq = [ls[0]]
            for x in ls[1:]:
                if x != seq[-1]:
                    seq.append(x)
            for i in range(2, len(seq)):
                moves += 1
                if (seq[i] - seq[i - 1]) * (seq[i - 1] - seq[i - 2]) < 0:
                    revs += 1
        print(f"  {b:9s} directional_moves={moves:5d}  reversals={revs:4d}  "
              f"reversal_rate={revs / max(moves, 1):.3f}")

    # First-arrival lead/lag — REPORTED WITH A HEALTH WARNING. This metric is confounded
    # by granularity: a coarse/sticky book trivially "arrives first" at a line level and sits
    # on it while a granular book oscillates through and re-touches levels later. It is NOT a
    # measure of information leadership. The correct test aligns book moves to game EVENTS
    # (game_state_panel). Printed only to demonstrate the artifact, per the report.
    print("\nFIRST-ARRIVAL LEAD/LAG  [CONFOUNDED — do not read as leadership]")
    live_by = defaultdict(set)
    for r in live:
        live_by[r["game"]].add(r["book"])
    co = [g for g, bs in live_by.items() if len(bs) >= 2]
    led, secs, compared = defaultdict(int), defaultdict(list), 0
    for g in co:
        lv = {}
        for b in ("bovada", "fanduel"):
            rs = sorted((r for r in live if r["game"] == g and r["book"] == b), key=lambda r: r["_t"])
            first = {}
            last = None
            for r in rs:
                if last is None or r["line"] != last:
                    first.setdefault(r["line"], r["_t"])
                    last = r["line"]
            lv[b] = first
        if "bovada" not in lv or "fanduel" not in lv:
            continue
        for ln in set(lv["bovada"]) & set(lv["fanduel"]):
            tb, tf = lv["bovada"][ln], lv["fanduel"][ln]
            if abs(tb - tf) < 1:
                continue
            compared += 1
            w = "bovada" if tb < tf else "fanduel"
            led[w] += 1
            secs[w].append(abs(tb - tf))
    print(f"  co-quoted live games={len(co)}  arrivals compared={compared}")
    for b in ("bovada", "fanduel"):
        n = led[b]
        print(f"  {b:9s} first={n:4d} ({n / max(compared, 1) * 100:4.1f}%)  "
              f"med_gap={st.median(secs[b]) if secs[b] else float('nan'):5.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
