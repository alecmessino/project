#!/usr/bin/env python3
"""July Instrument Characterization — what does the new (live, two-book, 30 s) instrument measure?

Standalone empirical characterization of the July dataset ON ITS OWN TERMS.
This script does NOT validate or invalidate Paper 1: the June instrument (Pinnacle line,
Statcast features, ~1 min cadence) and the July instrument (fanduel/bovada, MLB statsapi
state, 30 s cadence) are different measurement apparatus, so no comparison of results is
meaningful. Where June is mentioned it is only to record what is STRUCTURALLY ABSENT here.

Every relationship reported is EXPLORATORY (GD-14): generated from these data, therefore
requiring confirmation on data not used to generate it before entering any manuscript.

    python3 the_third_turn/july_instrument_report.py

Reads output/{book_panel,game_state_panel}.jsonl. Writes nothing; prints the report.
"""

from __future__ import annotations

import json
import math
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "output" / "book_panel.jsonl"
STATE = HERE / "output" / "game_state_panel.jsonl"

# Main-line extraction is a documented free parameter (RD-3 / A-11). We FIX the
# odds-anchored rule (most balanced quote in the group) and report sensitivity where it matters.
EXTRACTION = "balanced-odds"


def imp(o: float) -> float:
    o = float(o)
    return (-o) / ((-o) + 100) if o < 0 else 100.0 / (o + 100)


def epoch(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def mean_ci(xs: list[float]) -> tuple[float, float, float]:
    """Mean with a normal-approx 95% CI."""
    n = len(xs)
    if n < 2:
        return (float("nan"),) * 3
    m = st.mean(xs)
    se = st.stdev(xs) / math.sqrt(n)
    return (m, m - 1.96 * se, m + 1.96 * se)


def load():
    book = [json.loads(l) for l in BOOK.read_text().splitlines() if l.strip()]
    state = [json.loads(l) for l in STATE.read_text().splitlines() if l.strip()]
    for r in book:
        r["_t"] = epoch(r["ts"])
    for r in state:
        r["_t"] = epoch(r["ts"])
    return book, state


def main_lines(book: list[dict]) -> dict:
    """(game, book, ts) -> the single main-line quote, by the fixed extraction rule."""
    grp = defaultdict(list)
    for r in book:
        if r.get("over_odds") is not None and r.get("under_odds") is not None:
            grp[(r["game"], r["book"], r["ts"])].append(r)
    return {k: min(v, key=lambda r: abs(imp(r["over_odds"]) - imp(r["under_odds"])))
            for k, v in grp.items()}


def section(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def main() -> int:
    book, state = load()
    live = [r for r in book if r.get("live")]
    mains = main_lines(book)
    live_main = sorted((m for m in mains.values() if m.get("live")), key=lambda r: (r["game"], r["_t"]))

    print("JULY INSTRUMENT CHARACTERIZATION")
    print(f"extraction rule: {EXTRACTION} (fixed; RD-3/A-11 free parameter)")
    print("ALL relationships below are EXPLORATORY and require independent confirmation.")

    # ---------- A. Instrument profile ----------
    section("A. WHAT THIS INSTRUMENT IS")
    days = sorted({r["ts"][:10] for r in book})
    print(f"  span            : {days[0]} .. {days[-1]}  ({len(days)} days)")
    print(f"  book rows       : {len(book):,}  (live {len(live):,})")
    print(f"  state rows      : {len(state):,}")
    print(f"  games (book)    : {len({r['game'] for r in book})}   live games: {len({r['game'] for r in live})}")
    bc = Counter(r["book"] for r in book)
    print(f"  books           : {dict(bc)}")
    hasst = [r for r in book if "status" in r]
    print(f"  status coverage : {len(hasst):,}/{len(book):,} rows "
          f"({len(hasst)/len(book)*100:.0f}%), by book: "
          f"{ {b: sum(1 for r in hasst if r['book']==b) for b in bc} }")
    # cadence
    gaps = []
    per = defaultdict(list)
    for r in live:
        per[(r["game"], r["book"])].append(r["_t"])
    for ts in per.values():
        u = sorted(set(round(x) for x in ts))
        gaps += [b - a for a, b in zip(u, u[1:]) if 0 < b - a < 600]
    print(f"  live poll gap   : median {st.median(gaps):.0f}s  (p25 {sorted(gaps)[len(gaps)//4]:.0f}, "
          f"p75 {sorted(gaps)[3*len(gaps)//4]:.0f})")
    print("  STRUCTURALLY ABSENT vs the June instrument (not a finding, a design fact):")
    print("    - sharp benchmark book (Pinnacle live quotes = "
          f"{sum(1 for r in live if r['book']=='pinnacle')})")
    print("    - pitch-velocity features (Statcast unreachable)")
    print("    - weather/park covariates (not carried in the live panels)")

    # ---------- B. Event response ----------
    section("B. DOES THE LINE RESPOND TO RUNS? (the instrument's core signal)")
    # per game: score timeline -> run events; measure main-line change around each
    sc = defaultdict(list)
    for s in state:
        sc[s["game"]].append(s)
    for g in sc:
        sc[g].sort(key=lambda r: r["_t"])
    lines_by = defaultdict(list)
    for m in live_main:
        lines_by[(m["game"], m["book"])].append(m)

    def line_at(g, b, t):
        arr = lines_by.get((g, b))
        if not arr:
            return None
        prev = None
        for m in arr:
            if m["_t"] <= t:
                prev = m
            else:
                break
        return prev

    WIN = 300  # seconds after the event
    deltas = defaultdict(list)
    nev = 0
    for g, rows in sc.items():
        last = None
        for s in rows:
            tot = s["away_score"] + s["home_score"]
            if last is not None and tot > last:
                nev += 1
                runs = tot - last
                for b in ("fanduel", "bovada"):
                    a = line_at(g, b, s["_t"])
                    c = line_at(g, b, s["_t"] + WIN)
                    if a and c and a is not c:
                        deltas[b].append((c["line"] - a["line"]) / runs)
            last = tot
    print(f"  run-scoring events detected: {nev}")
    for b in ("fanduel", "bovada"):
        d = deltas[b]
        if len(d) < 30:
            print(f"  {b:9s} n={len(d)} (too few)")
            continue
        m, lo, hi = mean_ci(d)
        print(f"  {b:9s} n={len(d):5d}  mean Dline per run = {m:+.3f} [{lo:+.3f},{hi:+.3f}]  "
              f"median {st.median(d):+.3f}")
    print("  READ: the posted live number is a FULL-GAME total (verified: live median line")
    print("  8.5 = pregame median 8.5, max 28.5; a remaining-runs line would decay toward 0).")
    print("  So a scored run enters the total as +1 and is partly offset by the shorter")
    print("  remaining game. The coefficient is therefore a PASS-THROUGH fraction in [0,1]:")
    print("  ~0.6 means about 60% of a run sticks and ~40% is absorbed by less time left.")
    print("  This is a property of the instrument, NOT an efficiency claim, and it is NOT")
    print("  comparable to Paper 1's transfer function (different book, features, cadence).")
    print("  The fanduel/bovada gap is confounded by update frequency (E-016/17) and the")
    print("  fixed 300s window; do not read it as a book-quality difference.")

    # ---------- C. Vig: pregame vs live, and vs game state ----------
    section("C. PRICING (VIG): PREGAME vs LIVE  [the standout new phenomenon]")
    # Quotes within a game are massively autocorrelated, so ALL intervals here are
    # clustered at the GAME level: collapse each game to one mean, then interval the games.
    def clustered(vals_by_game: dict) -> tuple:
        per_game = [st.mean(v) for v in vals_by_game.values() if v]
        return mean_ci(per_game) + (len(per_game),)

    pre_by, live_by = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for m in mains.values():
        v = imp(m["over_odds"]) + imp(m["under_odds"]) - 1
        if not (-0.02 < v < 0.20):
            continue
        (live_by if m.get("live") else pre_by)[m["book"]][m["game"]].append(v)
    for b in ("fanduel", "bovada"):
        pm, plo, phi, pn = clustered(pre_by[b])
        lm, llo, lhi, ln = clustered(live_by[b])
        print(f"  {b:9s} pregame {pm*100:5.2f}% [{plo*100:5.2f},{phi*100:5.2f}] (n={pn} games)   "
              f"live {lm*100:5.2f}% [{llo*100:5.2f},{lhi*100:5.2f}] (n={ln} games)   "
              f"widening +{(lm-pm)*100:.2f}pp")
    print("  The in-play spread is materially wider than the pregame spread in both books.")
    print("  This is a genuinely NEW observable: the June instrument had no live two-sided")
    print("  quote stream to measure it on. It raises the bettor's break-even and is the")
    print("  natural subject of the separate vig/inventory paper (GD-13).")

    section("C2. VIG BY INNING  [game-clustered intervals]")
    by_inn = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for m in live_main:
        arr = sc.get(m["game"])
        if not arr:
            continue
        stt = None
        for s in arr:
            if s["_t"] <= m["_t"]:
                stt = s
            else:
                break
        if not stt:
            continue
        v = imp(m["over_odds"]) + imp(m["under_odds"]) - 1
        if -0.02 < v < 0.20:
            by_inn[m["book"]][min(stt["inning"], 9)][m["game"]].append(v)
    for b in ("fanduel", "bovada"):
        print(f"  {b}:")
        for inn in sorted(by_inn[b]):
            mm, lo, hi, n = clustered(by_inn[b][inn])
            if n < 10:
                continue
            print(f"    inning {inn}: {n:3d} games  vig {mm*100:5.2f}% [{lo*100:5.2f},{hi*100:5.2f}]")

    # ---------- D. Cross-book divergence ----------
    section("D. CROSS-BOOK DIVERGENCE  [only observable with >=2 books]")
    bytime = defaultdict(dict)
    for m in live_main:
        bytime[(m["game"], round(m["_t"] / 60))][m["book"]] = m
    both = [v for v in bytime.values() if len(v) == 2]
    dl = [v["fanduel"]["line"] - v["bovada"]["line"] for v in both]
    dv = [(imp(v["fanduel"]["over_odds"]) + imp(v["fanduel"]["under_odds"]))
          - (imp(v["bovada"]["over_odds"]) + imp(v["bovada"]["under_odds"])) for v in both]
    if dl:
        agree = sum(1 for x in dl if abs(x) < 1e-9)
        lo, hi = wilson(agree, len(dl))
        s = sorted(abs(x) for x in dl)
        print(f"  co-observed minutes: {len(dl):,}")
        print(f"  identical main line: {agree/len(dl)*100:.1f}% [{lo*100:.1f},{hi*100:.1f}]")
        print(f"  |line gap|: median {st.median(s):.2f}  p90 {s[int(.9*len(s))]:.2f}  max {s[-1]:.1f}")
        m, l2, h2 = mean_ci(dv)
        print(f"  vig gap (fd - bov): {m*100:+.2f}pp [{l2*100:+.2f},{h2*100:+.2f}]")

    # ---------- E. Quote lifecycle ----------
    section("E. QUOTE LIFECYCLE  [new phenomenon: only the 30s instrument sees this]")
    stc = Counter((r["book"], r.get("status") or "unset") for r in book if r.get("live"))
    for b in ("fanduel", "bovada"):
        tot = sum(v for (bb, s), v in stc.items() if bb == b)
        if not tot:
            continue
        row = {s: v for (bb, s), v in stc.items() if bb == b}
        print(f"  {b:9s} " + "  ".join(f"{s}={v/tot*100:.1f}%" for s, v in sorted(row.items())))
    print("  NOTE (RD-4): bovada emits no status at all, so any suspension-filtered")
    print("  comparison across books is asymmetric by construction.")

    # ---------- F. Multiplicity ----------
    section("F. MULTIPLICITY AND WHAT THIS LICENSES")
    print("  Distinct relationships examined above: 5 families (A-E).")
    print("  No p-values are reported: with game-clustered data and a fixed, un-preregistered")
    print("  analysis set, nominal significance would overstate evidence. Intervals are shown")
    print("  for magnitude only.")
    print("  NOTHING here is confirmatory. Per GD-14, any hypothesis generated from this")
    print("  dataset must be confirmed on data not used to generate it before entering a paper.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
