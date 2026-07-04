# Baselines

The Third Turn Benchmark is difficult because the baseline is strong. A new signal must improve on
these; against a sharp market, that is a high bar by construction.

## 1. The market forecast (`B`)

The incumbent forecast of remaining runs is the live total minus runs already scored,
`B = live_total − runs_scored`, read from `../../../data/trajectories.jsonl`. This is the primary
benchmark for forecast encompassing (rung 6): a signal is incremental only if it improves a model
that already contains `B`.

## 2. The remaining-runs model

A leave-one-game-out ridge forecast of remaining runs from game state only — inning remaining,
starter tier, bullpen quality, score differential (no fatigue terms). Reference implementation:
`../../../remaining_runs.py`. Out-of-sample R² = 0.226; adding fatigue terms (TTO, pitch count,
starter-in) leaves MAE unchanged (≈0.001 runs, no improvement). This is the "model side" baseline: it shows that a
well-specified state model needs nothing the market lacks either.

## Reference implementations of the protocol over these baselines

| rung | script |
|---|---|
| 3 Out-of-sample, 6 Forecast encompassing (+ E+) | `../../../encompass.py` |
| 4 Debiasing, calibration | `../../../calibration.py` |
| 7 Transfer function | `../../../program_a.py` |

Each reads the frozen caches under `../../../output/` and reproduces the numbers in
`../reference_results.md`.
