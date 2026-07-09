# Stopping-rule classification

A maturity label for every gate in `protocol/stopping_rules.md`, so the project is explicit about
what it has *established* versus what it has *assumed*. This is annotation only; it changes no
threshold and no normative rule text.

**Labels.**
- **Empirically validated** — the criterion has been tested against data and shown to deliver the
  property it claims (e.g., a power analysis confirms the sample size, or a held-out check confirms
  the metric measures what it intends).
- **Provisional** — a plausible placeholder number, not yet validated against a power analysis or
  evidence. Usable as a gate, but its exact value is not load-bearing.
- **Design assumption** — a principle asserted from prior reasoning or a documented lesson
  (safeguards, decisions log), not from this project's own data.
- **Awaiting evidence** — a forward gate whose counters are not yet even instrumented.

> Headline honesty: **no stopping-rule threshold is yet "empirically validated."** SR-1 is a working
> block built on a sound design assumption with provisional numbers; SR-2 and SR-3 are not yet
> instrumented. That is expected at this stage and is the point of tracking it.

## SR-1 · Cross-book leadership

| Sub-criterion | Statement | Classification | Basis / note |
|---|---|---|---|
| Overall principle | Leadership estimation needs dense, contemporaneous cross-book overlap or estimates are noise-dominated | **Design assumption** | From the one-night artifact lesson (S-10, S-11; July 3–4 decisions-log entries). Sound, but asserted from that episode, not from a power curve. |
| ≥ 2,000 simultaneous live pairs | Volume of paired live quotes | **Provisional** | Unvalidated target. Also confounded: the "pairs" count does not yet account for alt-line multiplicity or a forward-fill staleness horizon (see Engineering Debt). Currently PASS (10,359) but the margin is soft until those are pinned. |
| ≥ 100 independent games | Breadth of overlap | **Provisional** | Unvalidated target. Presently stalled on new-game enrollment, not maturation (EP-4). |
| median sync lag < 15 s | Contemporaneity of paired quotes | **Design assumption (intent) + Candidate design defect (implementation)** | The *intent* (contemporaneity, S-11) is a sound design assumption. The *implementation* is implementation-dependent: quantized to {0} ∪ [30 s, ∞) by the 30 s poll interval, so a PASS certifies collector co-capture, not sub-15 s market synchronization. Flagged as a redesign Candidate (see `SR1_sync_lag_design_review.md`, ED-2). **Not** revised. |
| ≥ 3 sportsbooks live | Independent sources | **Design assumption / Provisional** | Plausible that a 3rd book improves leadership estimation, but unvalidated — a tracked Known Unknown (KU-3). Currently structurally blocked by the stillborn pinnacle feed (ED-1). |

**SR-1 verdict:** genuinely and correctly **BLOCKED**. The block rests on the two structurally-sound
sub-gates (games, books); the pairs and lag sub-gates each carry a caveat above but do not currently
drive the verdict.

## SR-2 · Distribution dynamics *(forward gate — not yet active)*

| Sub-criterion | Statement | Classification | Basis / note |
|---|---|---|---|
| ≥ 50 games continuous implied-PMF through ≥ 6 innings | Within-game distribution continuity | **Awaiting evidence** | Counters not instrumented; the single sharp source (Pinnacle) is stillborn, so the PMF stream does not yet exist in live form. |
| Event timestamps joinable to the PMF stream (< 30 s) | Alignment | **Provisional** | Threshold plausible; untested. |

**SR-2 verdict:** **Awaiting evidence**, and further blocked upstream by the same dead Pinnacle feed
that blocks SR-1's third book. Whether SR-2 is in fact the more promising paper is a Known Unknown (KU-4).

## SR-3 · Real-line encompassing robustness *(forward gate — planned, not written)*

| Sub-criterion | Statement | Classification | Basis / note |
|---|---|---|---|
| Alternate-total strips for ≥ 30 games | De-vig robustness re-run of the encompassing test | **Awaiting evidence** | Pre-submission checklist item, not instrumented. Alt-lines *are* present in `book_panel` but are undiscriminated (main-vs-alt hazard, ED-3), and this gate would run on the sharp June encompassing cache, not on the live recreational panels. |

**SR-3 verdict:** **Awaiting evidence**; not currently on the critical path.

## Discipline reminder

A rule may be loosened only with a stated reason in the decisions log, never mid-analysis to rescue a
result. Re-labeling a rule from *provisional* to *empirically validated* requires the validating
analysis to be run and recorded — the label is a claim like any other and must be earned.
