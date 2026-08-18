# Data Continuity Record

The reproducibility record for **gaps in the collected panels**. A gap is not a finding and not a
defect in any estimate by itself, but a dataset described as continuously collected must state where
it is not continuous, and must demonstrate — not assume — which analyses that touches.

Three gaps are known. Each is recorded here with the same fields, so a later reader can decide for
themselves whether a gap matters to a result they care about. Two of the three are **persistence
failures rather than collection outages**: the collector ran and collected, and what it gathered did
not reach the repository.

---

## Gap 1 — 2026-07-12 → 2026-07-15 (~56.6 h)

| Field | Record |
|---|---|
| **Window** | last row `2026-07-12T22:56:30Z`; first row after `2026-07-15T07:34:10Z` |
| **Duration** | ~56.6 hours (2.36 days); calendar days 07-13 and 07-14 absent entirely |
| **Mechanism** | **Species established 2026-08-18; specific cause not recoverable.** This was a **persistence failure, not a collection outage** — the same species as Gap 3. Runs **#40 through #56** cycled continuously on the normal ~5.5 h cadence across 07-12, 07-13, 07-14 and 07-15 with no break in the chain, while **zero checkpoint commits** landed between 07-12 and 07-16. The collector was running; nothing reached the branch. The 100 MiB ceiling that caused Gap 3 is **ruled out** — the panel was roughly 35 MB at the time. The specific reason the pushes failed is **not recoverable**: the July checkpoint ran every git command under `-q` inside an `&&` chain with no error surface, so the run logs, which are still retrievable, record nothing about it. The blindness that caused the gap is the same blindness that prevents diagnosing it. |
| **Why monitoring failed** | Same structural cause as Gap 2 — collector health was self-reported by the collector, so a stopped collector reported nothing rather than reporting a stop. No external observer existed. |
| **Remediation** | Covered by the Gap 2 remediation below; no gap-specific fix, because the mechanism is unknown. |
| **Live data truncated?** | **Yes.** Persistence stopped at 22:56 UTC, mid-slate, so the last rows banked are partial. Three matchups had live quotes inside the final persisted hour: `TOR@SD`, `COL@SF`, `ARI@LAD`. For any analysis the effect is identical to truncation, whatever the collector was doing at the time. |

**Discovered** 2026-08-10, while verifying Gap 2. It was found by enumerating distinct calendar days
present in `book_panel.jsonl` rather than by any alarm, which is itself the point.

**Reclassified 2026-08-18.** Recorded here in full because it changes what this gap means. Two of the
three known gaps are now persistence failures rather than collection outages, and in both the
collector reported healthy throughout. The record previously implied a collector that stopped; the
evidence says a collector that ran and was not believed by the repository. Gap 1 also predates the
watchdog entirely, so nothing external was watching either the process or the data.

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

## Gap 3 — 2026-08-14 → 2026-08-17 (~79 h) · **persistence failure, not a collection outage**

This one is a different species from Gaps 1 and 2, and the distinction is the whole point.

| Field | Record |
|---|---|
| **Window** | last checkpoint on the branch `2026-08-14T15:32Z`; discovered `2026-08-17T22:17Z` |
| **Duration** | ~79 hours |
| **Was the collector running?** | **Yes, throughout.** Runs cycled normally and the hardened re-arm worked perfectly (`re-armed after 334 min (attempt 1)`). |
| **Was it collecting?** | **Yes.** The run log at 21:17 on 08-17 shows `book_panel.jsonl: 679,911 rows, last 2026-08-17T21:13:15`, both books quoting `3.3m ago`, `HEALTH_OK: yes`, integrity clean. The branch held **672,035** rows, so that run had accumulated ~7.9k unpushed rows at the time of the reading. |
| **Mechanism** | **GitHub hard-rejects any file over 100 MiB (104,857,600 bytes).** `book_panel.jsonl` grew into that ceiling: the last checkpoint that landed, 08-14T15:32, left it at **104,857,591 bytes — nine bytes under the limit**. Every checkpoint after that pushed it over, and the push was rejected. `-q` and the `&&` chain swallowed the rejection. Verified by tracing the blob size across the final checkpoints: 104,793,631 → 104,849,925 → 104,850,548 → 104,857,591, then nothing. |
| **Why monitoring failed** | Twice over. The checkpoint could not fail: its exit status was independent of whether data reached the branch. And the watchdog — added after Gap 2 — asked *"is a run in progress?"*, which stayed **yes** the entire time. It stood down hourly, exactly as designed. A watchdog that asks whether something is running cannot see a process that is running and accomplishing nothing. |
| **Remediation** | Checkpoint now uses `git pull --rebase --autostash`, captures both command outputs, and emits `::warning` per attempt and `::error` on exhaustion. Watchdog now reads the last commit on the collector branch and goes **red past 180 minutes** without one; it deliberately does **not** relaunch on staleness, because a restart discards whatever the live run holds unpushed. |
| **Live data truncated?** | **All of it, repeatedly.** Each ~5.5 h run started from the 08-14 branch state, gathered its own window of roughly 8k rows, and discarded them on exit. Successive runs covered *different* windows, so the aggregate loss is the whole 79 h, not one run's worth. Nothing is recoverable: no unpushed copy survives a runner. |

**Why it happened exactly when it did.** Nothing changed in the code or the platform on 08-14. The
panel simply crossed a hard limit that had always been there. That is why the failure looks abrupt
and total rather than intermittent: below the ceiling every push succeeds, above it every push
fails, and the file crossed over between one checkpoint and the next.

**Correction, 2026-08-18 (cause).** This entry first attributed the failure to a dirty worktree
defeating `git pull --rebase`, and a fix was shipped on that basis. **That diagnosis was wrong** —
plausible, reproducible in a sandbox, and not the cause. The pull was never the failing step; the
push was. The `--autostash` change is retained because it is correct hygiene for a tree the daemon
is actively writing, but it fixed nothing. Recorded rather than overwritten because a wrong
diagnosis that briefly looked right is exactly the thing this file exists to preserve.

**Remediation (actual).** git no longer stores the monolithic panels at all. `panel_shards.py`
splits them into fixed-size shards (≤32 MiB, cut on whichever of a line or byte cap is reached
first) which is what git tracks; the runner reassembles the single file after checkout, so every
analysis script still reads `output/book_panel.jsonl` unchanged. Round-tripping is byte-identical by
construction — sharding is by position, not by date, so it assumes nothing about row order. A useful
side effect: appends touch only the final shard, so each checkpoint commits a small delta instead of
restating 100 MiB.

**Correction, 2026-08-18.** This entry first recorded the branch as holding 594,643 rows and each
run as losing ~85k. Both were wrong: 594,643 was a stale local count taken before fetching the
08-14 checkpoints. The branch held **672,035**. The corrected per-run figure is ~8k rows. The
finding — that collection ran and did not persist for 79 h — is unchanged.

**Same failure class as Gap 2, one layer down.** Gap 2 was a re-arm that could not fail. This was a
checkpoint that could not fail. In both cases every available signal was generated by the component
that had stopped working, and in both cases the fix is the same shape: make the step capable of
failing, and make something outside it check the outcome rather than the activity.

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
