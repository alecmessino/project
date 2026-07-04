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
  stronger paper than price leadership. (Note: the +0.14 implied skew here is the *full-game
  per-team* distribution, a different object from Paper 1's +1.23 *remaining-runs* skew.)

## Daemon priority changes (why: tonight captured zero simultaneous live quotes)

1. **Alternate-total strips (highest value).** Unlocks the implied CDF → implied mean → Paper 1
   de-vig appendix and Paper 2 distribution work. Single highest-leverage feature.
2. **Three–four books, not two.** Two books ask "who leads"; four ask "how does information
   propagate through the market" — a network question, the better framing.
3. **Suspension / resume timestamps.** Books vanish around key events; without this, latency work is
   noise, and "zero simultaneous live quotes" tonight is likely partly a coverage/suspension gap.
4. **Quote age / freshness flag.** Distinguishing fresh from stale removes many apparent
   inefficiencies (see the 1-hour staleness above).

## Paper 2 reframing

Not "find inefficiencies" but **"how does information propagate through partially synchronized
forecasting systems?"** Sportsbooks are the observable laboratory; the transferable question is a
forecasting one. Same evidentiary standard as Paper 1.

**Stopping rule:** do not re-analyze leadership until the panel is ~10× larger (hundreds of games,
thousands of live quote changes, with suspension + quote-age fields). Until then, collect, don't
conclude.
