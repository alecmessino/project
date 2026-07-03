# Results (Pass 1 draft)

> **Drafting rule for this pass:** every paragraph points to exactly one figure or table, and
> opens from the evidence ("Figure X shows…"), not from intent ("We investigated…"). Numbers are
> the committed values in `output/*.json`. Language is bound to the experiment; findings are a
> **boundary**, never a "negative result." Figure files are content-named; the manuscript
> assigns numbers, shown here in brackets for reference.

**Research question (the spine).** *Do publicly observable baseball state variables contain
incremental predictive information about remaining runs beyond the forecast embedded in a sharp
live betting market?* The results below answer it in the negative, and locate the boundary at
which the answer turns.

---

Table 1 (`Appendix A`) records the full battery: ten candidate hypotheses drawn from the
public handicapping literature — times-through-order, velocity decline, bullpen-fatigue
multipliers, drop reversion on both sides, alternate-line skew, early-run anchoring,
weather/park context, a remaining-runs fatigue term, and finally forecast encompassing — each
with its motivation, the test applied, and the gate at which it was eliminated. Read as a whole,
the table establishes the study's central regularity before any single statistic: no hypothesis
reaches a positive verdict, and each is eliminated at a *different* stage, which rules out a
single shared artifact (a coding error, one bad month, one mis-specified model) as the common
cause.

Figure 2 [`hypothesis_elimination`] renders that battery as a five-gate elimination matrix —
initial signal, robustness, out-of-sample, market test, verdict. The diagonal texture of the
figure is the finding: several hypotheses clear an in-sample signal (green in column one), fewer
survive robustness, fewer still survive out-of-sample cross-validation, and none clears the
market test. Because the gate of elimination varies by row — times-through-order and the
velocity signal die at robustness, drop-reversion (Over) and forecast encompassing at
out-of-sample, the context hypotheses at the market test — the figure shows an *escalating
program* in which each surviving explanation is handed to a stricter test, not a set of
unrelated backtests that happened to fail.

Figure 3 [`incremental_information_funnel`] quantifies that attrition as a funnel: of ten
hypotheses tested, nine produce a detectable in-sample association with runs, three survive
out-of-sample validation, and zero add information beyond the market or clear a profitability
threshold. The collapse between "survives out-of-sample" (three) and "adds information beyond
the market" (zero) is the paper's pivot: predicting runs is common; predicting the *market's
error* is the wall. The funnel counts are derived directly from the Figure 2 matrix, so the two
figures cannot diverge.

Figure 4 [`forecast_encompassing`] is the statistical centerpiece and makes the wall precise.
Across 2,505 half-inning snapshots, a leave-one-game-out forecast of remaining runs from our full
feature set achieves an out-of-sample R² of 0.279; the market-implied remaining total alone
achieves 0.304; and combining the two moves R² by −0.017 — adding the features to the market does
not improve, and slightly degrades, the forecast. The left panel's annotation states the reading
directly: *no incremental information.* The right panel shows the per-feature version of the same
test (E+): each variable's individual incremental R² beyond the market, with every value inside a
±0.003 band (best case, bullpen, at +0.0018; velocity, tier, temperature, wind, and park all at
or below zero). The market statistically encompasses every public variable we measure, whether
tested jointly or one at a time. As the sharpest single test, we regress the book's forecast
error (realized minus implied remaining runs) on the features directly: it is not predictable
out-of-sample (R² = −0.037).

Figure 5 [`velocity_post_treatment_bias`] isolates why one hypothesis looked alive before it was
eliminated, and does so in a way that generalizes past baseball. A model that adds a starter's
velocity decline measured from the first to the third time through the order raises the
out-of-sample AUC for "team scores above 4.5" from a tier-only baseline of 0.420 to 0.610 — an
apparently large gain. But that velocity-drop variable is *post-treatment*: it is only defined for
starters who survived long enough to face the order a third time, precisely the starters already
being hit. Re-measuring velocity decline within a pre-treatment early window (first twenty pitches
versus the next twenty) collapses the AUC to 0.524, whose Hanley–McNeil confidence interval
straddles the 0.500 coin-flip line. The 0.61 "signal" was survivorship, not fatigue.

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
A well-calibrated forecast whose residual carries no recoverable public-information signal is the
empirical shape of the boundary this paper identifies.
