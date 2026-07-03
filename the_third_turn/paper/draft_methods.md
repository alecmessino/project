# Methods (Pass 3 draft)

> **Drafting stance:** describe an *experimental design*, not a software pipeline. Organize around
> the research question, not the code. Forecasting terminology over baseball terminology at every
> fork. No subsection is named for a hypothesis (TTOP, velocity, …) — those are objects of study,
> not methods. Five subsections plus a short justification of the central test.

Our design compares two forecasts of the same quantity — the number of runs a game has left to
score at a given moment — and asks whether publicly observable state improves the forecast already
implied by the market. The unit of analysis throughout is the *half-inning snapshot*: a single
moment in a single game at which both the market's live total and the full game state are observed.
This section defines the data behind each snapshot (§3.1), how state variables are constructed from
it (§3.2), the escalating protocol by which a candidate variable is tested (§3.3), the statistical
estimators applied at each rung (§3.4, including why forecast encompassing is the central test),
and the artifacts released for reproduction (§3.5).

## 3.1 Data

The study draws on 163 Major League Baseball games played in June 2026, each observed from three
aligned sources. **Market prices.** Live full-game total (Over/Under) lines and their associated
prices were recorded as one-minute trajectories from a single Pinnacle-grade feed, giving, for each
game, the market's evolving point forecast of final total runs and its implied Over probability.
**Game state.** Complete play-by-play and boxscore records from the MLB Stats API supply, at every
plate appearance, the inning and half, base-out state, score, batting-order position, the identity
and pitch count of the pitcher, and the times each batter has faced the current starter. **Pitch
measurement.** Pitch-level release speeds (`startSpeed`) from the same feed provide within-game
velocity trajectories. Venue and weather (temperature, wind speed and direction relative to the
field) and each game's realized final total complete the record. Sources are joined on game
identifier and, for odds, on timestamp. The one-minute cadence and single odds source are the
principal constraints on what the design can measure; their consequences are stated in §8.

## 3.2 Feature construction

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
run-expectancy table. No feature uses information unavailable at the snapshot it describes.

## 3.3 Validation protocol

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
enforce it.

## 3.4 Statistical evaluation

Each rung is a specific estimator, all computed out-of-sample by leave-one-game-out.

**Forecast encompassing.** For remaining runs `Y`, market forecast `B`, and a candidate feature set
`X`, we fit three ridge-regularized linear forecasts — `Y ~ B`, `Y ~ X`, and `Y ~ B + X` — and
compare their out-of-sample R² and mean absolute error. If `Y ~ B + X` does not improve on `Y ~ B`,
the market encompasses `X`. The sharpest form regresses the market's forecast error `Y − B`
directly on `X`: if `X` cannot predict the error out-of-sample, it carries no information the price
lacks. A per-feature variant (E+) fits `Y ~ B + Xᵢ` against `Y ~ B` for each variable individually,
so that two proxies for the same state cannot mask one another in the joint model. Continuous
predictors are standardized; the ridge penalty is fixed a priori and applied to all non-intercept
terms.

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
Hanley–McNeil variance.

**Transfer function.** For each in-game event we pair the true change in run expectancy `ΔRE` with
the converged change in the live total one and five minutes later (`ΔBook`), and estimate the
response ratio `ΔBook / ΔRE` by event type together with a single common slope through the origin.
Mean `ΔRE` by event type is checked against published linear weights as a validity control.

**Uncertainty.** All point forecasts are out-of-sample (leave-one-game-out); interval estimates use
the Hanley–McNeil formula for AUC, Wilson intervals for proportions, and the bootstrap otherwise.
Differences smaller than the width of their intervals are reported as such and are not interpreted
as effects.

## 3.5 Reproducibility

Every quantity in this paper is recomputed from committed inputs by a fixed set of scripts;
estimation is deterministic (leave-one-game-out folds and fixed seeds), so results regenerate
exactly. To facilitate reproduction we release the cleaned datasets, the feature schema, the
evaluation protocol of §3.3, and reference implementations of the market forecast, the
remaining-runs model, the encompassing tests, and the transfer function as the initial release of
the **Third Turn Benchmark**, archived under a persistent DOI alongside the code repository and the
research log. The release is described more fully where it is introduced as a contribution; here we
note only that the frozen result artifacts (`output/*.json`) and the scripts that produce them are
sufficient to reconstruct every figure and number without access to the original feeds.
