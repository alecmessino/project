# Introduction (Pass 4 draft)

> **Drafting stance:** open broad (live betting, not baseball); baseball enters in paragraph two.
> Forecasting terminology over baseball terminology. Contributions in a distinct boxed section.
> Close on the one research-question sentence — the spine that also opens the Abstract and the
> Discussion. Claims bound to the data; the finding is a boundary, not a "negative result."

Live, in-play wagering has grown from a marginal product into a large and rising share of
sportsbook handle, in some markets exceeding pre-game betting. Yet the empirical study of market
efficiency has concentrated on pre-game moneylines and point spreads, where a single closing price
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
most prominently the times-through-order penalty (TTOP): the widely held view that a starting
pitcher degrades sharply the third time he faces a lineup, which, if under-priced, would make the
live Over a profitable bet. That belief is a natural entry point — a concrete, popular, plausible
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

> ## Contributions
>
> This paper makes three contributions.
>
> **1. Empirical.** For a battery of publicly observable baseball variables — times through the
> order, velocity decline, bullpen fatigue, line-drop reversion, alternate-line skew, early-run
> anchoring, weather, and park — we show that none provides incremental predictive information about
> remaining runs once conditioned on the live market forecast, and we locate the point at which that
> incremental value disappears.
>
> **2. Methodological.** We formalize an escalating validation protocol — signal, robustness,
> out-of-sample, debiasing, conditional testing, forecast encompassing, transfer function — that
> shifts the burden of proof from demonstrating *prediction* to demonstrating *incremental
> information beyond an existing forecast*. The protocol is domain-general and applies to any market
> with a sharp public forecast and observable state.
>
> **3. Infrastructure.** We release the cleaned datasets, the feature schema, the evaluation
> protocol, and reference implementations of the market forecast, remaining-runs model, encompassing
> tests, and transfer function as the initial release of the **Third Turn Benchmark**, so that future
> hypotheses can be evaluated against the same reference rather than re-derived from scratch.

The remainder of the paper is organized around a single question, which every subsequent section
serves:

*Do publicly observable baseball state variables contain incremental predictive information about
remaining runs beyond the forecast embedded in a sharp live betting market?*
