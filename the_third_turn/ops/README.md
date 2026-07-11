# Operations & Research Governance

How the Third Turn platform is operated and governed. The daily review runs `DAILY_REPORT_TEMPLATE.md`
(v4 Governance Review): each day is an explicit Bayesian update on confidence, not a status report.

> **Status: the governance framework is FEATURE-COMPLETE (2026-07-09).** No further governance
> artifacts should be added. The program has entered **Phase 4: Evidence Accumulation** — the highest
> return now is collecting a materially larger dataset with minimal intervention, not refining the
> process. See the admission rule below.

## The four governance pillars

| Pillar | Question it answers | File |
|---|---|---|
| **Engineering Debt** | What can break? (system, technical, documentation faults) | `ENGINEERING_DEBT_AND_KNOWN_UNKNOWNS.md` |
| **Research Debt** | What could invalidate a future inference? | `RESEARCH_DEBT.md` |
| **Confidence Register** | What does the evidence currently justify believing? | `RESEARCH_CONFIDENCE_REGISTER.md` |
| **Governance Decision Log** | Why did those beliefs change? | `GOVERNANCE_DECISION_LOG.md` |

## Self-calibration layer (the citation system)

| Artifact | Role | File |
|---|---|---|
| **Evidence Ledger** | Every meaningful observation → a stable `E-ID`; confidence moves cite E-IDs, not prose | `EVIDENCE_LEDGER.md` |
| **Assumption Register** | The program's load-bearing assumptions (`A-ID`), with evidence for/against | `ASSUMPTION_REGISTER.md` |
| **Inference Graph** | `Observation → Evidence → Candidate → Finding → Paper Claim`, every edge cited | `INFERENCE_GRAPH.md` |

Together these close the loop: a belief (Confidence Register) cites the evidence (Evidence Ledger)
that moved it, the decision (Decision Log) that recorded it, the assumptions (Assumption Register) it
rests on, and the graph (Inference Graph) that carries it toward — or withholds it from — a paper claim.

## Supporting records

`DAILY_REPORT_TEMPLATE.md` (the daily prompt) · `ENGINEERING_PREDICTION_LOG.md` ·
`STOPPING_RULE_CLASSIFICATION.md` · `SR1_sync_lag_design_review.md` ·
`POSTMORTEM_2026-07-06_collector_outage.md`.

## Artifact-admission rule (governance must not outgrow the research)

Once governance is built, governance itself becomes technical debt if it grows faster than the
research. **A new permanent governance artifact may be added only if it does at least one of:**

1. reduces false-discovery risk,
2. increases reproducibility,
3. improves external auditability, or
4. shortens time to publication.

If it does none of those, it is not added. The framework above is judged complete against this rule;
extending it further requires a Governance Decision Log entry justifying the addition against these
four criteria.

## First principles

- **Health ≠ Capability.** A missing capability (third book, PMF continuity) is not a failure.
- **Four kinds of progress, never blurred:** engineering · measurement · dataset growth · scientific.
- **Fact vs hypothesis.** State observed properties as fact; label architectural conclusions as
  Candidates; flag implementation-dependent metrics for redesign rather than silently revising them.
- **Phase 4 priorities:** (1) stabilize the collector — no feature work unless it addresses
  Engineering or Research Debt; (2) resolve the highest-impact Research Debt (RD-1 sync-gate validity,
  RD-2 third live book, RD-3 alternate-line discrimination); (3) accumulate a materially larger live
  dataset with minimal intervention; (4) resist analysis until the predefined gates objectively clear.
