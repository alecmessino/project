# Research Decisions Log

A scientific log (not a code changelog): every time a promising signal died, what it was, why it
looked real, the confound that killed it, the safeguard that now catches it, and the verdict. The
value compounds — it records *why each robustness check exists*, which is exactly the question a
referee asks, and it is the raw material for the methods paper.

**Standing posture:** the goal is to discover why we might be wrong, not to prove we are right. A
signal is "not yet eliminated," never "confirmed." Positive results only earn belief after they
survive the same gauntlet that rejected everything below.

Safeguard IDs (S-nn) are defined in `../protocol/safeguards.md`; each was born from a row below.

## Rejections & resolutions

| Date | Claim | Why it looked real | Confound / flaw | Safeguard(s) | Verdict |
|---|---|---|---|---|---|
| Jun 2026 | TTOP: 3rd-time-through Over is +EV | Community consensus; raw 3rd-turn WHIP lift | Decay is continuous, not a cliff; market prices it | S-01, S-05 | Rejected |
| Jun 2026 | Velocity decline predicts scoring | Tier+velocity AUC 0.61 | Post-treatment: drop defined only if starter survived to be shelled (survivorship) | S-03 | Artifact (AUC→0.52) |
| Jun 2026 | Fatigued bullpen amplifies the cliff | Intuition; "gassed pen concedes more" | No effect once isolated to the pen's own innings | S-04 | Rejected |
| Jun 2026 | Drop→Over reverts up | Final avg +0.69 above the dropped line | Right-skew (mean≠median); OOS below breakeven | S-08, S-01 | Rejected |
| Jun 2026 | Drop→Under stays low | 60% overall, 63% on ≥10% drops | Non-monotone; snapshot-inning dependent; recent-sample concentration | S-02 | Not robust |
| Jun 2026 | Alternate-line skew is buyable | Right-skew +1.36 in the tail | Empirical win% < efficient-implied at every hook | S-04 | Priced |
| Jun 2026 | Early-run anchoring (under-reaction) | Intuition; a 1st-inning burst "should" under-price | 49/50 bursts hit-driven; market prices the climb | S-04 | Priced |
| Jun 2026 | Weather/park under-priced | Intuition; hitter-friendly = more runs | Hitter-friendly Overs hit 46% < 50% (market over-adjusts) | S-04 | Priced |
| Jun 2026 | Fatigue improves a state model | Fatigue "should" add to remaining-runs | Game state already contains the info | S-01, S-05 | ΔMAE −0.001 |
| Jun 2026 | Some public feature beats the market | Features predict runs (OOS R² 0.279) | The market already encompasses them | S-05, S-06 | Encompassed (err R² −0.037) |
| Jul 2026 | Book error is +0.49 → market is biased | Mean book error +0.49 runs | Mean–median gap of a right-skewed law (a balanced line tracks the median) | S-08 | Explained, not a bias (intercept) |
| Jul 3–4 2026 | FanDuel leads Bovada | "Reaches new levels first" 73:5 | Unequal sampling density (FanDuel 3.7× more quotes) | S-10 | Not identifiable (r +0.034 vs +0.023) |
| Jul 3–4 2026 | Cross-book divergence (live inefficiency) | Books differ 61% of the time, ~0.46 runs | 66% are one 0.5 tick; 90% pregame; **zero simultaneous live quotes** | S-11 | Not observed (not a finding yet) |

## Review-driven safeguards

Some safeguards were born from external review rather than a specific false positive; they are
logged here so their provenance is preserved too.

| Date | Safeguard | Born from |
|---|---|---|
| Jul 2026 | S-06 (nested forecast-comparison inference) | Referee: a raw OOS-MSPE comparison is biased toward the small model; the central null needs Clark–West + a CI |
| Jul 2026 | S-07 (cluster-aware power / MDE) | Referee: a null-result paper must state what it was powered to detect |
| Jul 2026 | S-09 (estimator/penalty sensitivity) | Referee: confirm the encompassing result is invariant to the ridge penalty |
| Jul 2026 | S-13 (claims conditioned on measurement resolution) | Referee: instrument resolution ≠ market resolution |
| — | S-12 (transfer-function magnitude/asymmetry) | Design of the transfer function: a uniform sub-1 ratio can be a single-source low-pass filter, so only asymmetry is evidence |
| — | S-14 (quote-lifecycle / staleness) *(provisional)* | The ~1-hour forward-fill staleness in the divergence probe; field not yet collected |

## Meta-note (for the methods paper's opening vignette)

On 2026-07-03/04, the first night of live cross-book data produced two attractive findings — a
14:1 lead-lag and a 61% cross-book divergence. Both dissolved within an hour under the same
validation discipline developed for the historical study: identify the measurement confound,
redesign the estimator, watch the apparent effect vanish. The reproducibility of that *process* —
independent of any particular result — is itself the contribution. This vignette should open the
methods paper.
