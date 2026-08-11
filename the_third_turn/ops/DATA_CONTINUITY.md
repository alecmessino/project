# Data Continuity Record

The reproducibility record for **gaps in the collected panels**. A gap is not a finding and not a
defect in any estimate by itself, but a dataset described as continuously collected must state where
it is not continuous, and must demonstrate — not assume — which analyses that touches.

Two gaps are known. Both are recorded here with the same six fields, so a later reader can decide
for themselves whether a gap matters to a result they care about.

---

## Gap 1 — 2026-07-12 → 2026-07-15 (~56.6 h)

| Field | Record |
|---|---|
| **Window** | last row `2026-07-12T22:56:30Z`; first row after `2026-07-15T07:34:10Z` |
| **Duration** | ~56.6 hours (2.36 days); calendar days 07-13 and 07-14 absent entirely |
| **Mechanism** | **Not established.** This gap predates the run-log review that identified Gap 2 and was not detected at the time. |
| **Why monitoring failed** | Same structural cause as Gap 2 — collector health was self-reported by the collector, so a stopped collector reported nothing rather than reporting a stop. No external observer existed. |
| **Remediation** | Covered by the Gap 2 remediation below; no gap-specific fix, because the mechanism is unknown. |
| **Live data truncated?** | **Yes.** Collection stopped at 22:56 UTC, mid-slate. Three games had live quotes inside the final hour: `TOR@SD`, `COL@SF`, `ARI@LAD`. These games are partially observed. |

**Discovered** 2026-08-10, while verifying Gap 2. It was found by enumerating distinct calendar days
present in `book_panel.jsonl` rather than by any alarm, which is itself the point.

---

## Gap 2 — 2026-08-06 → 2026-08-10 (101.9 h)

| Field | Record |
|---|---|
| **Window** | last row `2026-08-06T16:02:18Z`; collection restarted `2026-08-10T21:53:51Z` (run #151) |
| **Duration** | 101.9 hours (4.24 days) |
| **Mechanism** | Established from the run log. Run #150's self-re-arm dispatch received `HTTP 500` — `{"message":"Failed to run workflow dispatch","status":"500"}` — a transient GitHub API error. The re-arm step was `curl -s … \|\| true` with no status check and no retry, so it printed `re-armed after 208 min`, concluded **success**, and the chain ended. |
| **Why monitoring failed** | The failure was *structurally invisible*. The step could not fail: its exit status was independent of whether the dispatch succeeded. The job concluded normally, the workflow remained `active`, and the last checkpoint commit looked like every other one. Every available signal reported health, because every available signal was produced by the thing that had stopped. |
| **Remediation** | (a) the re-arm now requires `HTTP 204`, retries 5× with backoff, and exits non-zero so a failure is visibly red; (b) a watchdog workflow on an hourly cron, in concurrency group `ttt-watchdog` (never `ttt-live`, so it cannot cancel the collector it guards), relaunches the collector whenever no live run is in flight. The watchdog is on `master` because GitHub executes `on: schedule` only from the default branch. |
| **Live data truncated?** | **No.** See the determination below. |

**Post-remediation verification.** Run #151 started `2026-08-10T21:53:51Z` and checkpointed on its
normal ~16-minute cadence (commits at 00:50, 01:06, 01:22, 01:38, 01:54, 02:10). Collection is
confirmed restored by banked data, not by the collector's own health report.

---

## Determination: does either gap affect an already-reported estimate?

This is the question that matters, and it is answered by inspection rather than by argument.

**Gap 2 does not affect E-021.** The provenance sample spans `2026-08-05T03:18` to
`2026-08-06T15:57`, ending four minutes before the outage. The relevant risk is a market observed
part-way through its live window and then cut. There was none: in the final hour before the stop the
panel holds 145 rows, of which **zero are live**, and **no market's last observation is a live one**
within thirty minutes of the cutoff. The outage began at 16:02 UTC — around midday Eastern, before
first pitch. The sample is bounded by the outage; it is not truncated by it. E-021's four answers
stand unmodified.

**Gap 2 does not affect Paper 1.** Paper 1's sample is June data, frozen, and temporally disjoint
from both gaps (already established independently as E-011).

**Gap 1 does touch the July analyses.** E-016, E-017 and E-018 draw on the July window, which
contains Gap 1. Two distinct effects, worth separating:

- *Missing games* (07-13, 07-14 entirely absent). These games are not in the sample at all. This
  reduces coverage but does not bias a per-game statistic unless absence correlates with the
  quantity measured, and a platform outage has no plausible route to such a correlation.
- *Truncated games* (`TOR@SD`, `COL@SF`, `ARI@LAD` on 07-12). These are partially observed, and E-016
  and E-017 compute per-game intervals between main-line changes. A game cut short contributes a
  shorter observation window. The direction of any resulting distortion is not obvious and has not
  been quantified.

We do not treat this as invalidating those entries, and we also do not clear them. E-017 already
established that the *magnitude* of the book-heterogeneity result is not robust to the main-line
definition (ratios spanning 1.1×–9.5×); a handful of truncated games is a second-order concern
against a first-order one already on the record. The honest status is that E-016/E-017/E-018 carry
one additional unquantified qualification, recorded here.

---

## Standing rule

**Gaps are marked, not repaired.** We do not compensate for lost days by extending an analysis
window opportunistically, relaxing a sample requirement, or backfilling from another source. The
instrument stopped; the record says so; collection resumes. Any of those compensations would let an
infrastructure failure reach into a sample definition, which is precisely the kind of silent
researcher degree of freedom the pre-registration in Paper 2 §6.6 exists to prevent.
