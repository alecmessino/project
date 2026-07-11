# Engineering Prediction Log

A dated record of **engineering hypotheses** the project commits to *before* the evidence arrives,
and how they resolve. The purpose is discipline: an engineering claim is only worth trusting once a
prediction it made came true. Over a year this log is where "we understand our own system" is
earned rather than asserted.

**Rules.**
- Log the prediction when it is *made*, not after it resolves (no hindsight entries).
- State a concrete, falsifiable predicted outcome and the evidence that would confirm or refute it.
- Resolution is one of: **Confirmed**, **Refuted**, **Partial** (core right, detail wrong), or **Open**.
- Record refinements honestly — a Partial that got the mechanism right but the magnitude wrong is
  more useful than a Confirmed that was never at risk.
- A prediction is an *engineering* claim about the system. It is **not** a research finding and never
  promotes to one; research claims live behind the stopping rules.

| # | Date made | Prediction | Predicted outcome / confirming evidence | Resolution | Date resolved | Notes |
|---|---|---|---|---|---|---|
| EP-1 | 2026-07-06 | The inflated SR-1 median sync lag (~640 s) is a forward-fill artifact of a **sparse second book** (fanduel bursty, long live-quote gaps), not a synchronization problem. If the second book densifies, the cumulative median will collapse toward the poll-cadence rung. | Cumulative median sync lag falls sharply once fanduel live-quote density rises; per-book cadence unchanged. | **Confirmed (Partial on magnitude)** | 2026-07-09 | fanduel densified ~1k → ~10k live quotes; cumulative median fell 640 → 30 s. Refinement: the true floor is **0 s** (same-poll co-capture), and 30 s is a transient rung the median is collapsing *through*, not the terminal value originally implied. Mechanism confirmed; terminal value corrected. |
| EP-2 | 2026-07-06 | Moving the workflow re-arm into an `always()` step will let collection survive a **platform cancellation** (which still runs cleanup steps), eliminating the outage failure mode. | After the fix, the re-arm chain continues across cancellations with no manual intervention and no multi-hour game-hour outage. | **Confirmed** | 2026-07-09 | Runs #16→#27 re-armed 11 consecutive times, 0 failures (verified via GitHub Actions API). The only multi-hour outage in the 133 h window is the pre-fix 07-06 event. Two residual failure modes remain *uncovered* (hard runner loss; <60 min-cancel dead zone) — not yet exercised, so neither confirmed nor refuted. |
| EP-3 | 2026-07-06 | A sub-15 s median sync lag is not reachable "by collecting longer": the metric is quantized by the 30 s poll interval. | Recomputed paired lags show no values in (0, 30) s; the only sub-15 s value attainable is exactly 0. | **Confirmed** | 2026-07-09 | Independent recompute: lags ∈ {0} ∪ [30 s, ∞), min non-zero = 30.0 s. Note the *stronger* claim "the gate can never clear" was **Refuted** — median = 0 is reachable and already met within-day. This is why the sync-lag issue is logged as a **Candidate** design defect, not an established mis-specification. |

## Open predictions (awaiting evidence)

| # | Date made | Prediction | Confirming / refuting evidence | Status |
|---|---|---|---|---|
| EP-4 | 2026-07-09 | The SR-1 overlap-games count will **not** advance on collection time alone; it is stalled on **new-game enrollment**, not on maturation. | Overlap-games stays flat on days with 0 newly-enrolled games and only rises when new games first appear in the panel. | **Confirmed 2026-07-11** — overlap rose 30 → 37 (07-10) → 45 (07-11) as new games enrolled on the new slate days (E-015); it did not advance on collection time alone. |
| EP-5 | 2026-07-09 | Pinnacle's zero live quotes are a **configuration/subscription/auth** condition, not a transient feed outage, so it will stay stillborn until the collector integration is changed. | A read of the pinnacle adapter path + a controlled fetch explains the 6-pregame-rows-then-silence pattern; collecting longer does not produce a live pinnacle quote. | Open — see Engineering Debt ED-1 |
