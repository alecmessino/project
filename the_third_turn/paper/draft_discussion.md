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
information is already incorporated into the market forecast. The variables are informative about
runs and redundant with the price. Prediction survives; increment does not.

Why does this happen? Not because baseball theory is wrong, but because the forecast embedded in a
sharp live market already reflects these variables. Such a forecast is produced by participants
with strong incentives to price observable state correctly and quickly, and the transfer-function
evidence is consistent with that: the line moves in the right direction and by a stable fraction of
the true change in run expectancy after every event type, with no event class systematically under-
or over-priced. A forecast that adjusts proportionately to information shocks is precisely the kind
whose residual should carry no recoverable public-information signal — which is what we observe.

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

The reason a protocol like this matters is a matter of where the burden of proof sits. Sports
betting research frequently terminates after the discovery of an in-sample signal. The present
study instead treated each positive result as a hypothesis requiring progressively stronger
attempts at falsification. The protocol therefore shifts the burden of proof from demonstrating
*prediction* to demonstrating *incremental information beyond an existing market forecast* — a
higher and more economically meaningful standard, and one that a single backtest can never meet.
That shift is a philosophy of evidence, not merely a workflow.

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

## 8. Limitations

We state the conditions under which our conclusion holds, without interpretation. **Scope.** The
study covers 163 games over a single month (June 2026) of one sport; the boundary is characterized
precisely, but only under those conditions, and we make no claim of seasonal or cross-sport
generality. **Odds source.** Historical line trajectories derive from a single Pinnacle-grade
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

## 9. Remaining Questions

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

## 10. Conclusion — what we learned

This project began with a search for an exploitable feature of baseball. It ended by identifying
the empirical boundary at which publicly observable baseball information ceases to provide
incremental predictive value against a sharp live market. That boundary is itself a result. It
redirects future work away from discovering additional baseball variables and toward understanding
how information propagates through live betting markets. The contribution of this study is
therefore not a successful betting strategy, but a reproducible framework for determining when one
does — and does not — exist.
