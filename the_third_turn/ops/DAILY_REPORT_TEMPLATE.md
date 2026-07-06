# Daily Research Operations Review — standing format

This is the canonical structure for the daily report. It is an **operations** review: the default
assumption is that nothing scientific changed. Report health, gate state, and growth; treat
research findings as absent unless a predefined gate has cleared and the evidence survives the
project's own safeguards. If nothing meaningful changed, say so plainly.

## Standing rules

- Be skeptical; assume every apparent signal is an artifact until proven otherwise.
- Never confuse more data with more evidence; separate engineering progress from scientific progress.
- **Liveness first.** Compare the latest checkpoint timestamp to wall-clock. A checkpoint older
  than ~45 min while games are live is an incident, not a footnote. The health report's own
  "running normally" line is written by the collector and freezes when the collector dies, so it is
  not a liveness signal on its own.
- Do not recommend new analysis unless a verification or research gate has cleared. Prefer:
  continue collecting, fix infrastructure, or wait.

## Sections (in order)

1. **Infrastructure Health** — collector / protocol / dataset versions; latest checkpoint and its
   age; is collection running now; failed Actions runs (distinguish normal re-arm `cancelled`
   handoffs from real `failure`s); integrity (rows, malformed, missing, duplicate, future-ts);
   schema drift. State plainly whether the collector is healthy.
2. **Verification Gates** — for each gate: current status, change since yesterday, evidence,
   and whether it remains BLOCKED / PENDING / VERIFIED. No speculation; observable changes only.
3. **Dataset Growth** — objective, measurable deltas only (games, live innings, books, simultaneous
   live pairs, marketStatus values, alternate coverage). Growth is not evidence.
4. **Trend Dashboard** *(permanent)* — day-over-day movement in key operational metrics plus an
   overall trajectory of **Improving / Stable / Regressing**. Data source and method below.
5. **Research Findings** — assume none. Elevate to a Finding only if it survives confounds,
   measurement checks, reproduction, is economically meaningful, and would still matter if it
   weakened the original hypothesis. Otherwise: Observation / Candidate / Artifact / Rejected.
6. **Challenges to Existing Conclusions** — actively try to falsify Paper 1, the Protocol, the
   safeguard registry, and the operational assumptions. If nothing does, say so explicitly.
7. **Emerging Opportunities** — what new data has made possible; split Available now vs Needs more data.
8. **Recommendations** — at most three; prefer continue / fix / wait.
9. **Executive Summary** — exactly four lines: Infrastructure / Verification / Research /
   Recommended next action.

## Trend Dashboard — data source and method

Objective series lives in `output/metrics_history.jsonl`, upserted once per UTC day by
`collection_health.py` (latest snapshot of the day wins) and banked every checkpoint. Render with:

```
python the_third_turn/collection_health.py --trend
```

It prints day-over-day deltas and the trajectory verdict. Paste or summarize its output into
section 4.

**Metrics tracked:** SR-1 progress %, books quoting live, overlap games, live games seen, median
sync lag; plus cumulative growth counters (book-panel rows, simultaneous pairs, team-total rows);
plus integrity-clean and fix-verification flags.

**Trajectory rule** (health and gate-progress drive it; cumulative counters are shown but do **not**
vote, because they only ever rise):

- **Regressing** if integrity broke, fix-verification was lost, or collection stalled (no new
  book-panel rows since the prior day) — any one forces Regressing regardless of the counters.
- Otherwise net the gate/health signals: SR-1 %, books-live, overlap games, live games (up is good)
  and median sync lag (down is good). Net positive → **Improving**; zero → **Stable**; negative →
  **Regressing**.

The stall rule means a repeat of the 2026-07-06 outage would surface as **Regressing** on the next
day's dashboard even if every stored number still looked clean.
