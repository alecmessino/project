# Evidence Ledger

The quantitative record of **why confidence changed**. Every meaningful observation gets a stable
ID; confidence-register movements and decision-log entries **cite evidence IDs instead of prose**, so
any belief in the program can be traced back to the specific evidence that justifies it.

**Classification:** `Engineering` · `Verification` · `Measurement` · `Data-quality` · `Methodology` ·
`Scientific`. **Confidence impact** uses ↑ / ↓ / → against the affected Confidence-Register
component(s). An entry is a *fact on the record*; whether it promotes anything still requires the
stopping rules (a ledger entry is never a Finding).

| ID | Date | Evidence | Classification | Confidence impact | Affected components | Refs |
|---|---|---|---|---|---|---|
| E-001 | 2026-07-06 | FanDuel live-flag bug fixed (read `inPlay` on the market, not the event); live FanDuel quotes captured for the first time | Engineering | ↑ Collector, ↑ Feed quality | Collector, Feed | collector v1.1 |
| E-002 | 2026-07-06 | Re-arm SPOF fixed: re-arm moved into an `always()` step so a platform cancellation no longer stops collection | Engineering | ↑ Collector | Collector | EP-2, ED-6, GD-1 |
| E-003 | 2026-07-09 | 11 consecutive re-arms (#16→#27), 0 failures, verified against the GitHub Actions API; continuous 3-day checkpointing | Verification | ↑ Collector | Collector | EP-2 |
| E-004 | 2026-07-09 | Integrity independently reproduced at 103,494 rows: 0 malformed / missing / duplicate / future-ts (under the tool's field definition) | Verification | → Integrity (maintained) | Integrity, Dataset | ED-4 |
| E-005 | 2026-07-09 | FanDuel densified (~1k→~10k live quotes); cumulative median sync lag collapsed 640→30 s — confirmed as a forward-fill artifact, not a market change | Measurement | ↑ Measurement (understanding), → Science | Feed, Synchronization | EP-1 |
| E-006 | 2026-07-09 | SR-1 sync sub-gate is quantized to {0}∪[30 s,∞) by the 30 s poll interval; a PASS at median 0 certifies collector co-capture, not <15 s market contemporaneity | Methodology | ↓ Protocol (gate validity) | Protocol, SR-1 | RD-1, ED-2, GD-3 |
| E-007 | 2026-07-09 | Pinnacle is stillborn — 6 pregame rows in one burst, 0 live quotes ever; root cause unknown | Engineering / Verification | ↓ Feed quality; holds Paper 2 readiness Low | Feed, Paper 2 readiness | ED-1, RD-2, KU-1 |
| E-008 | 2026-07-09 | bovada emits no `marketStatus` on any of 27,988 rows; OPEN/SUSPENDED/REMOVED is FanDuel-only (single-book status) | Data-quality | ↓ Feed quality | Feed, Safeguards | RD-4, ED-5 |
| E-009 | 2026-07-09 | 61 FanDuel rows (36 live) carry null odds and pass the integrity gate (odds not a required field); odds heavy-tailed | Data-quality | ↓ bounds the "integrity clean" claim | Integrity | RD-5, ED-4 |
| E-010 | 2026-07-09 | `book_panel` interleaves 2–3 alternate total lines per (game,book,ts) with no main-vs-alt discriminator (~95% of groups) | Data-quality / Methodology | ↓ threatens line-based inference | Feed, SR-1 pairs | RD-3, ED-3 |
| E-011 | 2026-07-09 | Adversarial audit: live panels are 100% July (0/103,494 June rows), temporally/book/data-type disjoint from Paper 1's sample | Verification | → Paper 1 (unchallenged, confirmed) | Paper 1 | — |
| E-012 | 2026-07-09 | 576 nominal cross-book "arbs" dissolved under scrutiny (median divergence 3.6 pp; concentrated in near-settled / suspended / status-unverifiable legs; same-poll co-presence, not executable) | Verification / Rejected | → Science (no evidence of inefficiency) | — | A-01 |
| E-013 | 2026-07-11 | Re-arm chain now 22 consecutive clean re-arms (#16→#38), 0 failures since the pre-fix #14; continuous ~15-min checkpoints across 07-09→07-11 (verified via Actions API) | Verification | → Collector (High, firmer) | Collector | EP-2 |
| E-014 | 2026-07-11 | Cumulative SR-1 median sync lag moved **30 s (07-09) → 91 s (07-10/11)** — non-monotonic; a further symptom of the implementation-dependent metric, not a synchronization regression | Measurement / Methodology | ↓ confidence in the sync-lag metric (not the system) | Synchronization, SR-1 | RD-1, E-006 |
| E-015 | 2026-07-11 | SR-1 overlap-games broke its plateau: 30 → 37 (07-10) → 45 (07-11) as new games enrolled | Dataset / Verification | ↑ Dataset maturity | Dataset, SR-1 | EP-4 |

## How the ledger is used

- **Confidence Register** movements cite the E-IDs that justify them; a level never moves without a
  ledger citation. (Existing register basis text is being migrated to E-ID citations as it is next
  touched — new movements cite E-IDs from the outset.)
- **Governance Decision Log** entries cite the evidence they acted on.
- **Inference Graph** edges cite E-IDs on the path from observation to any paper claim.

## Discipline

An entry records evidence, not a conclusion. Classification is about the *kind* of evidence, not its
importance. A `↑ Measurement, → Science` impact (e.g., E-005) is the common and correct shape: the
instrument got better, the science did not move. Never log an interpretation as evidence.
