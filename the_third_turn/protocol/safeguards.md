# Safeguards registry

Every safeguard in the Third Turn Protocol has an ID and a **provenance**: the logged failure,
external-review requirement, or documented design-time risk that made it necessary. A safeguard
exists because something concrete demanded it — never because "more checks sound safer." Papers may
cite safeguards by ID
("following S-03 and S-05…"); `../decisions/RESEARCH_DECISIONS_LOG.md` records the provenance each
one came from.

**Rule for adding a safeguard:** it must trace to one of exactly three kinds of provenance — (a) a
real, logged failure; (b) a specific external-review requirement; or (c) a *documented design-time
interpretation risk* (a concrete way a result could be misread, recorded when the analysis was
built). Category (c) is the narrowest and most easily abused, so it is allowed only when the risk
is written down and points at a specific misreading; exactly one safeguard (S-12) currently rests
on it. No entry may be added on a vague or speculative rationale.

| ID | Safeguard | What it does | Born from (provenance) |
|---|---|---|---|
| S-01 | Out-of-sample validation (leave-one-game-out) | Judge a signal only on games not used to fit it | TTOP/gradient showed an in-sample edge that fired below breakeven out-of-sample |
| S-02 | Robustness sweep | Vary specification, threshold, sub-sample, and recency before believing | Drop→Under looked strong cumulatively (60–63%) but died under banding, snapshot-inning change, and a recency split |
| S-03 | Debias post-treatment variables | Re-measure any outcome-selected variable in a pre-treatment window | Velocity drop (1st→3rd time) scored AUC 0.61 only because it exists solely for starters who survived to be shelled; pre-treatment AUC 0.52 |
| S-04 | Conditional-testing discipline | Require value on average, not only inside a hand-picked context; isolate the proposed mechanism; guard multiple comparisons | Alt-line skew, early-run anchoring, and weather/park each claimed a context-only edge (all priced); the bullpen-fatigue test was isolated to the pen's own innings and found no effect |
| S-05 | Forecast encompassing | Condition on the incumbent forecast; test whether the signal improves it, not whether it predicts the outcome | Features predicted runs (R² 0.279) yet added nothing to the market (ΔR² −0.017); predicting the outcome ≠ improving an existing forecast |
| S-06 | Nested forecast-comparison inference | Clark–West statistic + block-bootstrap CI for the encompassing gain | Reviewer: a raw OOS-MSPE comparison is biased toward the small model; the central null needs formal inference and an interval |
| S-07 | Cluster-aware power / MDE | Report the minimum detectable effect, clustered by game, for every null claim | Reviewer: a paper built on nulls must state what it was powered to detect (MDE ≈ 0.007 snapshot → 0.10 game-clustered) |
| S-08 | Functional-target (median-vs-mean) check | For a skewed target, check median(error) and the error's slope on the forecast before calling a level a "bias" | The +0.49 mean book error looked like market bias; median 0.00, skew +1.23, slope +0.01 → mean–median gap, an intercept, not bias |
| S-09 | Estimator/penalty sensitivity | Repeat the conclusion across OLS ↔ ridge (penalty sweep) | Reviewer: confirm the encompassing result is not an artifact of the shrinkage penalty (invariant 0→100) |
| S-10 | Equal-frequency lead-lag estimator | Resample all series to a common cadence before any lead-lag / who-moved-first claim | Naïve "reached level first" said FanDuel leads Bovada 73:5 — a pure 3.7× sampling-density artifact; density-neutral r's were indistinguishable |
| S-11 | Simultaneous-live / synchronization requirement | No cross-book claim until quotes are contemporaneous (both books live in one tight window) | The 61% "divergence" was 90% pregame with zero simultaneous live quotes; the interesting object was never observed |
| S-12 | Transfer-function magnitude check | Read the *asymmetry* of the response ratio across event types, not its absolute level | **Design-time interpretation risk** (category c): a uniform sub-1 response ratio would be misread as a per-event edge when it is a single-source low-pass filter — the paper guards this explicitly (§4). Not born from a logged failure or a review item. |
| S-13 | Claims conditioned on measurement resolution | Bind every efficiency claim to the instrument ("one-minute, single-book resolution") | Reviewer: instrument resolution ≠ market resolution; a sub-minute or cross-book lag would masquerade as efficiency |
| S-14 | Quote-lifecycle / staleness filter *(provisional)* | Distinguish fresh from stale/suspended quotes before comparison | The divergence probe found ~1-hour forward-fill staleness; **adopted going forward, pending live overlap** — the daemon does not yet log lifecycle fields |

## Status of the registry

S-01 – S-13 are **active**: each is applied in Paper 1 or in the microstructure probe. All but one
trace to a logged failure or an external-review requirement; the exception is **S-12**, which rests
on a documented design-time interpretation risk (category c above) rather than a logged failure —
called out here so the accounting stays exact. S-14 is **provisional**: its trigger (quote
staleness) is real, but the field it needs is not yet collected, so it is a forward commitment
rather than an applied check. Provisional entries are marked as such and are not cited as if they
were in force.

## How the registry stays honest

- Every ID appears in `../decisions/RESEARCH_DECISIONS_LOG.md` against the failure, review
  requirement, or documented design risk that created it.
- A safeguard is retired (not deleted — struck through with a reason) only if the failure mode it
  guards is shown not to occur in this domain.
- The registry is append-mostly and small on purpose; its size should track the number of *distinct
  failure modes encountered*, not the ambition of the method.
- Rung 1 of the protocol (Signal) has **no registered safeguard by design**: a bare in-sample
  association is the entry gate, not something to be protected — every safeguard exists to *doubt*
  it. So rungs 2–7 map to safeguards and rung 1 deliberately does not.
