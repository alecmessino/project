# Live microstructure — running notes

Exploratory notes on the runner-banked live streams. **Standing rule: no substantive conclusion
from one night.** Both candidate findings below dissolved under measurement-process scrutiny; that
is the useful result. Reproduce with `microstructure_probe.py`.

## Data on hand (first night, 2026-07-03 → 07-04, ~23h)

| stream | rows | content |
|---|---|---|
| `book_panel` | 28k | FanDuel + Bovada game totals, change-only, 21 games, **10% live** |
| `team_total_panel` | 2.1k | Pinnacle implied *per-team* run distribution — line, σ, skew, **full pmf** |
| `game_state_panel` | 3k | inning/out/score/base/TTO changes, event matching |
| `ledger` | 3 | legacy ARM fires (refuted rule; informational) |

## Candidate finding 1 — cross-book divergence → DOES NOT SURVIVE

Headline looked strong: FanDuel and Bovada disagree on the total **61%** of the time, mean gap
0.46 runs. The validation checklist deflates it:
- **Convention:** 100% of lines on the 0.5 grid — clean, no push/half-run issue.
- **Tick size:** 66% of disagreements are a single 0.5 tick; only **~20% of all observations** are a
  material (≥1-run) gap. "Disagree 61%" is mostly one-tick rounding.
- **Regime:** 90% of rows are pregame; forward-fill staleness at comparison is a median of ~1 hour
  (stable pregame lines). A 0.5 pregame gap that sits for an hour is ordinary market-making.
- **Live overlap:** **zero** timestamps where *both* books were quoting live simultaneously. There
  is therefore no live cross-book divergence result in this data at all.

Verdict: not a finding yet. The interesting object (live divergence) was never observed, because
the daemon did not capture the two books live at the same moment.

## Candidate finding 2 — cross-book leadership → NOT IDENTIFIABLE (and the lesson is the keeper)

> **Naïve lead-lag estimators are biased under unequal quote frequencies.**

- Naïve "who reaches a new line level first" says FanDuel leads Bovada **73:5**. But FanDuel is
  sampled **3.7× more densely**, so it mechanically arrives first. A gap-closing estimator *flips*
  to Bovada — same confound, opposite sign (its counts track the 3.7× record ratio).
- Density-neutral test (resample both to a 60-s grid, lagged cross-correlation of changes):
  FanDuel-leads r = +0.034 vs Bovada-leads r = +0.023 — both ≈ 0, indistinguishable. **Leadership
  is not identifiable from one night.**

This is the paper's own discipline turned on the microstructure data, and it is worth keeping as a
**future Paper-2 appendix**: *"Naïve lead-lag estimators are biased under unequal quote
frequencies; use equal-cadence resampling or an event study."* The lesson generalizes beyond sport.

## What survives / is promising

- **The implied-distribution panel.** Pinnacle's per-team full pmf every snapshot (implied σ, skew
  banked) is unusual — most datasets carry only line + odds. It is the substrate for
  variance-repricing, skew evolution, uncertainty collapse, and inning-level entropy — plausibly a
  stronger paper than price leadership, and gated by **SR-2** in
  [`protocol/stopping_rules.md`](protocol/stopping_rules.md). (Note: the +0.14 implied skew here is
  the *full-game per-team* distribution, a different object from Paper 1's +1.23 *remaining-runs*
  skew.)

## Daemon priority changes (reordered: overlap is now the scarce resource)

Tonight captured **zero simultaneous live quotes**, so the binding constraint is not "more data,"
it is *contemporaneous* data. Reordered accordingly:

1. **Simultaneous live coverage (highest).** Without overlap there is no microstructure — full stop.
   Achieve it however works: tighter live polling of both books in one window, prioritizing books
   with real live coverage, and logging every live poll (not change-only) so overlap is measurable.
2. **Alternate-total strips.** Now serves *both* papers — implied CDF → implied mean (Paper 1 de-vig
   appendix) and distribution calibration (Paper 2). Excellent leverage once overlap exists.
3. **Quote lifecycle.** Suspended / resumed / age / time-since-update. Indispensable the moment
   overlap exists; also tells coverage gaps apart from genuine disagreement (see the 1-hour
   staleness above).
4. **Additional books.** Useful only if they overlap live — three asynchronous books are not better
   than two synchronized ones. Add after 1–3 are working.

## Paper 2 reframing

Not "find inefficiencies" but **"how does information propagate through partially synchronized
forecasting systems?"** Sportsbooks are the observable laboratory; the transferable question is a
forecasting one. Same evidentiary standard as Paper 1.

## Stopping rule

The leadership gate is now canonical as **SR-1** in [`protocol/stopping_rules.md`](protocol/stopping_rules.md)
(≥2,000 simultaneous live quote pairs, ≥100 overlap games, median sync lag <15 s, ≥3 live books).
`microstructure_probe.py` prints its live status each run — tonight all four FAIL. The lead-lag and
divergence lessons are catalogued as safeguards **S-10** and **S-11** in
[`protocol/safeguards.md`](protocol/safeguards.md), with their failures logged in
[`decisions/RESEARCH_DECISIONS_LOG.md`](decisions/RESEARCH_DECISIONS_LOG.md).
