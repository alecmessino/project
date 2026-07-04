# The Third Turn Protocol

**A predictive signal should be evaluated against the market's own forecast, not merely against the
outcome.**

The Third Turn Protocol is a fixed sequence of tests of increasing stringency for deciding whether
a candidate predictive signal carries information *beyond an existing forecast*. It is
domain-general: the "forecast" may be a betting line, an analyst consensus, a weather model, or any
incumbent predictor; the "signal" is any variable proposed to improve on it. A signal is carried
forward only until it is eliminated, and you report **the rung at which it is eliminated**.

```
            candidate signal
                   │
   1. Signal ──────────────── associated with the outcome at all?      no ─▶ discard
   2. Robustness ──────────── survives specification / threshold / sub-sample changes?   no ─▶ discard
   3. Out-of-sample ───────── survives cross-validation on held-out units?   no ─▶ discard
   4. Debiasing ──────────── survives when re-measured before treatment (no selection)?   no ─▶ artifact
   5. Conditional testing ── adds value on average, not only inside a hand-picked context?   no ─▶ discard
   6. Forecast encompassing ─ improves a model that already contains the incumbent forecast?   no ─▶ ALREADY PRICED
   7. Transfer function ───── (markets only) does the forecast move by the correct magnitude?
                   │
               Decision
```

## The rungs

1. **Signal.** Establish an in-sample association between the candidate and the outcome. This is
   the weakest possible evidence and never sufficient on its own.
2. **Robustness.** Vary the specification, thresholds, and sub-sample. A signal that depends on one
   arbitrary cutoff, or lives only in the recent tail of the sample, is rejected.
3. **Out-of-sample.** Re-estimate under cross-validation (we use leave-one-group-out, grouping by
   game). Judge the signal only on units not used to fit it.
4. **Debiasing.** Replace any *post-treatment* measurement — one defined only on a subsample that
   the outcome itself selects — with a *pre-treatment* analogue. A signal that survives in-sample
   but vanishes when measured before treatment is a selection artifact, not an effect.
5. **Conditional testing.** Check whether the signal earns its keep only inside a specific context.
   A conditional edge that does not survive multiple-comparison scrutiny is discarded.
6. **Forecast encompassing** *(the pivotal rung)*. Regress the outcome `Y` on the incumbent
   forecast `B`, on the signal `X`, and on both; the incumbent **encompasses** the signal if
   `Y ~ B + X` does not improve out-of-sample on `Y ~ B`. Equivalently, regress the incumbent's
   forecast error `Y − B` on `X`: if `X` cannot predict the error out-of-sample, the signal is
   already reflected in the forecast. This is the highest evidentiary standard in the protocol,
   because it conditions on the incumbent forecast rather than on realized outcomes alone.
7. **Transfer function** *(markets only)*. For a market forecast, ask not whether the price
   reflects the signal but whether it moves by the *correct magnitude* when the signal changes.
   Compare the realized change in the forecast target to the change in the price. A uniform
   attenuation across event types indicates a measurement/latency artifact; a per-event asymmetry
   is a candidate inefficiency.

## Reporting a result

Report the earliest rung your signal fails, with the diagnostic that failed it. Only a signal that
clears rung 6 (and, for markets, is priced by the wrong magnitude at rung 7) carries information
the incumbent forecast does not already hold. See `../benchmark/examples/report_template.md` for the
format, and `../benchmark/dataset/reference_results.md` for the ten reference signals evaluated in
the accompanying paper — all eliminated at or before forecast encompassing.

## Safeguards and gates

The rungs above are the spine; the specific checks that make each rung trustworthy are catalogued
with IDs in [`safeguards.md`](safeguards.md), and each traces to a logged failure, a review
requirement, or a documented design risk recorded in
[`../decisions/RESEARCH_DECISIONS_LOG.md`](../decisions/RESEARCH_DECISIONS_LOG.md). Analyses that
depend on data volume (e.g. cross-book leadership) are gated by [`stopping_rules.md`](stopping_rules.md).
Papers may cite safeguards by ID ("following S-05 and S-11…").

## Provenance

Introduced in Messino (2026), *Forecast Encompassing as a Test of Predictive Signals: Evidence from
Live MLB Totals Markets*. The forecast-encompassing rung follows Chong & Hendry (1986); the AUC
diagnostics follow Hanley & McNeil (1982). This document is the canonical definition of the
protocol; cite it via `../benchmark/CITATION.cff`.
