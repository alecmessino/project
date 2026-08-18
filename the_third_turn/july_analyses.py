#!/usr/bin/env python3
"""Authoritative, version-controlled implementation of E-016, E-017 and E-018.

WHY THIS FILE EXISTS (E-025, 2026-08-11)

E-016/E-017/E-018 were produced by ad-hoc scripts run in conversation and never committed.
An independent reconstruction later matched 0 of 7 recorded figures, which meant the ledger
carried three entries that could not be regenerated from committed inputs — a direct breach
of the reproducibility standard Paper 2 states for itself. This module recovers the original
implementations verbatim in logic, so the recorded numbers can be reproduced, audited, and
re-run under exclusions.

The recovered code is transcribed, not reinterpreted. Where the original made a choice that
is arguably wrong, the choice is PRESERVED and flagged in a `CAVEAT` comment rather than
silently corrected. Fixing it here would replace history instead of reproducing it.

The reconstruction failed for four separable reasons, all now documented:

  1. SAMPLE.    E-016 and E-017 group over the ENTIRE panel — pregame rows included. The
                reconstruction used live rows only. RD-3's alternate lines exist only in
                pregame (54.1% of pregame groups carry two lines; 0.0% of live groups do),
                so a live-only sample makes every extraction rule agree trivially and
                E-017's invariance question cannot arise.
  2. STATISTIC. E-016's headline "4.7x" is a per-game CHANGE RATE ratio (changes/polls),
                medianed across games — not a ratio of seconds between changes.
  3. EVENTS.    E-018 defines an event as a change in the posted LINE LEVEL only, ignoring
                odds moves, and matches the two books on the SAME level.
  4. FILTERS.   Gaps capped to 0 < dt < 3600 s; vig clipped to -0.02 < v < 0.20.

    python3 the_third_turn/july_analyses.py                  # reproduce the record
    python3 the_third_turn/july_analyses.py --exclude slice  # E-023 sensitivity
    python3 the_third_turn/july_analyses.py --exclude matchup
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE / "output" / "book_panel.jsonl"

TRUNCATED = {"TOR@SD", "COL@SF", "ARI@LAD"}     # games truncated by the E-023 outage
TRUNC_DATE = "2026-07-12"
W = 300                                          # E-018 lead/lag window, seconds


def imp(o):
    o = float(o)
    return (-o) / ((-o) + 100) if o < 0 else 100.0 / (o + 100)


# The as-of date the ledger entries were computed (2026-07-19). The panel is append-only and
# has grown since, so reproducing the RECORD requires reproducing its sample, not just its
# code. Without this the same code returns 609 s where the ledger says 916 s — not a bug,
# just a bigger sample. Every historical figure must be regenerated at its own as-of date.
# Resolved 2026-08-18: a DATE-only cutoff cannot reproduce the record, because the original
# analyses ran partway through 2026-07-19. Excluding all of that day returns a 28.2% agreement
# rate and including all of it returns 28.8%, bracketing but not matching the recorded 28.6%.
# The session transcript timestamps the original E-017 run at 2026-07-19T17:29:50Z; cutting
# there reproduces 28.6% exactly. The as-of is therefore an INSTANT, not a date.
RECORD_ASOF = "2026-07-19T17:29:50"


def load(exclude=None, asof=None):
    rows = [json.loads(l) for l in PANEL.open() if l.strip()]
    for r in rows:
        r["_t"] = datetime.fromisoformat(r["ts"]).timestamp()
    # CAVEAT (preserved): the originals did NOT restrict to July. The panel was July-only
    # when they ran; it no longer is. Restrict here so the recorded numbers reproduce.
    rows = [r for r in rows if r["ts"][:7] == "2026-07"]
    if asof:
        # compare on as many characters as the cutoff supplies, so a bare date still works
        k = len(asof)
        rows = [r for r in rows if r["ts"][:k] < asof]
    if exclude == "slice":
        rows = [r for r in rows
                if not (r["game"] in TRUNCATED and r["ts"][:10] == TRUNC_DATE)]
    elif exclude == "matchup":
        rows = [r for r in rows if r["game"] not in TRUNCATED]
    return rows


def groups(rows, live_only):
    """(game, book, ts) -> [rows]. E-016/E-017 include pregame; E-018 does not."""
    rs = [r for r in rows if r.get("over_odds") is not None
          and (r.get("under_odds") is not None or live_only)]
    if live_only:
        rs = [r for r in rs if r.get("live")]
    g = defaultdict(list)
    for r in rs:
        g[(r["game"], r["book"], r["ts"])].append(r)
    return g


# ────────────────────────────────────────────────────────────── E-016
def e016(rows):
    grp = groups(rows, live_only=False)
    main = [min(rs, key=lambda r: abs(imp(r["over_odds"]) - imp(r["under_odds"])))
            for rs in grp.values()]
    live = [r for r in main if r.get("live")]
    out = {}
    for b in ("bovada", "fanduel"):
        vigs = sorted(imp(r["over_odds"]) + imp(r["under_odds"]) - 1
                      for r in main if r["book"] == b)
        vigs = [v for v in vigs if -0.02 < v < 0.20]
        iqr = vigs[int(.75 * len(vigs))] - vigs[int(.25 * len(vigs))]

        per = defaultdict(list)
        for r in sorted((r for r in live if r["book"] == b),
                        key=lambda r: (r["game"], r["_t"])):
            per[r["game"]].append(r)
        gaps, changes, polls = [], 0, 0
        for rs in per.values():
            polls += len(rs)
            last = None
            for r in rs:
                k = (r["line"], r["over_odds"], r["under_odds"])
                # CAVEAT (preserved): dt is measured to the PREVIOUS OBSERVATION, not the
                # previous change, so this is "poll gap at the moment of a change", not the
                # interval between successive changes. Reported as "med_sec_btw_change".
                if last and k != last[0]:
                    dt = r["_t"] - last[1]
                    if 0 < dt < 3600:
                        gaps.append(dt)
                    changes += 1
                last = (k, r["_t"])
        out[b] = {"vig_med": st.median(vigs) * 100, "vig_iqr": iqr * 100,
                  "change_rate": changes / max(polls, 1),
                  "med_sec": st.median(gaps) if gaps else float("nan")}
    return out


# ────────────────────────────────────────────────────────────── E-017
def e017(rows):
    grp = groups(rows, live_only=False)
    game_lines = defaultdict(Counter)
    for rs in grp.values():
        for r in rs:
            game_lines[(r["game"], r["book"])][r["line"]] += 1
    modal = {k: c.most_common(1)[0][0] for k, c in game_lines.items()}

    def pick(rs, how):
        if how == "balanced":
            return min(rs, key=lambda r: abs(imp(r["over_odds"]) - imp(r["under_odds"])))
        if how == "modal":
            m = modal[(rs[0]["game"], rs[0]["book"])]
            return min(rs, key=lambda r: abs(r["line"] - m))
        med = st.median([r["line"] for r in rs])
        return min(rs, key=lambda r: abs(r["line"] - med))

    defs = ["balanced", "modal", "median"]
    mains = {d: {k: pick(rs, d) for k, rs in grp.items()} for d in defs}

    agree = Counter()
    for k in grp:
        agree["all3" if len({mains[d][k]["line"] for d in defs}) == 1 else "no"] += 1
    tot = sum(agree.values())

    def freq_result(mainmap):
        live = [m for m in mainmap.values() if m.get("live")]
        per = defaultdict(lambda: defaultdict(list))
        for r in sorted(live, key=lambda r: (r["game"], r["_t"])):
            per[r["game"]][r["book"]].append(r)

        def cr(rs):
            if len(rs) < 2:
                return None
            last, ch = None, 0
            for r in rs:
                k = (r["line"], r["over_odds"], r["under_odds"])
                if last and k != last:
                    ch += 1
                last = k
            return ch / len(rs)

        wins = n = 0
        ratios = []
        for bb in per.values():
            if "bovada" in bb and "fanduel" in bb:
                cb, cf = cr(bb["bovada"]), cr(bb["fanduel"])
                if cb is None or cf is None:
                    continue
                n += 1
                wins += cf > cb
                if cb > 0:
                    ratios.append(cf / cb)
        return wins, n, st.median(ratios) if ratios else float("nan")

    vig = {}
    for d in defs:
        vig[d] = {}
        for b in ("bovada", "fanduel"):
            v = sorted(imp(m["over_odds"]) + imp(m["under_odds"]) - 1
                       for m in mains[d].values() if m["book"] == b)
            v = [x for x in v if -0.02 < x < 0.20]
            vig[d][b] = (v[int(.75 * len(v))] - v[int(.25 * len(v))]) * 100
    return {"agree_pct": agree["all3"] / tot * 100, "n": tot,
            "freq": {d: freq_result(mains[d]) for d in defs}, "vig": vig}


# ────────────────────────────────────────────────────────────── E-018
def e018(rows):
    grp = groups(rows, live_only=True)
    gl = defaultdict(Counter)
    for rs in grp.values():
        for r in rs:
            gl[(r["game"], r["book"])][r["line"]] += 1
    modal = {k: c.most_common(1)[0][0] for k, c in gl.items()}
    mains = {k: min(rs, key=lambda r: abs(r["line"] - modal[(rs[0]["game"], rs[0]["book"])]))
             for k, rs in grp.items()}

    ev = defaultdict(list)
    for m in sorted(mains.values(), key=lambda r: (r["game"], r["book"], r["_t"])):
        key = (m["game"], m["book"])
        # CAVEAT (preserved): an event is a change in the LINE LEVEL only. Odds-only
        # revisions are not events here.
        if not ev[key] or ev[key][-1][1] != m["line"]:
            ev[key].append((m["_t"], m["line"]))

    def test(lead, follow):
        pre = post = n = 0
        for g in sorted({g for (g, _) in ev}):
            el, ef = ev.get((g, lead)), ev.get((g, follow))
            if not el or not ef:
                continue
            for tf, lf in ef:
                n += 1
                if any(lf == ll and tf - W <= tl < tf for tl, ll in el):
                    pre += 1
                if any(lf == ll and tf < tl <= tf + W for tl, ll in el):
                    post += 1
        return n, pre, post

    return {"fd_leads_bv": test("fanduel", "bovada"),
            "bv_leads_fd": test("bovada", "fanduel")}


def report(rows, label):
    a, b, c = e016(rows), e017(rows), e018(rows)
    print(f"\n{'=' * 74}\n {label}   (rows={len(rows):,})\n{'=' * 74}")
    print(" E-016  main line, whole panel for vig; live stream for cadence")
    for bk, v in a.items():
        print(f"   {bk:9s} vig_med={v['vig_med']:5.2f}%  vig_IQR={v['vig_iqr']:4.2f}pp  "
              f"change_rate={v['change_rate']:.3f}  med_sec_btw_change={v['med_sec']:5.0f}")
    print(f"\n E-017  3-rule agreement: {b['agree_pct']:.1f}%  (n={b['n']:,})")
    for d, (w, n, r) in b["freq"].items():
        print(f"   {d:9s} FanDuel>Bovada in {w}/{n} games   median ratio {r:.1f}x   "
              f"vig bovada={b['vig'][d]['bovada']:.2f}pp fanduel={b['vig'][d]['fanduel']:.2f}pp")
    print("\n E-018  base-rate placebo, same-level match, W=300s")
    for k, (n, pre, post) in c.items():
        if not n:
            continue
        print(f"   {k:12s} n={n:5,}  precede {pre / n * 100:4.0f}%  follow {post / n * 100:4.0f}%"
              f"   asymmetry {(pre - post) / n * 100:+.0f} pp")
    return a, b, c


def main() -> int:
    exclude = None
    if "--exclude" in sys.argv:
        exclude = sys.argv[sys.argv.index("--exclude") + 1]
    asof = RECORD_ASOF if "--asof" in sys.argv else None
    rows = load(exclude, asof)
    label = (f"JULY ANALYSES — exclude={exclude or 'none'}"
             f"  asof={asof or 'full panel'}")
    a, b, c = report(rows, label)

    if exclude is None and asof:
        print("\n" + "-" * 74)
        print(" REPRODUCTION CHECK vs the recorded ledger figures")
        print("-" * 74)
        checks = [
            ("E-016 bovada med_sec_btw_change", "916", f"{a['bovada']['med_sec']:.0f}"),
            ("E-016 fanduel med_sec_btw_change", "92", f"{a['fanduel']['med_sec']:.0f}"),
            ("E-016 vig IQR bovada tighter", "True",
             str(a["bovada"]["vig_iqr"] < a["fanduel"]["vig_iqr"])),
            ("E-017 3-rule agreement", "28.6", f"{b['agree_pct']:.1f}"),
            ("E-017 balanced ratio", "4.7", f"{b['freq']['balanced'][2]:.1f}"),
            ("E-017 modal ratio", "1.1", f"{b['freq']['modal'][2]:.1f}"),
            ("E-017 median ratio", "9.5", f"{b['freq']['median'][2]:.1f}"),
        ]
        ok = 0
        for name, rec, got in checks:
            hit = rec == got
            ok += hit
            print(f"   {name:34} recorded {rec:>7}   here {got:>7}   "
                  f"{'match' if hit else 'DIFFERS'}")
        n, pre, post = c["fd_leads_bv"]
        print(f"   {'E-018 precede / follow':34} recorded  36/18   here "
              f"{pre / n * 100:5.0f}/{post / n * 100:.0f}")
        print(f"\n   {ok}/{len(checks)} numeric checks reproduce.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
