# Gate Determination — Paper 2 §6.6

**Date:** 2026-08-11 · **Authority:** GD-20 · **Basis:** the evidence in this repository as of
commit `12a00d7`, and the authoritative implementation in `july_analyses.py`.

This memorandum applies §6.6 **literally**. The pre-registered conditions, thresholds, decision
rules and analysis plan are not modified, softened, or reinterpreted anywhere below. Where the
evidence is absent rather than adverse, that is stated as absence.

> The gate decides the paper. The paper does not reinterpret the gate.

---

## Condition 1 — A well-defined main line

> *"An extraction rule fixed in code and tested, with a demonstration that the primary statistic is
> materially invariant to reasonable alternatives."*

**Status: FAILED.**

The condition has three separable requirements. Two are met; the third is not.

| Requirement | Status | Evidence |
|---|---|---|
| Extraction rule **fixed in code** | **Met** | `july_analyses.py::pick()` implements balanced-odds, modal-anchor and median rules in committed, version-controlled code. |
| **Tested** | **Met** | Reproduces 6 of 7 recorded ledger figures exactly at the record's as-of date (E-025r). |
| Primary statistic **materially invariant** to reasonable alternatives | **NOT met** | E-017, regenerated: 4.7× / 1.1× / 9.5×; three-rule agreement 28.2%. |

The reproducibility question (E-025) is **resolved and is not the reason this condition fails**. The
rule is fixed in code and it reproduces the record. The condition fails on the substantive
requirement, and it fails because the required demonstration was performed and returned the opposite
of what the condition requires.

Regenerated at the record's as-of date (`< 2026-07-19`), the primary statistic under three
reasonable extraction rules:

| Rule | FanDuel > Bovada | Median ratio | Vig IQR (bovada / fanduel) |
|---|---|---|---|
| balanced-odds | 53/60 games | **4.7×** | 0.05 / 0.31 pp |
| modal anchor | 39/54 games | **1.1×** | 0.05 / 0.31 pp |
| median line | 53/58 games | **9.5×** | 2.04 / 1.11 pp |

The magnitude spans a factor of **8.6** across rules that are each defensible, and the three rules
select the same quote in only **28.2%** of groups. Under the modal anchor the two books re-price at
close to the same rate; under the median rule one re-prices nearly ten times as often. These are not
the same empirical claim.

The **direction** is invariant — FanDuel ≥ Bovada under all three rules. The pre-registered language
does not ask for directional invariance. It asks that *the primary statistic* be *materially
invariant*. An 8.6× spread in the headline magnitude is material on any reading, and reading the
condition as satisfied by sign-stability alone would be reinterpreting it after seeing the result.

**Determination: Condition 1 is not satisfied.**

---

## Condition 2 — Clock comparability

> *"An audit establishing that event and quote timestamps are comparable, with residual skew
> quantified."*

**Status: NOT SATISFIED — the required audit has never been performed.**

This is an absence, not an adverse finding, and the distinction matters for what happens next.

Searched and not found: no clock audit in `protocol/`, no event-timestamp entry in the Evidence
Ledger, no committed script performing this comparison.

What exists is **adjacent but different**. E-020 and E-021 quantify HTTP `Date` skew, CDN cache age,
and delivered-object staleness. Every one of those measurements concerns **how a quote reaches us**.
None concerns **whether the event clock and the quote clock are on the same footing**. Game events
are timestamped by ESPN's scoreboard, a third source that neither probe touched.

**Precisely what is missing:** a comparison of ESPN event timestamps against book quote timestamps,
with residual skew quantified. No new exploratory analysis is proposed here; this records the gap.

**Determination: Condition 2 is not satisfied.**

---

## Condition 3 — Transport separability resolved in one direction

> *"Either an independent measurement of book-specific feed latency, or a defended argument that it
> is common-mode, or a documented demonstration that neither is achievable with this class of
> instrument. The third outcome satisfies this condition and converts the paper into a pure
> identification result."*

**Status: SATISFIED — via the third route only.**

The condition offers three routes. Their statuses differ, and conflating them would overstate what
the instrument achieved.

**Route 1 — an independent measurement of book-specific feed latency: NOT satisfied.**
This is the determination most at risk of being overstated, so it is stated exactly. E-021 measured
`λ_deliv`, the staleness of the copy delivered to us — visible because the distribution network
describes itself in its own headers. Condition 3 names `λ_feed`, the delay between a bookmaker's
internal revision and its publication at origin. **These are different quantities.** `λ_feed`
remains entirely unmeasured, and no instrument in this study addresses it. Measuring a term adjacent
to the one the condition names does not satisfy the condition.

**Route 2 — a defended argument that it is common-mode: REFUTED.**
Not merely unachieved — measured false. FanDuel's delivered staleness is a CDN cache age accounted
for exactly, to the second, on 3,500 cache hits and absent on the 116 misses; Bovada rewrites the
same header at the edge and reports payload ages to a 90th percentile of 549 s. The two books do not
share a convention, let alone a magnitude (E-020, E-021).

**Route 3 — a documented demonstration that neither is achievable with this class of instrument:
SATISFIED.**
E-021 answered four questions fixed in advance (GD-19) under the coverage-based stopping rule fixed
before any probe data existed (GD-18). Neither book exposes a usable publication clock: one exposes
none (0/5,991 fetches; 95% upper bound 0.050%), the other an event-level heartbeat that moves on
98.6% of transitions without a price change and whose transitions arrive **28.4% out of order**
because the delivery network serves objects of differing age. A clock that cannot order its own
values cannot date a revision. The absence is quantified rather than asserted, which is what makes
it a demonstration.

**Scope, stated honestly:** the demonstration covers two public retail sportsbook endpoints. That is
what "this class of instrument" denotes here, and the claim is not extended beyond it.

**Determination: Condition 3 is satisfied, by the route that §6.6 itself says "converts the paper
into a pure identification result."**

---

## Condition 4 — Robustness support

> *"A third live source, or an explicit outlier-detection procedure that does not require one."*

**Status: FAILED.** Neither disjunct holds.

| Disjunct | Status | Evidence |
|---|---|---|
| A third live source | Not met | `books quoting live 2/3`. Pinnacle stillborn — 6 pregame rows, 0 live quotes ever (E-007). |
| An explicit outlier-detection procedure | Not met | No such procedure exists in committed code. The term appears only in prose (design brief, governance log, manuscript), never as an implementation. |

**Determination: Condition 4 is not satisfied.**

---

## Gate summary

| Condition | Status |
|---|---|
| 1. Well-defined main line | **FAILED** — invariance demonstration returned non-invariance |
| 2. Clock comparability | **NOT SATISFIED** — audit never performed |
| 3. Transport separability | **SATISFIED** — third route |
| 4. Robustness support | **FAILED** — neither disjunct |

**1 of 4 conditions holds. §6.6 requires all four. The Results section remains unwritten.**

---

## Pre-registered outcome determination

§4.3 admits exactly three outcomes. Each is evaluated against its own stated antecedent.

**Outcome A — excluded, on two independent grounds.** A requires that "feed latency is shown to be
common-mode or is independently measured" — it is neither (Condition 3, routes 1 and 2). A also
requires that "the extraction rule is shown not to drive the result" — it demonstrably does drive
it (Condition 1). Either failure alone excludes A.

**Outcome B — antecedent partially matches; deliverable is not producible.** B's second disjunct,
"the result is directionally stable but magnitude-sensitive to the extraction rule," is *literally
true* of E-017: direction holds under all three rules, magnitude spans 4.7×/1.1×/9.5×. That is the
strongest case for B and it must be taken seriously rather than waved past.

It fails on B's own stated deliverable. B says: *"The reportable object is then an interval within
which the pricing contrast must lie."* Constructing that interval requires bounding the transport
terms. `λ_deliv` is bounded — measured directly. **`λ_feed` is not bounded at all.** No upper bound
of any kind on bookmaker publication latency exists in this repository or is obtainable from these
endpoints. Without a bound on `λ_feed`, the observed contrast cannot be narrowed to any interval
containing the pricing contrast.

The directional stability that B's second disjunct describes is stability of the **observed**
contrast `Δλ`. It is not a bound on the **pricing** contrast, and treating it as one would assume
away exactly the decomposition this paper exists to confront.

**Outcome C — both antecedent clauses hold.** C requires that "no external measurement of feed
latency is obtainable from public endpoints" (established, E-021, under the GD-18 stopping rule) and
that "no argument establishes common-mode behaviour" (refuted by measurement, E-020/E-021). The
three worlds of Figure 4 therefore remain observationally equivalent no matter how much data
accumulates, because the term that distinguishes them is unmeasurable on this instrument.

### **Determination: Outcome C.**

This follows from the pre-registered text, not from preference. It is worth recording explicitly
that C is the outcome the design flagged as *least* likely to be reported and most demanding to
defend — it is not the convenient branch.

---

## What Outcome C permits, and what remains blocked

**Permitted by the outcome.** C's reportable object is "a demonstration, not a guess: a proof that
timestamp data from public sportsbook endpoints cannot separate market behaviour from publishing
infrastructure, together with a specification of the additional instrumentation that would be
required." The evidence for that demonstration is complete and in the repository.

**Blocked by the gate, as first issued.** §6.6 stated that the Results section "remains unwritten
until all four of the following hold." Three do not hold, so on the original wording Paper 2's
Results and Discussion remained unwritten.

**Under Amendment 1 (GD-21, recorded below):** the Outcome C demonstration may be written, because
Conditions 1, 2 and 4 are scoped to estimate-reporting and Condition 3 — the only condition bearing
on identification — is satisfied. **No numerical estimate of the pricing contrast may be reported**,
and the three failing conditions bind again the moment one is attempted.

### A structural tension in the pre-registration — RESOLVED by Amendment 1 (2026-08-11)

Conditions 1, 2 and 4 exist to support a **reported estimate**. Under Outcome C no estimate will be
reported: the reportable object is a demonstration of non-identification, which does not depend on
extraction-rule invariance, on a third book, or on an outlier procedure. Applying §6.6 literally
therefore left the Results section gated on conditions that guard a deliverable the outcome has
already excluded.

The pre-registration did not anticipate that Condition 3's third route could be satisfied while 1, 2
and 4 fail. This memorandum, as first issued, declined to resolve that tension and referred it to the
principal investigator as a governance decision.

**That decision was taken on 2026-08-11 (GD-21): Conditions 1, 2 and 4 are scoped to
estimate-reporting only.** The amendment is recorded in Paper 2 §6.6 as "Amendment 1", below the
four original conditions, which are preserved byte-for-byte. Its material terms:

- The amendment **postdates the evidence** and says so in the manuscript. A reader may evaluate the
  paper against the original four conditions, under which Results would remain unwritten.
- Conditions 1, 2 and 4 are **not waived, not weakened, and not deemed satisfied.** Their
  determinations above stand unchanged and are reported as failing throughout.
- Condition 3 is untouched in wording and scope. No threshold, decision rule, or analysis plan is
  altered.
- **Tripwire:** if any estimate of the pricing contrast is reported — in this paper, a successor, a
  talk, or a repository artifact — Conditions 1, 2 and 4 bind again in their original form and must
  be satisfied first. Their failure is deferred, not spent.

**Effect on this determination:** none of the condition statuses change. What changes is what the
gate permits: the Outcome C demonstration may now be written, while no numerical estimate of the
pricing contrast may be.

---

## Item flagged separately: the `game` identifier

`game` in `book_panel.jsonl` is a **matchup string, not a unique game identifier**. A series between
the same two teams pools across dates (ARI@LAD appears on both 07-11 and 07-12).

**Effect on §6.6 conditions: none.** Extraction operates within a single `(game, book, ts)` poll
group, so pooling across dates does not change which quote any rule selects; Condition 1's failure
is unaffected either way. Conditions 2, 3 and 4 do not key on game identity.

**Effect on interpretation and reporting of E-016–E-018: real.** "53/60 games" counts *matchups*,
not games. Per-game statistics pool observations across distinct contests, and any game-clustered
inference computed on this key clusters on matchups rather than games — which understates the number
of independent units. **No historical result is silently repaired.** This is recorded as a reporting
qualification on E-016/E-017/E-018.

---

## Data-continuity evidence

E-022 (August outage, 101.9 h) and E-023/E-023a/E-023b (July gap, 56.6 h) are **data-continuity
evidence and are not grounds to alter the research design.** The authoritative sensitivity result
(E-023b) governs: under the precise DROP-SLICE exclusion the July conclusions are unchanged — 4.7×,
53/60 games, vig IQRs 0.05/0.31 pp, and E-018's 36%/18% all hold — and no gate moves.

---

## Separately: SR-1 is a different gate

SR-1 governs the leadership analysis, not §6.6. It stands at **2 of 4, BLOCKED**: pairs 80,416/2,000
✅, overlap games 145/100 ✅, contemporaneity bound **572 s / 15 s ❌**, books quoting live 2/3 ❌.
The contemporaneity criterion fails for the same underlying reason Condition 3 resolves as it does:
delivered staleness is book-specific and large (E-021, E-024).

---

## What is missing, stated exactly

Per the instruction to name gaps rather than invent tests:

1. **Condition 2** requires an audit comparing ESPN event timestamps to book quote timestamps with
   residual skew quantified. It has never been performed. Nothing else is missing for it.
2. **Condition 1** cannot be satisfied by further measurement of the current statistic. It requires
   either a primary statistic that *is* invariant across reasonable extraction rules, or acceptance
   that the condition fails.
3. **Condition 4** requires a third live source or a committed outlier-detection procedure. Neither
   exists.
4. **`λ_feed`** has no bound of any kind. This is what excludes Outcome B, and no public-endpoint
   measurement in this study can supply it.

---

## Forward pointer — appended 2026-08-22

**The determination above is unchanged and is not amended by this note.** It is retained as the
dated record of what was determined on 2026-08-11 from the evidence then available.

Two figures in the text above were subsequently refined. Both are recorded here so a reader
comparing this memorandum against the manuscript does not mistake drift for contradiction:

1. **The three-rule agreement rate, given above as 28.2%.** It was later established (E-025r; QC
   §7.1, `paper/PAPER2_DRAFT_QC.md`) that the as-of for the E-017 record is an *instant*,
   `2026-07-19T17:29:50Z`, not a date. Cutting the panel at that instant reproduces the recorded
   **28.6%** exactly, along with all six other figures; the 28.2% and 28.8% values are the same
   computation under date-level cutoffs on either side of it. **28.6%** is the authoritative value
   and is what the manuscript reports.

   **This does not disturb Condition 1.** The condition failed on the non-invariance of the primary
   statistic across extraction rules — 4.7× / 1.1× / 9.5× — not on the agreement rate, and it fails
   identically at 28.2%, 28.6% or 28.8%.

2. **The SR-1 contemporaneity bound, given above as 572 s.** It is a cumulative statistic recomputed
   over a growing panel and drifts: 579 s (08-10), 572 s (08-11), 565 s (08-17), 568 s (08-18),
   567 s (08-22). No single value is canonical. SR-1's status is unaffected — every observation is
   roughly forty times the 15 s criterion, and SR-1 remains **BLOCKED**.

Nothing in Outcome C, GD-21, the four conditions, or the disposition of any condition is altered by
this note.
