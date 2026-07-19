# Assumption Register

Every research program quietly accumulates assumptions; unexamined, they are where invalid inference
hides. This register makes them explicit. Each assumption carries an owner, supporting and
contradicting evidence (as Evidence-Ledger IDs), a confidence label, a status, and a next-review
trigger. This becomes load-bearing when Paper 2 is written: an assumption that is `Weak` or
`Challenged` and feeds a gated analysis is a threat to inference and must appear in Research Debt.

**Confidence:** `Weak` · `Moderate` · `Strong`. **Status:** `Open` · `Supported` · `Under review` ·
`Challenged` · `Refuted`. Owner is the PI unless delegated.

| ID | Assumption | Supporting | Contradicting | Confidence | Status | Next review |
|---|---|---|---|---|---|---|
| **A-01** | Live quotes represent **executable** prices | — | E-012 (arbs concentrated in suspended/near-settled/status-unverifiable legs); E-008 (can't confirm "open" on bovada) | Weak | Open | Before any leadership/arb analysis |
| **A-02** | Feed timestamps **preserve event ordering** | E-004 (0 future-ts; monotonic within poll) | Cadence drift (mean 33.6 s, 226 gaps ≥180 s); no exchange clock | Moderate | Supported | On any ordering-sensitive analysis |
| **A-03** | 30 s **poll cadence is sufficient** for leadership inference | — | E-006 (sub-15 s contemporaneity unresolvable at 30 s; sync gate quantized) | Weak | Challenged / Under review | With the RD-1 sync-gate redesign |
| **A-04** | **Two-book overlap identifies** lead-lag | — | S-10/S-11 (one-night artifact); under-identification with 2 books | Weak | Challenged | Tied to RD-2 / third-book decision |
| **A-05** | The **main balanced line is separable** from alternate lines | — | E-010 (no main-vs-alt discriminator; ~95% multi-line groups) | Weak | Challenged | With the ED-3 discriminator work |
| **A-06** | Suspension filtering is **symmetric across books** | — | E-008 (bovada emits no status; FanDuel-only) | Weak | Refuted (as currently implemented) | Before any suspension-filtered comparison |
| **A-07** | A **sharp single-book incumbent forecast is available live** (for SR-2 / real-line work) | — | E-007 (Pinnacle stillborn) | Weak | Refuted (currently) | With ED-1 diagnosis |
| **A-08** | Static **RE24 / run values transfer** across parks and seasons (Paper 1 transfer benchmark) | Paper 1 uses published values with a stated limitation | Park/temp/wind residuals noted in Paper 1 | Moderate | Supported (with stated limitation) | If Paper 1 is revisited |
| **A-09** | Results **generalize** beyond June 2026 / MLB / single-book benchmark (external validity) | — | Untested by construction | Weak | Open | Post Paper-2 data accrual |
| **A-10** | The live books are **behaviorally interchangeable** as pricing instruments (a consensus can weight them symmetrically) | — | BOOK_CHARACTERIZATION v0.1 / RD-8 (FanDuel 31 s cadence & 0.36 pp vig IQR vs Bovada 8 min & 1.80 pp — different instrument classes) | Weak | Refuted (provisional) | With Book Characterization v0.2 (event-aligned) |

## How this register is used

- An assumption that is `Weak`/`Challenged`/`Refuted` **and** feeds a gated analysis is escalated to
  `RESEARCH_DEBT.md` (A-03↔RD-1, A-04↔RD-2, A-05↔RD-3, A-06↔RD-4, A-07↔RD-2).
- New evidence that bears on an assumption is logged in `EVIDENCE_LEDGER.md` and cited in the
  Supporting/Contradicting columns; the confidence label moves only with that evidence.
- Before Paper 2 analysis is authorized, every assumption it relies on must be at least `Supported`,
  or its `Weak`/`Challenged` status must be explicitly bounded in the analysis plan.

## Discipline

An assumption does not become `Supported` by being convenient or long-held. It becomes `Supported`
only when supporting evidence outweighs contradicting evidence on the record. Refuted assumptions are
kept (not deleted) so the audit trail shows what was believed and why it changed.
