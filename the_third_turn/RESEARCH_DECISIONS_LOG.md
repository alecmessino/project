# Research Decisions Log

A scientific log (not a code changelog): every time a promising signal died, what it was, why it
looked real, the confound that killed it, the safeguard that now catches it, and the verdict. The
value compounds — it records *why each robustness check exists*, which is exactly the question a
referee asks, and it is the raw material for the methods paper.

**Standing posture:** the goal is to discover why we might be wrong, not to prove we are right. A
signal is "not yet eliminated," never "confirmed." Positive results only earn belief after they
survive the same gauntlet that rejected everything below.

## Rejections & resolutions

| Date | Claim | Why it looked real | Confound / flaw | Safeguard added | Verdict |
|---|---|---|---|---|---|
| Jun 2026 | TTOP: 3rd-time-through Over is +EV | Community consensus; raw 3rd-turn WHIP lift | Decay is continuous, not a cliff; market prices it | Gradient (soft) model + LOGO out-of-sample + encompassing | Rejected |
| Jun 2026 | Velocity decline predicts scoring | Tier+velocity AUC 0.61 | Post-treatment: drop defined only if starter survived to be shelled (survivorship) | Re-measure in a pre-treatment early window (debiasing) | Artifact (AUC→0.52) |
| Jun 2026 | Fatigued bullpen amplifies the cliff | Intuition; "gassed pen concedes more" | No effect once isolated | Restrict to the bullpen's own innings | Rejected |
| Jun 2026 | Drop→Over reverts up | Final avg +0.69 above the dropped line | Right-skew (mean≠median); OOS below breakeven | Median/skew check + OOS threshold sweep | Rejected |
| Jun 2026 | Drop→Under stays low | 60% overall, 63% on ≥10% drops | Non-monotone; snapshot-inning dependent; recent-sample concentration | Banded robustness + snapshot-inning perturbation + recency split | Not robust |
| Jun 2026 | Alternate-line skew is buyable | Right-skew +1.36 in the tail | Empirical win% < efficient-implied at every hook | Empirical vs efficient-implied at each half-run increment | Priced |
| Jun 2026 | Early-run anchoring (under-reaction) | Intuition; a 1st-inning burst "should" under-price | 49/50 bursts hit-driven; market prices the climb | Cause split (hit-driven vs fluky) | Priced |
| Jun 2026 | Weather/park under-priced | Intuition; hitter-friendly = more runs | Hitter-friendly Overs hit 46% < 50% (market over-adjusts) | Conditional split vs breakeven | Priced |
| Jun 2026 | Fatigue improves a state model | Fatigue "should" add to remaining-runs | Game state already contains the info | Incremental MAE, LOGO | ΔMAE −0.001 |
| Jun 2026 | Some public feature beats the market | Features predict runs (OOS R² 0.279) | The market already encompasses them | (Y−B)~X OOS + per-feature E+ + Clark–West | Encompassed (err R² −0.037) |
| Jul 2026 | Book error is +0.49 → market is biased | Mean book error +0.49 runs | Mean–median gap of a right-skewed law (a balanced line tracks the median) | median(E) vs mean(E); slope of E on B | Explained, not a bias (intercept) |
| Jul 3–4 2026 | FanDuel leads Bovada | "Reaches new levels first" 73:5 | Unequal sampling density (FanDuel 3.7× more quotes) | Density-neutral equal-cadence lagged cross-correlation | Not identifiable (r +0.034 vs +0.023) |
| Jul 3–4 2026 | Cross-book divergence (live inefficiency) | Books differ 61% of the time, ~0.46 runs | 66% are one 0.5 tick; 90% pregame; **zero simultaneous live quotes** | Tick-size breakdown + regime split + simultaneous-live check | Not observed (not a finding yet) |

## Why the safeguards exist (referee-facing summary)

- **Out-of-sample by leave-one-game-out** — an in-sample edge is the weakest evidence.
- **Pre-treatment re-measurement** — because a variable defined on an outcome-selected subsample
  (velocity drop) manufactures a signal from survivorship.
- **Forecast encompassing + Clark–West** — because predicting the outcome ≠ improving a forecast
  that already exists; nested MSPE comparison is biased toward the small model without the
  correction.
- **Median-vs-mean / intercept checks** — because a right-skewed target makes a balanced forecast
  look "biased" when it is only tracking a different functional.
- **Equal-cadence resampling before any lead-lag** — because unequal quote frequencies bias naïve
  "who-moved-first" estimators (either direction, depending on the estimator).
- **Simultaneous-live / synchronization checks before any cross-book claim** — because comparing
  non-contemporaneous quotes measures nothing.

## Meta-note (for the methods paper's opening vignette)

On 2026-07-03/04, the first night of live cross-book data produced two attractive findings — a
14:1 lead-lag and a 61% cross-book divergence. Both dissolved within an hour under the same
validation discipline developed for the historical study: identify the measurement confound,
redesign the estimator, watch the apparent effect vanish. The reproducibility of that *process* —
independent of any particular result — is itself the contribution. This vignette should open the
methods paper.
