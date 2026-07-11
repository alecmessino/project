# Operations & Research Governance

How the Third Turn platform is operated and governed. The daily review runs the format in
`DAILY_REPORT_TEMPLATE.md` (v4 Governance Review): each day is an explicit Bayesian update on
confidence, not a status report.

## The governance framework (four pillars)

| Pillar | Question it answers | File |
|---|---|---|
| **Engineering Debt** | What can break? (system, technical, documentation faults) | `ENGINEERING_DEBT_AND_KNOWN_UNKNOWNS.md` |
| **Research Debt** | What could invalidate a future inference? | `RESEARCH_DEBT.md` |
| **Confidence Register** | What does the evidence currently justify believing? | `RESEARCH_CONFIDENCE_REGISTER.md` |
| **Governance Decision Log** | Why did those beliefs change? | `GOVERNANCE_DECISION_LOG.md` |

## Supporting records

| File | Role |
|---|---|
| `DAILY_REPORT_TEMPLATE.md` | The v4 Governance Review format (the daily prompt). |
| `ENGINEERING_PREDICTION_LOG.md` | Dated engineering hypotheses and their resolutions (a prediction is never a research finding). |
| `STOPPING_RULE_CLASSIFICATION.md` | Each gate labeled empirically-validated / provisional / design-assumption / awaiting-evidence. |
| `SR1_sync_lag_design_review.md` | The SR-1 sync-lag Candidate design defect and a proposed (undecided) redesign. |
| `POSTMORTEM_2026-07-06_collector_outage.md` | The re-arm SPOF incident and its fix. |

## First principles

- **Health ≠ Capability.** A missing capability (third book, PMF continuity) is not a failure.
- **Four kinds of progress, never blurred:** engineering · measurement · dataset growth · scientific.
  Almost every day is the first three.
- **Fact vs hypothesis.** State observed properties as fact; label architectural conclusions as
  Candidates; flag implementation-dependent metrics for redesign rather than silently revising them.
- **Discipline:** no analysis unless a stopping rule objectively clears; Paper 1 frozen; Paper 2
  fully gated; the goal is that any future result survives hostile scrutiny.
