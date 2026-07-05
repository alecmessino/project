# Changelog

Research versions, not software versions. The Protocol (method) and the Benchmark Dataset (data)
version independently.

## Third Turn Protocol — v1.0 (2026-07-04)
- First numbered release of the seven-rung ladder (signal → robustness → out-of-sample → debiasing →
  conditional testing → forecast encompassing → transfer function) in `../protocol/protocol.md`,
  with the safeguard registry (`../protocol/safeguards.md`, S-01–S-14) and stopping rules
  (`../protocol/stopping_rules.md`, SR-1–SR-3).
- Versioning policy: a new safeguard or a modified rung bumps the minor version (v1.1…); a
  structural change to the ladder bumps the major version (v2.0). The registry is deliberately
  near-frozen at 14 — add only when a genuinely new failure mode appears.

## Third Turn Benchmark Dataset — v1 (preview)
- 163 MLB games, June 2026: half-inning snapshots (`B`, `Y`, features), 6,414-event transfer
  stream, remaining-runs snapshots, and frozen result artifacts.
- Ten reference signals with elimination rungs (`dataset/reference_results.md`).
- Known scope: single month, single sharp-book feed at ~1-min cadence, static RE24/park constants.

_Unreleased / planned:_ persistent DOI and packaged archive at paper publication; future dataset
versions (v2+) as the live streams accumulate and enable cross-book / distribution-shape tests.
