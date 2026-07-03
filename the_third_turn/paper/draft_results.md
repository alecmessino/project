# Results (Pass 1 draft — v2, brief order)

> **Drafting rules for this pass:** lead with the strongest evidence, then show how the
> supporting analyses explain it (a brief, not a chronicle). Every paragraph points to exactly
> one figure, opens from the evidence ("Figure X shows…"), and every number is the committed
> value in `output/*.json`. Language is bound to the experiment; findings are an **empirical
> boundary**, never a "negative result." Figure files are content-named; the manuscript assigns
> numbers, shown here in brackets.

## Research Question

Do publicly observable baseball state variables contain incremental predictive information about
remaining runs beyond the forecast embedded in a sharp live betting market?

Figure 4 answers this question directly.

---

Figure 4 [`forecast_encompassing`] demonstrates that publicly observable baseball variables
provide no measurable incremental predictive information beyond the live market. Across 2,505
half-inning snapshots, a leave-one-game-out forecast of remaining runs from our full feature set
achieves an out-of-sample R² of 0.279; the market-implied remaining total alone achieves 0.304;
and combining the two changes R² by −0.017 — adding the features to the market does not improve,
and slightly degrades, the forecast. The right panel shows the per-feature version of the same
test (E+): each variable's individual incremental R² beyond the market falls inside a ±0.003
band (best case, bullpen, at +0.0018; velocity, starter tier, temperature, wind, and park at or
below zero), so no single variable hides behind the others. As the sharpest test, we regress the
book's forecast error — realized minus market-implied remaining runs — directly on the features:
it is not predictable out-of-sample, R² = −0.037. This is the central empirical result of the
study.

Figure 2 [`hypothesis_elimination`] shows that this boundary is not a property of one variable
but of the entire battery. The figure arranges ten candidate hypotheses drawn from the public
handicapping literature — times-through-order, velocity decline, bullpen-fatigue multipliers,
drop reversion on both sides, alternate-line skew, early-run anchoring, weather/park context, a
remaining-runs fatigue term, and forecast encompassing — against five escalating gates: initial
signal, robustness, out-of-sample, market test, verdict. The pattern of elimination is the
finding: several hypotheses clear an in-sample signal, fewer survive robustness, fewer survive
out-of-sample cross-validation, and none clears the market test. Because the gate of elimination
varies by row — times-through-order and the velocity signal die at robustness, drop-reversion
(Over) and forecast encompassing at out-of-sample, the context hypotheses at the market test — no
single artifact (a coding error, one anomalous month, one mis-specified model) can be the common
cause. The complete battery, with each hypothesis's motivation and mode of elimination, is
summarized in Appendix Table A1.

Figure 3 [`incremental_information_funnel`] quantifies the attrition as a funnel: of ten
hypotheses tested, nine produce a detectable in-sample association with runs, three survive
out-of-sample validation, and zero add information beyond the market or clear a profitability
threshold. The collapse between "survives out-of-sample" (three) and "adds information beyond the
market" (zero) is the paper's pivot: predicting runs is common; predicting the market's error is
the empirical boundary. The funnel counts are derived directly from the Figure 2 matrix, so the
two figures cannot diverge.

Figure 5 [`velocity_post_treatment_bias`] explains why one hypothesis appeared to survive before
it was eliminated, and in doing so illustrates a general statistical principle. A model that adds
a starter's velocity decline measured from the first to the third time through the order raises
the out-of-sample AUC for "team scores above 4.5" from a tier-only baseline of 0.420 to 0.610 —
an apparently large gain. But that velocity-drop variable is *post-treatment*: it is defined only
for starters who survived long enough to face the order a third time, precisely the starters
already being hit. Re-measuring velocity decline within a pre-treatment early window (first twenty
pitches versus the next twenty) collapses the AUC to 0.524, whose Hanley–McNeil confidence
interval straddles the 0.500 coin-flip line. The apparent 0.61 signal was survivorship, not
fatigue — a conditioning artifact that the escalating protocol is designed to catch.

Figure 6 [`transfer_function`] turns from whether the market prices information to whether it
prices it by the right *amount*. For each of 6,414 in-game events we compute the true change in
run expectancy (ΔRE, from a base-out RE24 table plus runs scored) and the converged move in the
live total five minutes later (ΔBook). Plotted against each other, every positive-run event type
lies on a single common slope of approximately 0.74 through the origin; the response ratios for
the higher-frequency events cluster in a narrow 0.63–0.84 band (walk 0.63, double 0.64, single
0.72, home run 0.81, triple 0.84) with no ordering by event magnitude. That uniformity is
evidence about the *measurement pipeline* — a single Pinnacle-grade source sampled at roughly
one-minute cadence acts as a low-pass filter that attenuates every shock by the same factor —
rather than a per-event mispricing an edge could exploit. (Hit-by-pitch, n = 115, sits below the
band; pitching changes move the line near zero, but RE24 cannot benchmark reliever quality, so we
exclude them from the elasticity claim.)

Figure 7 [`market_calibration`] closes the loop on the model side of the comparison. The left
panel bins the 2,842 half-inning snapshots by market-implied remaining runs and plots the mean
realized remaining runs in each bin: the points track the diagonal, so the market forecast is
approximately calibrated within this sample (the underlying leave-one-game-out remaining-runs
model reaches R² = 0.224, and adding fatigue terms changes its mean absolute error by −0.001
runs). The right panel shows the distribution of the book's forecast error: symmetric, centered
near zero (mean +0.49 runs), and — per Figure 4 — not predictable from any feature we measure.
Together with Figure 4, this defines the empirical boundary of public-information prediction
against a sharp live market.

## Summary of Results

Across every stage of the analysis, variables that predicted runs failed to provide incremental
predictive information once conditioned on the live market. The remaining sections interpret this
boundary, examine its methodological implications, and discuss what classes of questions remain
open.
