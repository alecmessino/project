#!/usr/bin/env python3
"""Microstructure probe — exploratory analysis of the live-banked panels.

Runs on the runner-committed streams (output/{book,team_total,game_state}_panel.jsonl).
Every "finding" here is validated against the measurement process before it is believed;
tonight's two candidate findings (cross-book leadership, cross-book divergence) BOTH
dissolve under that scrutiny. See microstructure_notes.md for the write-up.

    python the_third_turn/microstructure_probe.py
"""
from __future__ import annotations
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
def rd(n): return [json.loads(l) for l in (HERE / "output" / n).open() if l.strip()]
def T(s): return datetime.fromisoformat(s)


def load_series(bp):
    s = defaultdict(lambda: defaultdict(list))
    for r in bp:
        s[r["game"]][r["book"]].append((T(r["ts"]), r["line"], r["live"]))
    for g in s:
        for b in s[g]:
            s[g][b].sort()
    return s


def ff(sl, t):
    v = lv = vt = None
    for (tt, l, liv) in sl:
        if tt <= t:
            v, lv, vt = l, liv, tt
        else:
            break
    return v, lv, vt


def main():
    bp = rd("book_panel.jsonl")
    tt = rd("team_total_panel.jsonl")
    print(f"book_panel {len(bp)} rows; team_total {len(tt)} rows")
    books = Counter(r["book"] for r in bp)
    live = sum(r["live"] for r in bp)
    print(f"  books {dict(books)}; games {len({r['game'] for r in bp})}; "
          f"live {live} ({live/len(bp):.0%})")

    s = load_series(bp)
    both = [g for g in s if "fanduel" in s[g] and "bovada" in s[g]]

    # ── divergence + the validation checklist ────────────────────────────────
    gap = []; stale = []; live_gap = []
    for g in both:
        fd, bv = s[g]["fanduel"], s[g]["bovada"]
        for t in sorted({x[0] for x in fd} | {x[0] for x in bv}):
            a, al, at = ff(fd, t); b, bl, bt = ff(bv, t)
            if a is None or b is None:
                continue
            gap.append(abs(a - b)); stale.append(max((t - at).total_seconds(), (t - bt).total_seconds()))
            if al and bl:
                live_gap.append(abs(a - b))
    gap = np.array(gap)
    nz = gap[gap > 1e-9]
    print("\nDIVERGENCE (validated):")
    print(f"  any disagreement: {len(nz)/len(gap):.0%};  >0.5-run (material): {(gap>0.5).mean():.0%}")
    print(f"  of disagreements, share that is exactly one 0.5 tick: "
          f"{np.mean(np.round(nz,2)==0.5):.0%}")
    print(f"  fwd-fill staleness at comparison: median {np.median(stale):.0f}s "
          f"(mostly pregame, stable lines)")
    print(f"  comparisons with BOTH books live simultaneously: {len(live_gap)}  "
          f"<= if 0, there is no live divergence result at all")

    # ── lead-lag: naive (confounded) vs density-neutral ──────────────────────
    fd_first = bv_first = 0
    for g in both:
        rf, rb = {}, {}
        for (t, l, _) in s[g]["fanduel"]: rf.setdefault(l, t)
        for (t, l, _) in s[g]["bovada"]: rb.setdefault(l, t)
        for l in set(rf) & set(rb):
            dt = (rf[l] - rb[l]).total_seconds()
            fd_first += dt < -1; bv_first += dt > 1
    print("\nLEAD-LAG:")
    print(f"  naive 'who reached level first': FanDuel {fd_first} vs Bovada {bv_first} "
          f"(CONFOUNDED by {books['fanduel']/max(books['bovada'],1):.1f}x sampling density)")
    # density-neutral 60s grid, lagged cross-correlation of changes
    lead_fd, lead_bv = [], []
    for g in both:
        fd, bv = s[g]["fanduel"], s[g]["bovada"]
        t0 = max(fd[0][0], bv[0][0]); t1 = min(fd[-1][0], bv[-1][0])
        if t1 <= t0:
            continue
        grid = []; t = t0
        while t <= t1:
            grid.append(t); t += timedelta(seconds=60)
        fv = np.array([ff(fd, t)[0] for t in grid], float)
        bvv = np.array([ff(bv, t)[0] for t in grid], float)
        dfd, dbv = np.diff(fv), np.diff(bvv)
        for i in range(1, len(dfd)):
            lead_fd.append((dbv[i], dfd[i - 1])); lead_bv.append((dfd[i], dbv[i - 1]))

    def corr(p):
        a = np.array([x[0] for x in p]); b = np.array([x[1] for x in p])
        m = (a != 0) | (b != 0)
        if m.sum() < 10 or a[m].std() == 0 or b[m].std() == 0:
            return float("nan")
        return float(np.corrcoef(a[m], b[m])[0, 1])
    print(f"  density-neutral (60s grid): FanDuel-leads r={corr(lead_fd):+.3f}, "
          f"Bovada-leads r={corr(lead_bv):+.3f}  -> indistinguishable; not identifiable")

    # ── distribution panel ───────────────────────────────────────────────────
    sk = [r["skew"] for r in tt]; sd = [r["sd"] for r in tt]
    print("\nDISTRIBUTION PANEL (Pinnacle implied per-team, full pmf):")
    print(f"  implied skew mean {np.mean(sk):+.3f}; implied sd mean {np.mean(sd):.2f}; "
          f"pmf present: {all('probs' in r for r in tt)}")
    print("  (right-skewed as expected; full pmf every snapshot is the higher-moment substrate)")

    # ── stopping-rule gate (leadership analysis is blocked until ALL pass) ────
    pairs = 0; ov_games = set(); lags = []
    for g in both:
        fd, bv = s[g]["fanduel"], s[g]["bovada"]
        for t in sorted({x[0] for x in fd} | {x[0] for x in bv}):
            a, al, at = ff(fd, t); b, bl, bt = ff(bv, t)
            if a is None or b is None or not (al and bl):
                continue
            pairs += 1; ov_games.add(g); lags.append(abs((at - bt).total_seconds()))
    live_books = set()
    for r in bp:
        if r["live"]:
            live_books.add(r["book"])
    med_lag = float(np.median(lags)) if lags else float("inf")
    gate = [
        ("≥2000 simultaneous live quote pairs", pairs, pairs >= 2000),
        ("≥100 games with live overlap", len(ov_games), len(ov_games) >= 100),
        ("median sync lag <15s", f"{med_lag:.0f}s" if lags else "n/a", med_lag < 15),
        ("≥3 books quoting live", len(live_books), len(live_books) >= 3),
    ]
    print("\nSTOPPING-RULE GATE (leadership analysis blocked until all PASS):")
    for name, val, ok in gate:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:38s} current: {val}")
    print(f"  => {'CLEARED — analysis permitted' if all(g[2] for g in gate) else 'BLOCKED — keep collecting'}")


if __name__ == "__main__":
    main()
