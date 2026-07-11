# Research Confidence Register

The running **posterior**: given everything learned so far, how much confidence does the evidence
currently justify in each part of the research program? This is the counterpart to Research Debt —

- **Engineering Debt** asks: what can break?
- **Research Debt** asks: what could invalidate a future inference?
- **Confidence Register** (this file) asks: what does the evidence *currently justify believing*?
- **Governance Decision Log** asks: why did those beliefs change?

**Scale (ordinal):** `Very Low` · `Low` · `Moderate` · `High` · `Very High`. A level is a claim like
any other and must be *earned by verified evidence*, never by optimism or by data volume. The daily
Governance Review produces the update; every change is justified in one sentence and logged in the
Governance Decision Log. **Only change a level when evidence justifies it.** Optimize for reliability,
never for positive findings.

## Current register — baseline set 2026-07-09

| Component | Level | Direction | Basis (verified evidence) |
|---|---|---|---|
| **Collector reliability** | High | baseline | 11 consecutive re-arms (#16→#27) across 3 days verified against the Actions API; continuous ~15-min checkpoints; the SPOF fix confirmed (EP-2). Held below Very High by two uncovered failure modes (hard runner loss; <60-min-cancel dead zone). |
| **Feed quality** | Moderate | baseline | bovada dense/reliable; fanduel densified (EP-1). But behind the green check: status is single-book (bovada emits none), 61 null-odds rows (36 live) pass integrity, odds are heavy-tailed, and pinnacle is stillborn. Real data-quality gaps (RD-4, RD-5). |
| **Synchronization (understanding)** | High | baseline | The 640→30 s collapse is now *explained* as a forward-fill artifact of sparse-vs-dense coverage; fresh-both-books lag is ~0. We understand the instrument. |
| **Synchronization (gate validity)** | Moderate | baseline | Understanding the metric is not the same as trusting the gate: the SR-1 sync sub-gate is a Candidate design defect (certifies co-capture, not <15 s contemporaneity; RD-1). Validity unresolved by design, not by evidence. |
| **Dataset maturity** | Low | baseline | 103k rows / 30 games is growth, but overlap-games plateaued at 30 (enrollment stall), only 2 live books, alt-lines undiscriminated. Structurally short of what any gated analysis needs. |
| **Protocol validity** | Moderate–High | ↑ (vs project start) | The ladder + safeguards are sound and the falsification culture demonstrably works (it caught real defects and the PI's own overreaches). Raised by the new governance scaffolding (Debt/Confidence/Decision registers). Held below High: one Candidate defect open (RD-1) and **no stopping-rule threshold is yet empirically validated**. |
| **Safeguards** | Moderate | baseline | Registry exists and is used, but S-14 is stale (RD-7) and the status-coverage asymmetry means a safeguard premise drifted from reality. Needs a refresh pass. |
| **Paper 1** | High | → | Frozen; the adversarial audit verified the live panels are temporally (0/103,494 June rows), book, and data-type disjoint, so nothing collected can bear on it. |
| **Paper 2 readiness** | Low | → | Fully gated: SR-1 structurally BLOCKED (2 books, 30 games), SR-2 needs the stillborn sharp source. No path until the 3rd book / Pinnacle is resolved (ED-1, RD-2). |
| **External validity** | Very Low | baseline | Untested outside the single-month, single-sport, single-book-benchmark regime; an explicit, unaddressed limitation. |

## Reading notes

- **Confidence in the *process* is rising; confidence in the *science* is not, and should not be.**
  The governance scaffolding makes the eventual papers more defensible; it produces no scientific
  evidence. Keep these separate (they map to the daily review's Scientific Value Assessment).
- A **High** on Collector reliability and a **Low** on Paper 2 readiness are *consistent*: the machine
  is trustworthy, and the science is correctly gated behind unmet capability.
- Two synchronization rows exist on purpose: we can *understand* an instrument well (High) while the
  *gate built on it* remains of uncertain validity (Moderate). Do not collapse them.

## Discipline

Movements are logged to `GOVERNANCE_DECISION_LOG.md` with the evidence that justified them. A level
never rises on "more data collected"; it rises only when a *specific uncertainty was reduced* or a
*specific threat was eliminated or bounded*. Downgrades are as important as upgrades and must be as
prompt.
