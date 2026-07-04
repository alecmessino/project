# Report template — a new signal against the Third Turn Protocol

Copy this block, fill it in, and report the **earliest rung your signal fails**. A signal that
reaches rung 6 and improves out-of-sample on the incumbent forecast is a genuinely new result.

```
Signal:            <name and one-line definition>
Domain / dataset:  <Third Turn Benchmark Dataset v1 | your dataset>
Incumbent forecast B: <what existing forecast you condition on>
Outcome Y:         <what you predict>

1. Signal              PASS / FAIL   <in-sample association, effect size>
2. Robustness          PASS / FAIL   <specification / threshold / sub-sample checks>
3. Out-of-sample       PASS / FAIL   <CV scheme, held-out metric>
4. Debiasing           PASS / FAIL   <pre- vs post-treatment measurement, if applicable>
5. Conditional testing PASS / FAIL   <average vs context-only, multiple-comparison note>
6. Forecast encompassing PASS / FAIL <ΔR²(B+X − B) OOS; (Y−B)~X OOS R²>   ← the pivotal rung
7. Transfer function   PASS / FAIL / N/A   <response ratio by event, if a market>

Eliminated at rung:   <n>
Verdict:              <already priced / selection artifact / genuinely incremental / ...>
Notes:
```

## Worked example (from the reference set)

```
Signal:            Velocity decline — starter mph drop as a fatigue proxy
Domain / dataset:  Third Turn Benchmark Dataset v1
Incumbent forecast B: sharp live game total → remaining runs
Outcome Y:         remaining runs (and P[team scores > 4.5])

1. Signal              PASS   facing-team runs rise with starter velocity drop
2. Robustness          PASS   holds across tiers
3. Out-of-sample       PASS   AUC 0.61 with the 1st→3rd-time velocity drop
4. Debiasing           FAIL   drop is post-treatment (defined only if the starter survived);
                              re-measured in a pre-treatment early window, AUC → 0.52 (coin flip)

Eliminated at rung:   4 (Debiasing)
Verdict:              selection artifact, not a fatigue effect
```
