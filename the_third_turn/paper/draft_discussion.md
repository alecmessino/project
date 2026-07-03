# Discussion (Pass 2 draft)

> **Drafting stance for this pass:** the Discussion is an essay, not a longer Results. It answers
> the four questions the Results deliberately avoid — *what does this mean, why did it happen, why
> should anyone outside baseball care, and what remains genuinely open* — and it protects one
> thread above all: the durable contribution is the framework, not a betting edge. Claims stay
> bound to the data ("within the limits of our data"); the finding is an **empirical boundary**,
> never a "negative result."

The question this study set out to answer was whether publicly observable baseball state variables
contain incremental predictive information about remaining runs beyond the forecast embedded in a
sharp live betting market. The Results answer it: within the limits of our data, they do not. What
follows interprets that boundary — what it means, why it arises, why it matters beyond baseball,
and where the evidence genuinely runs out.

## 7.1 What the boundary actually means

The central question of this study was not whether baseball variables predict runs. They do. Pitch
count, inning, pitcher quality, weather, park effects, and velocity all contain information about
future scoring, and our own feature-only forecast (out-of-sample R² = 0.279) confirms it. The
question was narrower and economically more meaningful: *after* conditioning on the forecast
already embedded in a sharp live betting market, do those publicly observable variables provide
*additional* predictive information? Within the limits of our data, the answer is no.

That distinction is the whole paper, and it disarms the most natural objection in advance. A
reader may protest that weather obviously matters, or that a tiring pitcher obviously concedes more
runs. Both are true. The point of forecast encompassing is not to deny that these variables carry
signal; it is to ask whether their signal is *already priced*. When the market's forecast error —
the difference between what actually happened and what the line implied — cannot be predicted from
any of these variables out-of-sample (R² = −0.037), the most parsimonious reading is that the
market has already incorporated them. The variables are informative about runs and redundant with
the price. Prediction survives; increment does not.

Why does this happen? Not because baseball theory is wrong, but because the counterparties setting
these lines are themselves sophisticated processors of exactly this public information. A sharp
live market is a forecast produced by participants with strong incentives to price observable
state correctly and quickly. The transfer-function evidence sharpens this: the line moves in the
right direction and by a stable fraction of the true change in run expectancy after every event
type, with no event class systematically under- or over-priced. A market that responds
proportionately to information shocks is precisely the kind of market whose residual should carry
no recoverable public-information signal — which is what we observe.

## 7.2 Prediction is not profit

Here the paper stops being about baseball. **Prediction and profit are distinct statistical
problems**, and conflating them is the most common error in applied betting research.

Much of that literature implicitly assumes a single arrow: better prediction leads to better
betting. Our results break that arrow into three distinct links that must each hold independently.
A variable may *predict an outcome* — velocity decline is associated with more runs. It may
nonetheless carry *no incremental information* once the market forecast is conditioned upon —
because the price already reflects it. And even a variable that did carry incremental information
would not automatically be *profitable*, because profitability additionally requires that the edge
exceed transaction costs, survive the vig, and persist after the act of betting moves the line.
Prediction, increment, and profit are three questions, not one.

Forecast encompassing is valuable precisely because it isolates the middle link — the one betting
papers most often skip. A naïve backtest measures something closer to prediction; a
profit-and-loss simulation measures something closer to the third link and is easily flattered by
overfitting and by using stale lines. Encompassing asks the hard question directly: *does this
variable improve on what the price already knows?* In our data, for every variable we measured,
the answer is no — and because the test speaks to increment rather than to a particular staking
scheme, that conclusion does not depend on how one would have bet.

## 7.3 The efficient frontier of public information

We give this boundary a name. We use the term **efficient frontier of public information** to
describe the point at which additional publicly observable variables cease to improve prediction
after conditioning on the market forecast. Inside the frontier lie the observable baseball
variables — pitch count, tier, bullpen, park, weather, velocity, times-through-order — that the
market encompasses. Outside it lie the dimensions our data cannot reach: the timing of price
formation, disagreement across books, and the evolution of the full implied distribution rather
than its mean.

Every hypothesis in this study was, in effect, an attempt to move beyond that frontier using
public state variables. None succeeded. That uniformity is not a series of independent
disappointments; it is a single, coherent mapping of where the frontier sits for one sport, one
month, and one class of information. The contribution is conceptual as much as empirical: the
frontier reframes "we failed to find an edge" as "we located the line beyond which public
information stops helping," and it tells the next researcher where *not* to dig.

## 7.4 The methodological contribution

Although motivated by baseball, the methodology is not baseball-specific. The contribution is an
escalating validation protocol designed to distinguish variables that predict outcomes from
variables that contain incremental information beyond an existing forecast. Each rung strips away
one more class of illusion — overfitting, then selection, then confounding, then
redundancy-with-the-market — so that a hypothesis surviving to the top has been tested against
progressively harder alternatives rather than a single easy one.

> Signal
> ↓
> Robustness
> ↓
> Out-of-sample
> ↓
> Debiasing
> ↓
> Conditional testing
> ↓
> Forecast encompassing
> ↓
> Transfer function

The ladder transfers unchanged to any market with a sharp public forecast and observable state:
NBA totals, NFL spreads, soccer in-play, tennis, racing. A researcher there can adopt the same
sequence, report at which rung each candidate variable is eliminated, and compare results across
domains. We release the pipeline, feature schema, and result artifacts as **The Third Turn
Benchmark (v1.0)** so that future hypotheses can be evaluated against the same reference rather
than re-derived from scratch. Over time a shared benchmark and a citable protocol — "the Third
Turn validation protocol" — may prove more durable than any single finding, because they let a
field accumulate falsifications instead of scattered one-off backtests.

## 8. Remaining questions

We deliberately title this section *Remaining Questions* rather than *Future Work*: it lists what
the evidence genuinely does not answer, not merely what we would like to do next.

Our data cannot separate latency from feed cadence. Because the historical trajectories come from
a single Pinnacle-grade source sampled at roughly one-minute intervals, the uniform sub-one
response ratio in the transfer function is consistent with either a real convergence lag or a
measurement artifact; distinguishing them requires higher-frequency, multi-source capture. For the
same reason we cannot test cross-book price leadership — who moves first, and whether a laggard is
tradable — nor whether the market updates the *shape* of the implied distribution (variance, skew,
tail) as accurately as it updates the mean. Retail live team totals, which some books post and
which our feeds did not expose, remain untested; so does whether the boundary we map for full-game
totals holds for first-five-inning markets that isolate the starters. And the entire study covers
one month and 163 games of one sport: the boundary is characterized precisely, but only under
those conditions. Each of these is a live-data question, and each is the natural subject of the
market-microstructure study our forward-collected streams are built to support.

## What we learned

This project began with a search for an exploitable feature of baseball. It ended by identifying
the empirical boundary at which publicly observable baseball information ceases to provide
incremental predictive value against a sharp live market. That boundary is itself a result. It
redirects future work away from discovering additional baseball variables and toward understanding
how information propagates through live betting markets. The contribution of this study is
therefore not a successful betting strategy, but a reproducible framework for determining when one
does — and does not — exist.
