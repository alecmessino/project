#!/usr/bin/env python3
"""Read the feed-provenance probe and report whether Condition 3 can be satisfied.

Condition 3 of the Paper 2 gate (PAPER2_DESIGN_BRIEF §9) asks for an independent handle on
feed transport, or a defended argument that it is common-mode, or a documented demonstration
that neither is obtainable. This script turns `output/provenance_probe.jsonl` into that
document.

Two things matter and they are graded separately:

  PUBLICATION TIMESTAMP  a payload field that moves when the price moves. If one exists,
                         A4 becomes testable and Outcome A or B opens.
  TRANSPORT BOUND        the HTTP `Date` skew. Bounds network transport; does NOT separate
                         pricing from publication on its own.

Absence is a result. The script reports a rule-of-three upper bound on the presence rate so
"we never saw one" becomes a quantified claim rather than an assertion.

    python3 the_third_turn/provenance_report.py
"""

from __future__ import annotations

import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "output" / "provenance_probe.jsonl"

# Fields that are about the CONTRACT (when the game starts, when the market closes) rather
# than about publication. Their presence does not satisfy Condition 3.
_CONTRACT_HINTS = ("start", "open", "close", "kickoff", "commence", "cutoff", "expiry", "settle")


def classify(path: str, key: str) -> str:
    k = f"{path} {key}".lower()
    if any(h in k for h in _CONTRACT_HINTS):
        return "contract"          # scheduling metadata, not a publication clock
    return "candidate"             # possibly a publication/update clock


def main() -> int:
    if not LOG.exists():
        print(f"no probe log yet at {LOG}")
        print("The collector writes one record per successful book fetch; wait for a slate.")
        return 0

    recs = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
    if not recs:
        print("probe log is empty")
        return 0

    by_book: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_book[r.get("book", "?")].append(r)

    print("=" * 74)
    print(" FEED PROVENANCE PROBE — can Condition 3 be satisfied?")
    print("=" * 74)
    print(f" records: {len(recs):,}   span: {recs[0]['ts'][:16]} .. {recs[-1]['ts'][:16]}")

    overall_candidates = 0
    for book, rs in sorted(by_book.items()):
        n = len(rs)
        with_date = sum(1 for r in rs if r.get("server_date") is not None)
        skews = [r["recv_minus_server_s"] for r in rs
                 if r.get("recv_minus_server_s") is not None]
        cand, contract = Counter(), Counter()
        n_with_cand = 0
        for r in rs:
            hit_cand = False
            for h in r.get("payload_time_fields", []):
                kind = classify(h.get("path", ""), h.get("key", ""))
                (cand if kind == "candidate" else contract)[h["path"]] += 1
                hit_cand = hit_cand or kind == "candidate"
            n_with_cand += hit_cand
        overall_candidates += n_with_cand

        print(f"\n {book.upper()}   fetches={n:,}")
        print(f"   HTTP Date present     : {with_date:,}/{n:,} ({with_date/n*100:.1f}%)")
        if skews:
            s = sorted(skews)
            print(f"   recv minus server (s) : median {st.median(s):.2f}  "
                  f"p10 {s[int(.1*len(s))]:.2f}  p90 {s[int(.9*len(s))]:.2f}")
            print(f"   -> TRANSPORT BOUND    : network transport is at most ~{s[int(.9*len(s))]:.1f}s "
                  f"at the 90th percentile (Date has 1s granularity, so this is a bound)")
        print(f"   payload fields flagged: {sum(cand.values()) + sum(contract.values()):,}")
        if contract:
            print("     scheduling/contract (does NOT satisfy Condition 3):")
            for p, c in contract.most_common(4):
                print(f"       {p}  seen {c:,}x")
        if cand:
            print("     ** PUBLICATION CANDIDATES **")
            for p, c in cand.most_common(6):
                print(f"       {p}  seen {c:,}x")
        else:
            # rule of three: 0 hits in n trials -> 95% upper bound on rate is 3/n
            ub = 3.0 / n * 100
            print(f"     none. 0/{n:,} fetches carried a publication-clock candidate;")
            print(f"     95% upper bound on its presence rate is {ub:.3f}%.")

    print("\n" + "-" * 74)
    if overall_candidates:
        print(" VERDICT: publication-clock candidates FOUND. Next step is to test whether the")
        print(" field actually moves when the posted price moves. If it does, A4 becomes")
        print(" testable and Outcome A or B is reachable.")
    else:
        print(" VERDICT: no publication clock in any payload. The HTTP Date header bounds")
        print(" transport but cannot separate the bookmaker's pricing decision from its feed's")
        print(" publication. On this evidence Condition 3 resolves in the negative, which")
        print(" satisfies the gate via the documented-impossibility branch and points the paper")
        print(" at Outcome C.")
    print(" This is a schema question, so coverage matters more than volume: the claim is")
    print(" only as strong as the market states sampled (pregame, live, suspended, settled).")
    print("-" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
