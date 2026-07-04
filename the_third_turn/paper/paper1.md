<div class="titleblock">
<h1>Forecast Encompassing as a Test of Predictive Signals: Evidence from Live MLB Totals Markets</h1>
<p class="epigraph">This paper asks whether publicly observable baseball information predicts outcomes, or merely predicts what the market already knows.</p>
<p class="author">Alec Messino<br/><span class="affil">The Third Turn Research Initiative &middot; alec.messino@gmail.com</span></p>
<p class="wp">Working paper &middot; Draft 0.9 &middot; July 2026 &middot; Comments welcome</p>
</div>

<!-- Draft 0.9 — editorial pass applied; §2 + references drafted with source-verified citations
(every reference checked against the publisher/arXiv/search record, July 2026); pending:
Benchmark packaging, external review. Figures embedded from `figures/` (content-named). Numbers
are committed values in `output/*.json`; the input caches (encompass_cache, program_a_cache,
remaining_snapshots) are now committed as frozen build inputs. Build PDF with
`python3 paper/build_pdf.py`. -->

## Abstract

Live, in-play wagering is a large and growing share of sports-betting volume, yet market-efficiency
research remains concentrated on pre-game prices; the calibration of live markets, and their
incorporation of in-game information, are comparatively unstudied. We ask a single question: do
publicly observable baseball state variables contain incremental predictive information about
remaining runs beyond the forecast embedded in a sharp live betting market? Using 163 Major League
Baseball games (June 2026) with one-minute live-total trajectories from a sharp book, pitch-level
measurement, and full play-by-play, we subject a battery of public hypotheses — times through the
order, velocity decline, bullpen fatigue, line-drop reversion, alternate-line skew, early-run
anchoring, and weather/park effects — to an escalating validation protocol ending in a
forecast-encompassing test against the market itself. No variable survives. The market's forecast
error is not predictable from any variable we measure (out-of-sample R² = −0.037; a Clark–West
nested forecast comparison does not favor the augmented model), and the design is powered to
exclude moderate incremental information. An apparent velocity signal is shown to be selection
bias, and an event-level transfer function indicates the line adjusts to information shocks by an
approximately uniform magnitude. At the one-minute, single-book resolution of our data we find no
evidence of exploitable public-information inefficiency, and we characterize this boundary
precisely. We release the Third Turn Protocol — an integration of standard forecast-evaluation
tools into a sequential validation ladder — and an accompanying benchmark dataset.

*Keywords:* market efficiency; in-play betting; forecast encompassing; calibration; incremental
information; reproducible benchmark.
*JEL codes:* C53 (forecasting), G14 (information and market efficiency), Z23 (sports economics).

---

## 1. Introduction

Live, in-play wagering has grown from a marginal product into a large and rising share of
sportsbook handle — industry reporting consistently places it at or near half of volume in mature
markets. Yet the empirical study of wagering-market efficiency, a literature surveyed by Sauer
(1998), has concentrated on pre-game moneylines and point spreads, where a single closing price
can be compared against a realized outcome. Live markets pose a different and less-studied problem:
prices update continuously as the game state evolves, so the object of interest is not a single
forecast but a stream of them, and the natural questions concern calibration and information
incorporation rather than a one-shot verdict. Whether live markets efficiently absorb the publicly
observable information generated during a game — and how one would even test such a claim — remains
comparatively open.

Baseball is an unusually favorable setting in which to ask the question. The game unfolds as a
sequence of discrete events with well-established run values (the RE24 base-out run-expectancy
table and linear weights), so the informational content of each event can be quantified rather than
estimated. Pitch-level measurement makes within-game state — velocity, pitch count, times through
the order — observable in fine detail. And the sport carries a strong body of public prior belief,
most prominently the times-through-order penalty (Tango, Lichtman, and Dolphin, 2007): the widely
held view that a starting pitcher degrades sharply the third time he faces a lineup, which, if
under-priced, would make the live Over a profitable bet. That belief is a natural entry point — a concrete, popular, plausible
hypothesis with which to probe the general question.

The general question, however, is not whether such variables predict scoring. Many of them do.
It is whether they carry *incremental* predictive information once the forecast already embedded in
a sharp live market is conditioned upon. This distinction — between predicting an outcome and adding
information beyond an existing forecast — is the conceptual center of the paper, and it is routinely
elided in applied betting research, where an in-sample association is often treated as evidence of
an edge. We take the opposite stance: an in-sample signal is the weakest possible evidence, and each
candidate variable must survive progressively stronger tests, culminating in a forecast-encompassing
test against the market itself. Within the limits of our data, no variable does. The result is not a
failure to find an edge but a characterization of the boundary at which publicly observable baseball
information ceases to add value beyond the market — a boundary we map precisely, and bind to the
conditions under which it was measured: 163 games across a single month, at one-minute cadence, from
a single sharp-book feed.

> ### Contributions
>
> This paper makes three contributions.
>
> **1. Empirical.** For a battery of publicly observable baseball variables — times through the
> order, velocity decline, bullpen fatigue, line-drop reversion, alternate-line skew, early-run
> anchoring, weather, and park — we show that none provides incremental predictive information about
> remaining runs once conditioned on the live market forecast, and we locate the point at which that
> incremental value disappears.
>
> **2. Methodological.** The individual tools are standard; our contribution is their *integration*
> into a single escalating protocol — the **Third Turn Protocol**: signal, robustness, out-of-sample,
> debiasing, conditional testing, forecast encompassing, transfer function — that shifts the burden
> of proof from demonstrating *prediction* to demonstrating *incremental information beyond an
> existing forecast*. It is domain-general and applies to any market with a sharp public forecast and
> observable state.
>
> **3. Infrastructure.** We release the cleaned datasets and feature schema as the **Third Turn
> Benchmark Dataset (v1)**, together with reference implementations of the market forecast,
> remaining-runs model, encompassing tests, and transfer function that operationalize the protocol,
> so that future hypotheses can be evaluated against the same reference rather than re-derived from
> scratch.

The remainder of the paper is organized around a single question, which every subsequent section
serves:

*Do publicly observable baseball state variables contain incremental predictive information about
remaining runs beyond the forecast embedded in a sharp live betting market?*

<div class="protocol-box">
<div class="pb-title">Box 1 · The Third Turn Protocol, in brief</div>
<pre>
              candidate variable
                     │
   1.  predicts the outcome?         ──no──▶  discard
                     │ yes
   2.  survives robustness?          ──no──▶  discard
                     │ yes
   3.  survives debiasing?           ──no──▶  selection artifact
                     │ yes
   4.  improves the market's
       own forecast?
                ╱         ╲
             yes           no
              │             │
        genuinely      already reflected
     new information     in the price
</pre>
</div>

Only a variable that clears the final gate carries information the price does not already hold.
Every hypothesis in this study reaches that gate and stops.

---

## 2. Related Work

This section is deliberately brief: its job is to establish a gap, not to survey three
literatures. We draw on each only for what the design requires.

**Wagering-market efficiency.** The economics of wagering markets is a mature literature, surveyed
by Sauer (1998), whose broad finding is that betting prices are accurate but not perfect:
systematic deviations such as the favorite–longshot bias exist, yet rarely survive transaction
costs. For baseball specifically, Woodland and Woodland (1994) document a *reverse*
favorite–longshot bias in the moneyline market and conclude that the deviations are insufficient
for profitable betting. This literature is overwhelmingly pre-game. The in-play evidence is
thinner and mixed. Croxson and Reade (2014) find that soccer exchange prices update swiftly and
essentially fully at goal arrival, consistent with semi-strong efficiency. More recent work
documents imperfections in the price *process* itself: Simon (2024) rejects weak-form efficiency
for MLB moneyline movement, finding systematic overreaction; Simon (2025) generalizes the negative
autocorrelation of price changes to NFL, NBA, and NHL markets; and Angelini and De Angelis (2026)
measure an approximately 0.64-for-one contemporaneous underreaction to benchmark-probability
changes in real-time prediction markets, with predictable subsequent drift.

**Baseball performance.** The times-through-order penalty entered the sabermetric canon through
Tango, Lichtman, and Dolphin (2007). The strongest recent evidence, however, favors continuous
decay over a discontinuity: Brill, Deshpande, and Wyner (2023) find little support for a
performance cliff at the third time through the order once batter and pitcher quality and other
confounders are controlled — a conclusion our own gradient analysis independently reproduces.
Velocity effects on batting outcomes are real but small per mile per hour: Sutton-Brown (2023)
estimates roughly 0.004 wOBA per mph operating through pitch quality, with a residual direct
effect an order of magnitude smaller. Run values for discrete events (the RE24 base-out
run-expectancy table and linear weights) are standard tools from the same tradition.

**Forecast evaluation.** Our tests are drawn from the econometric forecast-evaluation literature.
The pivotal one is the forecast-encompassing framework of Chong and Hendry (1986): a benchmark
forecast encompasses a rival when the rival adds no explanatory power for the target beyond the
benchmark. Because our nested models are compared out-of-sample, we use the tools developed for
that setting — the Diebold and Mariano (1995) comparison of predictive accuracy, West's (1996)
asymptotic theory of predictive inference, the Clark and West (2007) correction for nested-model
comparison, and, for the conditional case, Giacomini and White (2006). Calibration diagnostics —
reliability curves, the Brier score, expected calibration error — and the probabilistic
interpretation of the area under the ROC curve (Hanley and McNeil, 1982) complete the toolkit. None
of these instruments is new; our contribution is to assemble them into a single sequential protocol
and apply it with a sharp live betting line as the benchmark forecast.

**The gap.** These strands study either the price series in isolation, a single discrete shock, or
baseball performance without reference to prices. To our knowledge, no published work combines
live baseball state, pitch-level features, calibration analysis, an event-level transfer function,
and a forecast-encompassing test in which a sharp live betting line serves as the benchmark
forecast. That combination is this paper's contribution.

---

## 3. Methods

Our design compares two forecasts of the same quantity — the number of runs a game has left to
score at a given moment — and asks whether publicly observable state improves the forecast already
implied by the market. The unit of analysis throughout is the *half-inning snapshot*: a single
moment in a single game at which both the market's live total and the full game state are observed.
This section defines the data behind each snapshot (§3.1), how state variables are constructed from
it (§3.2), the escalating protocol by which a candidate variable is tested (§3.3), the statistical
estimators applied at each rung (§3.4, including why forecast encompassing is the central test),
and the artifacts released for reproduction (§3.5).

### 3.1 Data

The study draws on 163 Major League Baseball games played in June 2026, each observed from three
aligned sources. **Market prices.** Live full-game total (Over/Under) lines were recorded as
one-minute trajectories from a single Pinnacle-grade feed. From each trajectory we take the main
balanced total — the handicap at which the Over and Under prices are closest to even, i.e. the
market's median-outcome forecast of final total runs — as the incumbent forecast, and its implied
Over probability for the calibration diagnostics. Appendix B details how a snapshot's line is
matched to game state by timestamp.
**Game state.** Complete play-by-play and boxscore records from the MLB Stats API supply, at every
plate appearance, the inning and half, base-out state, score, batting-order position, the identity
and pitch count of the pitcher, and the times each batter has faced the current starter. **Pitch
measurement.** Pitch-level release speeds (`startSpeed`) from the same feed provide within-game
velocity trajectories. Venue and weather (temperature, wind speed and direction relative to the
field) and each game's realized final total complete the record. Sources are joined on game
identifier and, for odds, on timestamp. The one-minute cadence and single odds source are the
principal constraints on what the design can measure; their consequences are stated in §6.

### 3.2 Feature construction

From the raw record we construct, at each snapshot, the two forecasts under comparison and the
public state variables that might improve on them. The **market forecast of remaining runs** is
`B = (live total) − (runs already scored)`; the **realized remaining runs** is
`Y = (final total) − (runs already scored)`. `Y − B` is therefore the market's forecast error at
that snapshot — the object whose predictability is the crux of the study.

The candidate state variables are built without reference to the outcome. The starter is the
pitcher at the first plate appearance of each half; batting-order slots are assigned by order of
first appearance against that starter, and times-through-order counts prior faced batters divided
by nine. Velocity decline is computed two ways — across successive times through the order, and
within a fixed early pitch-count window (first twenty pitches versus the next twenty) — a
distinction that becomes decisive in §3.3. Bullpen quality is each team's season relief runs
allowed per nine innings; park factor and signed wind/temperature come from static published
tables. The true change in run expectancy at each event, used by the transfer function, is
`ΔRE = (runs scored) + (RE24_after − RE24_before)`, where RE24 is the standard 24-state base-out
run-expectancy table (Tango, Lichtman, and Dolphin, 2007). No feature uses information unavailable
at the snapshot it describes.

### 3.3 Validation protocol

The core of the design is a fixed sequence of tests of *increasing stringency*, applied in the same
order to every candidate variable. A variable is carried forward only until it is eliminated, and
we report the rung at which elimination occurs; a variable that reaches the top has been tested
against progressively harder alternatives rather than a single easy one. The ladder is:

> Signal → Robustness → Out-of-sample → Debiasing → Conditional testing →
> Forecast encompassing → Transfer function

**Signal** asks whether the variable is associated with scoring at all, in-sample. **Robustness**
asks whether that association survives reasonable changes in specification, thresholds, and
sub-sample — an in-sample edge that moves with an arbitrary cutoff is rejected here. **Out-of-sample**
re-estimates every model by leave-one-game-out cross-validation, so a variable is judged only on
games not used to fit it. **Debiasing** replaces any post-treatment measurement — one defined only
on a subsample selected by the outcome — with a pre-treatment analogue; a signal that survives
in-sample but vanishes once measured before treatment is diagnosed as selection, not effect.
**Conditional testing** asks whether the variable earns its keep only within specific contexts
(e.g. hitter-friendly parks or weather) rather than on average. **Forecast encompassing** conditions
on the market forecast itself and asks whether the variable adds anything to it. **Transfer function**
finally asks not whether the market prices the variable but whether it prices it by the correct
magnitude. The protocol embodies a single guiding principle — *a betting hypothesis should be
evaluated against the market, not merely against the outcome* — and the last two rungs are what
enforce it. Figure 1 traces the study's actual course through this sequence.

![](figures/research_process.png)

**Figure 1.** The research process. Each surviving explanation was handed to a stricter test; the
sequence terminates at a boundary, not at an edge.

### 3.4 Statistical evaluation

Each rung is a specific estimator, all computed out-of-sample by leave-one-game-out.

**Forecast encompassing** (Chong and Hendry, 1986)**.** For remaining runs `Y`, market forecast
`B`, and a candidate feature set `X`, we fit three ridge-regularized linear forecasts — `Y ~ B`,
`Y ~ X`, and `Y ~ B + X` — and compare their out-of-sample R² and mean absolute error. If `Y ~ B + X` does not improve on `Y ~ B`,
the market encompasses `X`. The sharpest form regresses the market's forecast error `Y − B`
directly on `X`: if `X` cannot predict the error out-of-sample, it carries no information the price
lacks. A per-feature variant (E+) fits `Y ~ B + Xᵢ` against `Y ~ B` for each variable individually,
so that two proxies for the same state cannot mask one another in the joint model. Continuous
predictors are standardized; the ridge penalty is fixed a priori and applied to all non-intercept
terms, and Appendix B confirms that the encompassing conclusion is invariant from ordinary least
squares (penalty zero) through heavy shrinkage. Because the restricted (`Y ~ B`) and unrestricted
(`Y ~ B + X`) models are nested, a naïve out-of-sample MSPE comparison is biased against the larger
model; we therefore report the Clark and West (2007) adjusted statistic, which corrects for the
noise the extra parameters introduce, clustered by game, alongside a 95% confidence interval for the
encompassing gain obtained by block-bootstrapping whole games.

*Why forecast encompassing?* Ordinary predictive accuracy cannot separate the two claims this paper
must distinguish. A model that predicts runs well demonstrates only that a variable is informative
about the outcome; it says nothing about whether that information is already contained in an
existing forecast. Forecast encompassing answers the second question directly by conditioning on
the market forecast before evaluating the variable, so that the quantity being tested is
*incremental* information rather than raw predictive power. Because a variable can predict the
outcome while adding nothing beyond the market — the empirical situation we in fact observe — this
conditioning is not a refinement of the analysis but its center.

**Calibration.** We assess the market forecast by binning snapshots on `B` and comparing mean
realized `Y` per bin against the identity line, and we assess probabilistic forecasts (e.g. the
probability a team exceeds a run threshold) with reliability curves, the Brier score, expected
calibration error, and area under the ROC curve. The velocity debiasing of §3.3 is evaluated here
as the change in out-of-sample AUC between a baseline forecast and forecasts augmented with the
post-treatment versus pre-treatment velocity measures; AUC confidence intervals use the analytic
variance of Hanley and McNeil (1982).

**Transfer function.** For each in-game event we pair the true change in run expectancy `ΔRE` with
the converged change in the live total one and five minutes later (`ΔBook`), and estimate the
response ratio `ΔBook / ΔRE` by event type together with a single common slope through the origin.
Mean `ΔRE` by event type is checked against published linear weights as a validity control.

**Statistical power.** Because the paper's claims are null, we report what effect sizes the design
could have detected. For the incremental-information test (an *F*-test for the ten features beyond
the market), 80% power at the 5% level corresponds to a minimum detectable incremental R² of about
0.007 treating the 2,505 snapshots as independent, rising to about 0.10 under the conservative
assumption that only the 163 games are independent; the true effective sample lies between. Every
observed per-feature incremental R² (≤ 0.0018) sits below even the optimistic floor, so the design
is powered to exclude moderate incremental information but not arbitrarily small amounts. In
betting terms, detecting a 55% win rate against the 52.4% break-even at 80% power would require on
the order of 2,000 wagers; our few hundred qualifying situations can rule out large edges, not tiny
ones. Appendix B gives the full calculation.

**Uncertainty.** All point forecasts are out-of-sample (leave-one-game-out); interval estimates use
the Hanley–McNeil formula for AUC, Wilson intervals for proportions, and the bootstrap otherwise.
Differences smaller than the width of their intervals are reported as such and are not interpreted
as effects.

### 3.5 Reproducibility

Every quantity in this paper is recomputed from committed inputs by a fixed set of scripts;
estimation is deterministic (leave-one-game-out folds and fixed seeds), so results regenerate
exactly. To facilitate reproduction we release the cleaned datasets and feature schema as the
**Third Turn Benchmark Dataset (v1)**, together with reference implementations of the market
forecast, the remaining-runs model, the encompassing tests, and the transfer function — an
executable form of the Third Turn Protocol (§3.3) — archived under a persistent DOI alongside the
code repository and the research log. The frozen result artifacts (`output/*.json`) and the scripts that produce them are
sufficient to reconstruct every figure and number without access to the original feeds.

---

## 4. Results

The research question is answered directly by Figure 4; the remaining figures explain why the
answer takes the form it does.

Figure 4 demonstrates that publicly observable baseball variables provide no measurable incremental
predictive information beyond the live market. Across 2,505 half-inning snapshots, a
leave-one-game-out forecast of remaining runs from our full feature set achieves an out-of-sample
R² of 0.279; the market-implied remaining total alone achieves 0.304; and combining the two changes
R² by −0.017 — adding the features to the market does not improve, and slightly degrades, the
forecast. The right panel shows the per-feature version of the same test (E+): each variable's
individual incremental R² beyond the market is at most +0.0018 (best case, bullpen); the rest are
at or below zero, several materially so (park, temperature, and wind near −0.006), so no single
variable hides behind the others. As the sharpest test, we regress the book's forecast error —
realized minus market-implied remaining runs — directly on the features: it is not predictable
out-of-sample, R² = −0.037. This is the central empirical result of the study. The difference is
small and its uncertainty is bounded: the encompassing gain of −0.017 has a 95% block-bootstrap
confidence interval (resampling whole games) of [−0.036, +0.002], and a Clark–West test for nested
forecast comparison (2007) does not reject equal predictive accuracy in the market's favor
(statistic −0.1, one-sided *p* = 0.55) — the market is, if anything, the better forecast. Forecast
encompassing is the highest evidentiary standard we apply, because it conditions on the market's
own forecast rather than on realized outcomes alone: a variable clears it only by improving a
forecast that already reflects the market's information.

![](figures/forecast_encompassing.png)

**Figure 4.** Forecast encompassing. *Left:* adding the feature set to the market forecast changes
out-of-sample R² by −0.017. *Right:* each feature's individual incremental R² beyond the market;
bars within the ±0.003 band are drawn neutral.

Figure 2 shows that this boundary is not a property of one variable but of the entire battery. The
figure arranges ten candidate hypotheses drawn from the public handicapping literature —
times-through-order, velocity decline, bullpen-fatigue multipliers, drop reversion on both sides,
alternate-line skew, early-run anchoring, weather/park context, a remaining-runs fatigue term, and
forecast encompassing — against five escalating gates: initial signal, robustness, out-of-sample,
market test, verdict. The pattern of elimination is the finding: several hypotheses clear an
in-sample signal, fewer survive robustness, fewer survive out-of-sample cross-validation, and none
clears the market test. Because the gate of elimination varies by row — times-through-order and the
velocity signal die at robustness, drop-reversion (Over) and forecast encompassing at out-of-sample,
the context hypotheses at the market test — no single artifact (a coding error, one anomalous month,
one mis-specified model) is a plausible common cause. The complete battery, with each hypothesis's
motivation and mode of elimination, is summarized in Appendix Table A1.

![](figures/hypothesis_elimination.png)

**Figure 2.** Sequential elimination of candidate public-information hypotheses across five
escalating gates. Green = cleared this gate; red = failed here; grey = not reached.

Figure 3 quantifies the attrition as a funnel: of ten hypotheses tested, nine produce a detectable
in-sample association with runs, three survive out-of-sample validation, and zero add information
beyond the market or clear a profitability threshold. The collapse between "survives out-of-sample"
(three) and "adds information beyond the market" (zero) is the paper's pivot: predicting runs is
common; predicting the market's error is the empirical boundary. The funnel counts are derived
directly from the Figure 2 matrix, so the two figures cannot diverge.

![](figures/incremental_information_funnel.png)

**Figure 3.** The incremental-information funnel. Counts derive from the Figure 2 matrix.

Figure 5 explains why one hypothesis appeared to survive before it was eliminated, and in doing so
illustrates a general statistical principle. A model that adds a starter's velocity decline
measured from the first to the third time through the order raises the out-of-sample AUC for "team
scores above 4.5" from a tier-only baseline of 0.420 to 0.610 — an apparently large gain. But that
velocity-drop variable is *post-treatment*: it is defined only for starters who survived long enough
to face the order a third time, precisely the starters already being hit. Re-measuring velocity
decline within a pre-treatment early window (first twenty pitches versus the next twenty) collapses
the AUC to 0.524, whose Hanley–McNeil confidence interval straddles the 0.500 coin-flip line. The
apparent 0.61 signal was survivorship, not fatigue — a conditioning artifact that the escalating
protocol is designed to catch.

![](figures/velocity_post_treatment_bias.png)

**Figure 5.** Post-treatment bias in the velocity signal. Out-of-sample AUC with Hanley–McNeil 95%
intervals; the debiased estimate straddles the coin-flip line.

Figure 6 turns from whether the market prices information to whether it prices it by the right
*amount*. For each of 6,414 in-game events we compute the true change in run expectancy (ΔRE, from a
base-out RE24 table plus runs scored) and the converged move in the live total five minutes later
(ΔBook). Plotted against each other, every positive-run event type lies on a single common slope of
approximately 0.74 through the origin; the response ratios for the higher-frequency events cluster
in a narrow 0.63–0.84 band (walk 0.63, double 0.64, single 0.72, home run 0.81, triple 0.84) with
no ordering by event magnitude. That uniformity is evidence about the *measurement pipeline* — a
single Pinnacle-grade source sampled at roughly one-minute cadence acts as a low-pass filter that
attenuates every shock by the same factor — rather than a per-event mispricing an edge could
exploit. (Hit-by-pitch, n = 115, sits below the band; pitching changes move the line near zero, but
RE24 cannot benchmark reliever quality, so we exclude them from the elasticity claim.)

![](figures/transfer_function.png)

**Figure 6.** The market transfer function. Every positive-run event type lies on one common slope
≈ 0.74; marker area is proportional to event count.

Figure 7 closes the loop on the model side of the comparison. The left panel bins the 2,505
half-inning snapshots by market-implied remaining runs and plots the mean realized remaining runs in
each bin: the points track the diagonal, so the market forecast is approximately calibrated within
this sample (the underlying leave-one-game-out remaining-runs model, fit on 2,859 snapshots,
reaches R² = 0.226, and adding fatigue terms leaves its mean absolute error essentially unchanged —
≈ 0.001 runs, if anything slightly worse). The
right panel shows the distribution of the book's forecast error. Its *median is zero*, but its
*mean is +0.49 runs* — the signature of a right-skewed remaining-runs distribution (skewness +1.23),
in which a balanced betting line tracks the median outcome while realized runs and a least-squares
forecast track the higher mean. This mean–median gap is a level term — its dependence on the market
forecast is negligible (a slope of +0.01 on `B`) — that any regression with an intercept absorbs; it
is therefore orthogonal to the incremental-information tests rather than a market bias, and Appendix
B documents it. Beyond that intercept the error is not predictable from any feature we measure.
Together with Figure 4, this defines the empirical boundary of public-information prediction against
a sharp live market, at the one-minute, single-book resolution of our data.

![](figures/market_calibration.png)

**Figure 7.** Market calibration. *Left:* binned market-implied versus realized remaining runs.
*Right:* the distribution of the market's forecast error.

### Summary of results

Across every stage of the analysis, variables that predicted runs failed to provide incremental
predictive information once conditioned on the live market. The remaining sections interpret this
boundary, examine its methodological implications, and discuss what classes of questions remain
open.

---

## 5. Discussion

The question this study set out to answer was whether publicly observable baseball state variables
contain incremental predictive information about remaining runs beyond the forecast embedded in a
sharp live betting market. The Results answer it: within the limits of our data, they do not. What
follows interprets that boundary — what it means, why it arises, why it matters beyond baseball,
and where the evidence genuinely runs out.

### 5.1 What the boundary actually means

The central question of this study was not whether baseball variables predict runs. They do. Pitch
count, inning, pitcher quality, weather, park effects, and velocity all contain information about
future scoring, and our own feature-only forecast (out-of-sample R² = 0.279) confirms it. The
question was narrower and economically more meaningful: *after* conditioning on the forecast
already embedded in a sharp live betting market, do those publicly observable variables provide
*additional* predictive information? Within the limits of our data, the answer is no.

That distinction — introduced in Section 1 as the paper's conceptual center — disarms the most
natural objection in advance. A reader may protest that weather obviously matters, or that a tiring
pitcher obviously concedes more runs. Both are true. The point of forecast encompassing is not to
deny that these variables carry signal; it is to ask whether their signal is *already priced*. When
the market's forecast error — the difference between what actually happened and what the line
implied — cannot be predicted from any of these variables out-of-sample (R² = −0.037), the most
parsimonious reading is that the information is already incorporated into the market forecast. The
variables are informative about runs and redundant with the price. Prediction survives; increment
does not.

Why does this happen? Not because baseball theory is wrong, but because the forecast embedded in a
sharp live market already reflects these variables — it is produced by participants with strong
incentives to price observable state quickly. The transfer-function evidence is consistent with
this: the line moves proportionately to the true change in run expectancy after every event type,
with no class systematically mispriced. A forecast that adjusts proportionately to information
shocks is precisely the kind whose residual carries no recoverable public-information signal —
which is what we observe.

### 5.2 Prediction is not profit

Here the paper stops being about baseball. **Prediction and profit are distinct statistical
problems**, and conflating them is among the most common errors in applied betting research.

Much of that literature implicitly assumes a single arrow: better prediction leads to better
betting. Our results break that arrow into three distinct links that must each hold independently.
A variable may *predict an outcome* — velocity decline is associated with more runs. It may
nonetheless carry *no incremental information* once the market forecast is conditioned upon —
because the price already reflects it. And even a variable that did carry incremental information
would not automatically be *profitable*, because profitability additionally requires that the edge
exceed transaction costs, survive the vig, and persist after the act of betting moves the line.
Prediction, increment, and profit are three questions, not one.

Forecast encompassing isolates the middle link — the one betting papers most often skip. A naïve
backtest speaks to prediction; a profit-and-loss simulation speaks to the third link and is easily
flattered by overfitting and stale lines. Encompassing asks the middle question directly — *does
this variable improve on what the price already reflects?* — and because it speaks to increment
rather than to a staking scheme, our negative answer does not depend on how one would have bet.

### 5.3 The efficient frontier of public information

We give this boundary a name. We use the term **efficient frontier of public information** to
describe the point at which additional publicly observable variables cease to improve prediction
after conditioning on the market forecast. Inside the frontier lie the observable baseball
variables — pitch count, tier, bullpen, park, weather, velocity, times-through-order — that the
market encompasses. Outside it lie the dimensions our data cannot reach: the timing of price
formation, disagreement across books, and the evolution of the full implied distribution rather
than its mean.

One caution bounds the claim. What we observe is limited by the *resolution of our instrument* — a
single sharp book sampled once a minute — not necessarily by the resolution of the *market*. A
lag that resolves within that minute, or a disagreement visible only across books, would be
invisible to us and would register, incorrectly, as efficiency. Our result is therefore that public
baseball variables carry no incremental information *at the one-minute, single-book resolution of
our data*; finer-grained or cross-book measurement could revise the boundary, and mapping it is the
subject of the microstructure work in Section 7.

Every hypothesis in this study was, in effect, an attempt to move beyond that frontier using
public state variables. None succeeded. That uniformity is not a series of independent
disappointments; it is a single, coherent mapping of where the frontier sits for one sport, one
month, and one class of information. The contribution is conceptual as much as empirical: the
frontier reframes "we failed to find an edge" as "we located the line beyond which public
information stops helping," and it tells the next researcher where *not* to dig.

### 5.4 The methodological contribution

Although motivated by baseball, the methodology is not baseball-specific. Its individual
components — cross-validation, selection-bias correction, forecast encompassing, nested
forecast-comparison tests — are standard; the contribution is their *integration* into a single
escalating protocol that distinguishes variables which predict outcomes from variables that contain
incremental information beyond an existing forecast. Each rung strips away one more class of
illusion — overfitting, then selection, then confounding, then redundancy-with-the-market — so that
a hypothesis surviving to the top has been tested against progressively harder alternatives rather
than a single easy one.

The reason a protocol like this matters is a matter of where the burden of proof sits. Sports
betting research frequently terminates after the discovery of an in-sample signal. The present
study instead treated each positive result as a hypothesis requiring progressively stronger
attempts at falsification. The protocol therefore shifts the burden of proof from demonstrating
*prediction* to demonstrating *incremental information beyond an existing market forecast* — a
higher and more economically meaningful standard, and one that a single backtest can never meet.
That shift is a philosophy of evidence, not merely a workflow.

> Signal → Robustness → Out-of-sample → Debiasing → Conditional testing →
> Forecast encompassing → Transfer function

The ladder transfers unchanged to any market with a sharp public forecast and observable state:
NBA totals, NFL spreads, soccer in-play, tennis, racing. A researcher there can adopt the same
sequence, report at which rung each candidate variable is eliminated, and compare results across
domains. We name it the **Third Turn Protocol** and release its reference implementation with the
accompanying data as the **Third Turn Benchmark Dataset (v1)**. A citable protocol and a shared
dataset may prove more durable than any single finding, because they let a field accumulate
falsifications instead of scattered one-off backtests.

---

## 6. Limitations

We state the conditions under which our conclusion holds, without interpretation. **Scope.** The
study covers 163 games over a single month (June 2026) of one sport; the boundary is characterized
precisely, but only under those conditions, and we make no claim of seasonal or cross-sport
generality. A second month of live data is being collected and will be added before journal
submission to test temporal stability. **Odds source.** Historical line trajectories derive from a single Pinnacle-grade
feed sampled at roughly one-minute intervals; we therefore cannot separate genuine price-formation
latency from feed cadence, and the uniform sub-one response ratio in the transfer function is
consistent with either. **Single-book benchmark.** All encompassing tests are conducted against
one sharp book; we cannot test cross-book agreement or leadership. **Market coverage.** Retail live
team totals were not exposed by our feeds and are untested, as are first-five-inning totals.
**Ground truth.** The remaining-runs model and RE24 transfer benchmark use published static run
values, not park- or season-specific re-estimation; the pitching-change response is reported but
excluded from the elasticity claim because RE24 cannot price reliever quality. **Estimation.**
Out-of-sample figures are leave-one-game-out; effective sample sizes for the rarer event types
(e.g. triples, n = 47) are small, and the corresponding response ratios should be read with that
in mind. None of these conditions is load-bearing for the central result — the book's forecast
error is unpredictable from every feature we measure — but each bounds how far it may be
generalized.

---

## 7. Remaining Questions

Distinct from the limitations above, this section lists what the evidence *genuinely does not
answer* — the questions that remain open not because our experiment was narrow, but because they
require data of a kind the historical record cannot provide. Does information propagate across
books with a measurable lag, and is a laggard ever tradable? Does the market update the *shape* of
the implied run distribution — its variance, skew, and tail — as accurately as it updates the
mean, or is higher-moment miscalibration the place a residual edge could still hide? What is the
information half-life of a given shock: how long does the line take to absorb a home run versus a
pitching change versus an injury? Does the boundary we map for full-game totals move when the
market isolates the starters, as first-five-inning totals do? Each of these is a live-data
question — none is answerable from one-minute historical snapshots of a single book — and each is
the natural subject of the market-microstructure study that our forward-collected, timestamped
streams are being built to support.

---

## 8. Conclusion — what we learned

This project began with a search for an exploitable feature of baseball. It ended by identifying
the empirical boundary at which publicly observable baseball information ceases to provide
incremental predictive value against a sharp live market. That boundary is itself a result. It
redirects future work away from discovering additional baseball variables and toward understanding
how information propagates through live betting markets. The contribution of this study is
therefore not a successful betting strategy, but a reproducible framework for determining when one
does — and does not — exist. The principal contribution is thus methodological: a reproducible
procedure for distinguishing variables that predict outcomes from variables that carry information
not already reflected in an existing forecast.

---

## Appendix Table A1 — the full hypothesis battery

Referenced once from §4; Figure 2 is the main-text representation.

| Hypothesis | Motivation | Test | Outcome | Mode of elimination |
|---|---|---|---|---|
| Times-through-order | Familiarity/fatigue penalty on 3rd time through | Binary gate → gradient, LOGO | Encompassed | Decay is continuous, not a discontinuity; out-of-sample fires below breakeven; market prices it |
| Velocity decline | Fatigue shows as lost velocity | Debiased early-window vs post-treatment | Artifact | Defined only for starters who remained in long enough to be measured (selection); clean signal AUC ≈ 0.52 |
| Bullpen fatigue | Fatigued bullpen → higher scoring after a starter collapse | Isolated to the bullpen's own innings | No effect | Fatigued bullpens concede the same or fewer runs; no multiplier |
| Drop reversion (Over) | Over-dropped line reverts up | Threshold sweep, all games | Not out-of-sample | Reversion is right-skewed (win-big/lose-small); median below the line |
| Drop reversion (Under) | Line stays low after a slow start | Banded + robustness gates | Not robust | Effective band moves with the snapshot inning; concentrated in the recent sample |
| Alternate-line skew | Buy the fat upper tail at longer odds | Empirical win% vs efficient-implied | Priced | Empirical < implied at every half-run increment above the main line; tail priced fatter than realized |
| Early-run anchoring | Live total under-reacts to a 1st-inning scoring burst | Post-1st Over, cause split | Priced | 49/50 bursts hit-driven (no fluky-runs population); market prices the change |
| Weather / park | Books under-price hitter-friendly context | Conditional split | Priced | Hitter-friendly Overs hit *less* (46% < 50%): market over-adjusts for context |
| Remaining-runs fatigue | Fatigue adds to a state model | Incremental MAE, LOGO | No increment | Game state already contains the information; ΔMAE ≈ 0 (no improvement) |
| **Forecast encompassing** | Does *anything* beat the market? | `Y~B+X`; `(Y−B)~X`; per-feature E+ | **Encompassed** | Book error not predictable from any feature out-of-sample (R² ≈ 0) |

---

## Appendix B — construction, power, and the forecast-error bias

**Snapshot construction.** The unit of analysis is the first plate appearance of each half-inning
through the eighth, for which a live line is available. Game state (inning, half, base-out, score,
batting slot, pitcher, pitch count, times-through-order) is read from the play-by-play at that plate
appearance; the market line is matched to it by timestamp, using the most recent quote at or before
the plate-appearance start time. The incumbent forecast is `B = (main total) − (runs already
scored)` and the target is `Y = (final total) − (runs already scored)`.

**Sample sizes.** The three analyses use overlapping but distinct samples, by construction. The
encompassing and calibration analysis uses 2,505 half-inning snapshots (innings 1–8 with a matched
line). The remaining-runs baseline uses 2,859 half-inning states (it does not require a market line,
so a few additional states qualify). The transfer function uses 6,414 *events* rather than
snapshots — every run-scoring play and pitching change with a converged before/after line — a
different unit entirely.

**The forecast-error bias.** The book error `E = Y − B` has mean +0.489 but median 0.000, on
snapshots whose remaining-runs distribution has skewness +1.23. This is the mean–median gap of a
right-skewed count distribution: a balanced betting line sits at the median outcome, while realized
runs and any least-squares forecast track the higher mean. Regressing `E` on `B` gives a slope of
+0.014 — the gap is essentially a constant level term, not a function of the forecast — so any model
with an intercept absorbs it, and it does not enter the incremental-information comparisons. It is a
property of the forecast's target functional, not evidence of market bias.

**Nested forecast comparison.** Comparing the nested out-of-sample forecasts `Y ~ B` and
`Y ~ B + X` by raw MSPE is biased toward the smaller model; the Clark–West (2007) adjustment
corrects this. The market model has the lower MSPE (13.79 vs 14.14); the Clark–West statistic,
clustered by game, is −0.1 (one-sided *p* = 0.55), so we do not reject equal predictive accuracy in
the market's favor. Block-bootstrapping whole games, the encompassing gain R²(`B+X`) − R²(`B`) is
−0.017 with a 95% interval of [−0.036, +0.002].

**Power.** For the ten-feature *F*-test of incremental information, 80% power at the 5% level
requires an incremental R² of about 0.007 if the 2,505 snapshots are treated as independent and
about 0.10 if only the 163 games are; every observed per-feature incremental R² (≤ 0.0018) is below
even the former. A win-rate edge of 55% versus the 52.4% break-even would need ≈ 2,000 wagers to
detect at 80% power. The design excludes moderate incremental information, not tiny amounts.

**Penalty sensitivity.** The encompassing conclusion is invariant to the ridge penalty. From
ordinary least squares (penalty 0) through heavy shrinkage (penalty 100), the encompassing gain
stays in [−0.017, −0.013] and the book-error out-of-sample R² in [−0.037, −0.034]; features never
improve on the market.

| ridge penalty | R²(`Y~B`) | R²(`Y~X`) | R²(`Y~B+X`) | gain | (`Y−B`)~X R² |
|---|---|---|---|---|---|
| 0 (OLS) | 0.304 | 0.279 | 0.286 | −0.017 | −0.037 |
| 1 | 0.304 | 0.279 | 0.286 | −0.017 | −0.037 |
| 10 | 0.304 | 0.279 | 0.287 | −0.017 | −0.037 |
| 100 | 0.303 | 0.281 | 0.290 | −0.013 | −0.034 |

*All Appendix B numbers are produced by `revision1.py` from the committed caches.*

---

## Data and code availability

The cleaned datasets, feature schema, and frozen result artifacts are released as the **Third Turn
Benchmark Dataset (v1)** (`benchmark/`); the **Third Turn Protocol** is specified canonically in
`protocol/` — the validation ladder (`protocol.md`), a safeguard registry with per-safeguard
provenance (`safeguards.md`), and objective stopping rules (`stopping_rules.md`) — with reference
implementations that reproduce every reported number from the committed inputs. Both are archived
alongside the code repository and the research decisions log. *(Persistent DOI and packaged archive
pending publication.)*

## References

Angelini, G., and L. De Angelis (2026). "When Do Markets Fully Process Public Information?
Evidence from Real-Time Prediction Markets." arXiv:2606.07811.

Brill, R. S., S. K. Deshpande, and A. J. Wyner (2023). "A Bayesian Analysis of the Time Through
the Order Penalty in Baseball." *Journal of Quantitative Analysis in Sports* 19(4): 245–262.

Chong, Y. Y., and D. F. Hendry (1986). "Econometric Evaluation of Linear Macro-Economic Models."
*Review of Economic Studies* 53(4): 671–690.

Clark, T. E., and K. D. West (2007). "Approximately Normal Tests for Equal Predictive Accuracy in
Nested Models." *Journal of Econometrics* 138(1): 291–311.

Diebold, F. X., and R. S. Mariano (1995). "Comparing Predictive Accuracy." *Journal of Business &
Economic Statistics* 13(3): 253–263.

Giacomini, R., and H. White (2006). "Tests of Conditional Predictive Ability." *Econometrica* 74(6):
1545–1578.

Croxson, K., and J. J. Reade (2014). "Information and Efficiency: Goal Arrival in Soccer Betting."
*The Economic Journal* 124(575): 62–91.

Hanley, J. A., and B. J. McNeil (1982). "The Meaning and Use of the Area Under a Receiver
Operating Characteristic (ROC) Curve." *Radiology* 143(1): 29–36.

Sauer, R. D. (1998). "The Economics of Wagering Markets." *Journal of Economic Literature* 36(4):
2021–2064.

Simon, J. (2024). "Inefficient Forecasts at the Sportsbook: An Analysis of Real-Time Betting Line
Movement." *Management Science*. doi:10.1287/mnsc.2022.00456.

Simon, J. (2025). "Autocorrelation and Weekend Effects: Inefficiencies in Moneyline Movement for
Three Major Sports." *International Journal of Sport Finance* 20: 211–231.

Sutton-Brown, S. (2023). "The Value of Relative Velocity." *Baseball Prospectus*, December 14,
2023.

Tango, T., M. Lichtman, and A. Dolphin (2007). *The Book: Playing the Percentages in Baseball.*
Potomac Books.

West, K. D. (1996). "Asymptotic Inference About Predictive Ability." *Econometrica* 64(5):
1067–1084.

Woodland, L. M., and B. M. Woodland (1994). "Market Efficiency and the Favorite–Longshot Bias:
The Baseball Betting Market." *Journal of Finance* 49(1): 269–279.
