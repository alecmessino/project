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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from shared_piping.provenance import key_is_timeish  # noqa: E402
LOG = HERE / "output" / "provenance_probe.jsonl"

# Fields that are about the CONTRACT (when the game starts, when the market closes) rather
# than about publication. Their presence does not satisfy Condition 3.
_CONTRACT_HINTS = ("start", "open", "close", "kickoff", "commence", "cutoff", "expiry", "settle")


def classify(path: str, key: str, value_kind=None) -> str:
    """candidate | contract | not-a-time.

    Records written before the token fix carry name matches on incidental substrings
    ("numMarkets", "hasAttachments"). Re-apply the corrected name test at read time so
    historical records are graded by the same rule as new ones.
    """
    if value_kind is None and not key_is_timeish(key):
        return "not-a-time"
    k = f"{path} {key}".lower()
    if any(h in k for h in _CONTRACT_HINTS):
        return "contract"          # scheduling metadata, not a publication clock
    return "candidate"             # possibly a publication/update clock


# The pre-registered stopping rule (GD-18). Fixed before any probe data arrived.
REQUIRED_STATES = ("pregame", "live")     # payload shape can differ by market state
MIN_PER_STATE   = 200                     # fetches per book per state


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

    print("=" * 76)
    print(" FEED PROVENANCE PROBE — can Condition 3 be satisfied?")
    print("=" * 76)
    print(f" records: {len(recs):,}   span: {recs[0]['ts'][:16]} .. {recs[-1]['ts'][:16]}")

    overall_candidates = 0
    coverage_ok = True

    for book, rs in sorted(by_book.items()):
        n = len(rs)
        with_date = sum(1 for r in rs if r.get("server_date") is not None)
        skews = [r["recv_minus_server_s"] for r in rs
                 if r.get("recv_minus_server_s") is not None]
        states = Counter(r.get("state", "unknown") for r in rs)

        # candidate fields, and whether their VALUE ever changed across fetches
        cand, contract = Counter(), Counter()
        values: dict[str, set] = defaultdict(set)
        n_with_cand = 0
        for r in rs:
            hit = False
            for h in r.get("payload_time_fields", []):
                kind = classify(h.get("path", ""), h.get("key", ""), h.get("value_kind"))
                if kind == "not-a-time":
                    continue
                (cand if kind == "candidate" else contract)[h["path"]] += 1
                if kind == "candidate":
                    hit = True
                    if len(values[h["path"]]) < 500:
                        values[h["path"]].add(h.get("sample"))
            n_with_cand += hit
        overall_candidates += n_with_cand

        print(f"\n {book.upper()}   fetches={n:,}")
        print(f"   market states sampled : " +
              "  ".join(f"{k}={v:,}" for k, v in sorted(states.items())))
        short = [s for s in REQUIRED_STATES if states.get(s, 0) < MIN_PER_STATE]
        if short:
            coverage_ok = False
            print(f"   COVERAGE INCOMPLETE   : need >= {MIN_PER_STATE} each of "
                  f"{', '.join(REQUIRED_STATES)}; short on {', '.join(short)}")
        else:
            print(f"   coverage              : OK (>= {MIN_PER_STATE} in every required state)")

        print(f"   HTTP Date present     : {with_date:,}/{n:,} ({with_date/n*100:.1f}%)")
        if skews:
            s = sorted(skews)
            print(f"   recv minus server (s) : median {st.median(s):.2f}  "
                  f"p90 {s[int(.9*len(s))]:.2f}")
            print(f"   -> TRANSPORT BOUND    : <= ~{s[int(.9*len(s))]:.1f}s at p90. Date has 1s "
                  f"granularity, so this is a coarse bound, not an estimate.")
        if contract:
            print("   scheduling/contract fields (do NOT satisfy Condition 3):")
            for pth, c in contract.most_common(4):
                print(f"       {pth}  seen {c:,}x")
        if cand:
            print("   ** PUBLICATION CANDIDATES **")
            for pth, c in cand.most_common(6):
                nv = len(values[pth])
                verdict = ("VARIES across fetches -> test whether it tracks price revisions"
                           if nv > 1 else "CONSTANT -> not a publication clock")
                print(f"       {pth}  seen {c:,}x  distinct values {nv}  [{verdict}]")
        else:
            ub = 3.0 / n * 100
            print(f"   no publication-clock candidate in 0/{n:,} fetches;")
            print(f"   95% upper bound on presence rate {ub:.3f}% (rule of three).")

    print("\n" + "-" * 76)
    if overall_candidates:
        print(" VERDICT: candidates FOUND. Condition 3 is not satisfied by presence alone: a field")
        print(" only qualifies once it is shown to MOVE when the posted price moves.")
        print("")
        print(" That test HAS NOW BEEN RUN — see market_panel_report.py and E-021. Result: bovada's")
        print(" `lastModified` moves on 100% of price changes but also on 98.6% of transitions with")
        print(" no price change, so it is an event-level heartbeat rather than a per-market")
        print(" publication stamp, and 28.4% of its transitions arrive out of order because the CDN")
        print(" serves objects of differing age. It can EXCLUDE revisions; it cannot date them.")
        print(" Do not read the candidate count below as progress toward Outcome A.")
    elif not coverage_ok:
        print(" VERDICT: WITHHELD. No candidate found so far, but the required market states")
        print(" are not yet covered. Declaring Outcome C now would rest on payload shapes we")
        print(" have not sampled. Keep collecting; this is the pre-registered stopping rule")
        print(" (GD-18) doing its job.")
    else:
        print(" VERDICT: coverage satisfied and no publication clock in any payload. The HTTP")
        print(" Date header bounds transport but cannot separate the bookmaker's pricing")
        print(" decision from its feed's publication. Condition 3 resolves in the negative via")
        print(" the documented-impossibility branch, and the paper reports Outcome C.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
