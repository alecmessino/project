# The Third Turn Protocol & Benchmark Dataset

> **A predictive signal should be evaluated against the market's own forecast, not merely against
> the outcome.**

This directory is the citable front door for two separate, deliberately named artifacts:

- **The Third Turn Protocol** — a domain-general *method*: an escalating validation ladder for
  deciding whether a candidate predictive signal carries information beyond an existing forecast.
  Canonical definition in [`evaluation.md`](evaluation.md).
- **The Third Turn Benchmark Dataset (v1)** — the *data*: 163 MLB games (June 2026) as aligned
  half-inning snapshots of a sharp live market forecast and full game state, plus the frozen result
  artifacts against which new signals can be compared. Schema in
  [`dataset/schema.md`](dataset/schema.md).

A method is not a dataset; a benchmark implies a dataset and a protocol implies a scientific method,
so we keep the names apart. The Protocol can be applied to any domain (finance, weather, elections,
forecasting competitions); the Dataset is one instance it was first validated on.

## Why it exists

Countless projects produce "here is a signal." Very few establish "here is how to tell whether a
signal survives conditioning on an existing forecast." Prediction, *incremental* information, and
profit are three distinct questions; ordinary predictive accuracy answers only the first. The
Protocol isolates the second — the one that matters when a strong incumbent forecast already exists.

## Contents

```
benchmark/
├── README.md                    this file
├── evaluation.md                THE PROTOCOL — the canonical ladder (start here)
├── CITATION.cff                 how to cite the protocol and dataset
├── CHANGELOG.md                 version history
├── dataset/
│   ├── schema.md                the half-inning snapshot schema (B, Y, ΔRE, features, events)
│   └── reference_results.md     the ten reference signals + the rung each is eliminated at
│   └── baseline/README.md       the two strong baselines every signal must beat
└── examples/
    └── report_template.md       how to report where your signal is eliminated
```

## How to evaluate a new signal

1. Read [`evaluation.md`](evaluation.md).
2. Express your signal as a per-snapshot feature `X` over the schema in
   [`dataset/schema.md`](dataset/schema.md) (or your own dataset with an incumbent forecast `B`, a
   realized outcome `Y`, and candidate features).
3. Run the ladder. Against this dataset, the reference implementations are
   `../encompass.py` (rungs 3 & 6), `../calibration.py` (rung 4), and `../program_a.py` (rung 7).
4. Report the earliest rung your signal fails, using
   [`examples/report_template.md`](examples/report_template.md), and compare against
   [`dataset/reference_results.md`](dataset/reference_results.md).

## How to cite

See [`CITATION.cff`](CITATION.cff). In text: *evaluated with the Third Turn Protocol (Messino,
2026); results reported against the Third Turn Benchmark Dataset v1.*

## Status

**Preview / initial release.** A persistent DOI and a packaged, versioned archive are pending
publication of the accompanying paper. Until then this directory and the repository it lives in are
the reference; the frozen result artifacts under `../output/*.json` are recomputable from
`../data/trajectories.jsonl` with the scripts noted above.

## License

Code: MIT (see repository root). Data and documentation: CC BY 4.0 (intended; to be finalized at
the DOI release).
