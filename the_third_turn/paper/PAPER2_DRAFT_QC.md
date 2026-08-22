# Paper 2 — Results/Discussion draft QC

Drafted 2026-08-18 under the Outcome C mandate. Authority: `GD-21` and the committed repository
state. No new analysis was run, no new data collected, §6.6 was not amended further, and no
estimation result was attempted.

---

## 1. Substantive claims changed in this pass

| # | Change | Why |
|---|---|---|
| 1 | **Added §7 Results and §8 Discussion**; renumbered *Scope of the contribution* 7 → 9. | Results/Discussion were gated; the gate has been applied and returned Outcome C. |
| 2 | **Restored the missing `## 5. Data and institutional setting` heading.** | It had been dropped in an earlier edit, leaving §5.1–§5.4 orphaned under §4. Structural defect, found by the sweep. |
| 3 | Roadmap (§1) now names Sections 7, 8 and 9. | Previously ended at "Section 7 states the scope of the contribution", which is now Section 9. |
| 4 | §3.2 closing sentence changed from *"precisely what Section 4 must establish"* to a statement that §4 sets it up and §7 answers it in the negative. | Forward-looking language for a question the gate has now decided. |
| 5 | Title block: "DRAFT, Sections 1-6 · Results not yet written" → "DRAFT, complete · Gate applied: Outcome C — non-identification". | Accuracy. |
| 6 | Draft-status note: "complete through the Methods section" → "complete through the Discussion". | Accuracy. |

## 2. The SR-1 number, reconciled before use

The mandate flagged 572 s vs 579 s. **Neither is canonical.** The contemporaneity bound is a
*cumulative* statistic recomputed over a growing panel, and it drifts:

| Recomputation | Bound |
|---|---|
| 2026-08-10 | 579 s |
| 2026-08-11 | 572 s |
| 2026-08-17 (run log) | 565 s |
| **2026-08-18 (current, authoritative)** | **568 s** |

The paper quotes **568 s as of 2026-08-18**, states explicitly that the figure moves with the panel,
lists the four recomputations, and rests the argument on the stable fact — roughly **forty times**
the 15 s criterion — rather than on any single value. Arithmetic checks: co-capture 0.0 s + bovada
p90 537 s + fanduel p90 31 s = 568 s.

## 3. Tripwire compliance

No estimate of the pricing contrast is introduced by any route. Specifically:

- **No interval or bound** on the pricing contrast appears; §8.2 states why one cannot be constructed
  (`λ_feed` carries no bound of any kind).
- **No leadership claim.** The only two sentences in §7–§8 containing "incorporates information
  first" are explicit negations.
- **Table 5 is guarded.** The 4.7× / 1.1× / 9.5× figures are labelled a *re-pricing frequency ratio*
  and the text states in its own paragraph that this "says nothing about which book incorporates
  information first" and is reported only as the statistic on which extraction sensitivity was
  tested.
- **§7.8 declares the withholding.** Leadership-shaped statistics exist in the internal record; they
  are named as withheld, without values, and the withholding is framed as part of the result.
- **No figure was added.** Nothing in this pass encodes an unestimated quantity (GD-17).

## 4. Terminology discipline

`λ_price` / `λ_feed` / `λ_deliv` / `λ_samp` are held apart throughout. §7 opens by restating the four
and by saying that only `λ_deliv` and `λ_samp` are measured. Every occurrence of `λ_feed` in the new
text asserts that it is **unmeasured**; E-021 is described as establishing delivered-object staleness
(`λ_deliv`) and never publication latency (`λ_feed`). §7.4 separates Condition 3's three routes and
records route 1 as **not satisfied** on precisely this ground.

## 5. Consistency sweep — results

| Check | Result |
|---|---|
| Stale Outcome A/B language | Clean. Remaining "Outcome B" mentions are the §4.3 pre-registered definition and the §7.1 exclusion argument. |
| "Observation latency is common-mode" | None. |
| `λ_deliv` mislabelled as `λ_feed` | None. |
| "53/60 games" | Reported as **53 of 60 matchup groups**, under a column so labelled, with a note that `game` is a matchup string rather than a unique game identifier. |
| Both 572 s and 579 s in prose | Present only inside the explicit drift list (§7.6); the quoted figure is 568 s with its as-of date. |
| Conditions 1/2/4 described as passes | None. Table 4 marks them Failed / Unsatisfied / Failed; §8.4 restates that the amendment scopes rather than satisfies them. |
| Instruction to run a completed probe | Fixed (item 4 above). |
| Section numbering | Contiguous 1–9 after restoring the §5 heading. |
| Table numbering | Sequential 1–5 in document order. |

## 6. Qualifications carried into the draft

1. **Conditions 1, 2 and 4 remain failing.** The amendment scopes them to estimate-reporting only.
   The tripwire binds them again in original form the moment an estimate is attempted. Condition 1's
   non-invariance is deferred, not cured.
2. **GD-21 is disclosed in-manuscript as a post-evidence amendment**, with the four original
   conditions preserved byte-for-byte and a reader invited to judge the paper against the unamended
   gate.
3. **Condition 2 is an absence, not an adverse finding** — the event-clock audit was never performed.
   The draft says so rather than implying it was tried.
4. **Condition 3 is satisfied by its third route only.** Route 1 is explicitly not satisfied.
5. **The `game` key is a matchup string.** Per-game statistics pool across dates and clustered
   inference on this key clusters on matchups. Historical counts are not relabelled as unique games.
6. **Three documented continuity gaps.** §7.7 summarizes them and reports the DROP-SLICE sensitivity
   as leaving Table 5 unchanged; operational detail stays in the continuity register.
7. **Historical figures are reproducible only at their own as-of date.** The committed
   implementation reproduces all seven at the record's as-of **instant**, 2026-07-19T17:29:50Z (see
   §7.1); a date-level cutoff does not suffice. The same code on the full panel returns
   different numbers, which is a property of an append-only dataset rather than a discrepancy.
8. **Delivery-staleness figures in §5.3/§7.4 come from the frozen one-slate provenance experiment**,
   not from the cumulative panel, which now reports different medians as it grows.

## 7. The four unresolved inconsistencies — bounded QC pass, 2026-08-18

Each of the four items listed in the first draft was tested against the authoritative committed code,
the recorded as-of dates, and existing evidence. No new research, probe, estimation, data collection,
or methodological change was performed. Two are resolved, one is upgraded, one stands unresolved.

### 7.1 Agreement rate 28.2% / 28.6% / 28.8% — **RESOLVED. Authoritative value: 28.6%.**

The three figures were not competing measurements. They were the same computation under three
different cutoffs, and only one of them corresponds to the moment the record was made.

| Cutoff | Agreement | What it is |
|---|---|---|
| `ts < 2026-07-19` (date) | 28.2% | excludes all of the run day |
| `ts < 2026-07-19T17:29:50Z` (**instant**) | **28.6%** | **the sample that existed when E-017 ran** |
| `ts < 2026-07-20` (date) | 28.8% | includes all of the run day |

**Basis.** The session transcript timestamps the original E-017 execution at
`2026-07-19T17:29:50.544Z`. Cutting the panel at that instant reproduces the recorded 28.6% exactly,
together with 53/60, 4.7×, 1.1× and 9.5×. The bracketing values were artifacts of a date-level
cutoff, not evidence of an irreproducible record.

**Consequence.** `july_analyses.py::RECORD_ASOF` is now an instant rather than a date, and the
reproduction check reports **7 of 7** figures matching, up from 6 of 7. The manuscript is corrected
in three places: Table 5 (28.2% → **28.6%**, modal row 39/54 → **42 of 57**), the §7.2 reproducibility
paragraph (six of seven → **all seven**, with the date-versus-instant lesson stated), and the §6.6
determination table (28.2% → **28.6%**). The competing values are preserved in §7.2 with their
provenance, because the generalizable point is that on an append-only panel a day is not a fine
enough unit to name an as-of.

### 7.2 Gap 1 mechanism — **UPGRADED: species established; specific cause not recoverable.**

Previously recorded as "not established". Existing evidence settles what kind of failure it was.

**Established.** Runs **#40 through #56** cycled continuously on the normal ~5.5 h cadence across
07-12, 07-13, 07-14 and 07-15 with no break in the chain, while **zero checkpoint commits** landed
between 07-12 and 07-16. Gap 1 was therefore a **persistence failure, not a collection outage** —
the same species as Gap 3. The 100 MiB ceiling that caused Gap 3 is ruled out: the panel was roughly
35 MB at the time.

**Not recoverable.** The specific reason the pushes failed cannot be determined. The July checkpoint
ran every git command under `-q` inside an `&&` chain with no error surface, so the run logs — still
retrievable, and checked — record nothing about it. The blindness that caused the gap is the same
blindness that prevents diagnosing it, and no amount of re-reading the logs changes that.

Recorded in `ops/DATA_CONTINUITY.md`, which now states that **two of three gaps are persistence
failures rather than outages**, and that in both the collector reported healthy throughout.

### 7.3 Truncated-matchup effect on per-matchup interval statistics — **UNRESOLVED.**

Quantifying the distortion would require computing per-matchup interval statistics with and without
the partial observations and characterizing the difference — a new analysis, which this pass is
barred from running and which the mandate excludes.

What is established stands: the committed DROP-SLICE exclusion leaves every figure in Table 5
unchanged, and the deliberately over-aggressive DROP-MATCHUP exclusion preserves every direction
while moving magnitudes slightly. That bounds the concern in practice without measuring it. The
manuscript claims no more than that, and §7.7 states the sensitivity result rather than a null
effect.

### 7.4 §5.3 versus §7.4 — **RESOLVED. No substantive divergence; two precision gaps closed.**

Compared line by line for terminology, dates, definitions and values.

**Agree on every shared quantity:** 3,500 cache hits, 116 misses, 1,094 of 1,094 price changes,
98.6% of non-price transitions, 0.27% upper bound, 28.4% out-of-order, 3,615 of 3,616 scheduled-start
rows. The Book A / Book B assignments are consistent between the table and the prose: the cache-age
book is the one with no publication timestamp, and the edge-rewriting book is the one carrying the
event-level field.

**Two precision gaps closed**, both cases of a section leaving its denominator or sample implicit
rather than stating something different:

1. §7.4 cited "0 of 5,991 fetches" alongside per-market transition counts without noting that these
   come from two instruments with different row definitions. It now names both.
2. §7.6's 568 s bound is computed on the **cumulative** panel, while Table 3 reports a single frozen
   slate, so the bound's inputs are deliberately not the table's figures. §7.6 now says so, to
   prevent a reader from checking 30 + 549 against 568 and finding a contradiction that does not
   exist.

Remaining difference is depth only and is intentional: §5.3 describes the instrument, §7.4 applies
it to the gate.

## 8. Not done, deliberately

Final-publication formatting, figure regeneration, PDF build, and any dissemination step. The draft
is committed for review only.

---

## 9. Re-verification pass, 2026-08-22

The bounded QC instruction was issued a second time. Rather than repeat work already committed, the
prior pass was re-verified against the current repository state. **No item changed disposition and no
regression was found.** Three of the four original items remain closed; one remains open. The
manuscript was not edited in this pass.

**Reproduction, re-tested against a larger panel.** The point of an as-of *instant* is that later
collection cannot disturb a historical figure. The panel has grown from 672,035 to **745,831 rows**
since the last pass — 74k rows of new data — and `july_analyses.py --asof` still returns **7 of 7**
figures matching the record, including the 28.6% agreement rate. This is stronger evidence than the
original check, which ran when the panel had barely moved.

**§5.3 versus §7.4, re-compared.** All six shared quantities still agree (3,500 / 116 / 1,094 /
98.6% / 0.27% / 28.4%). Section-exclusive figures were enumerated and are depth differences rather
than conflicts: §5.3 alone carries the payload-age medians (115 s, 549 s) and the slate size (8,463);
§7.4 alone carries the presence bound (0.050% of 5,991 fetches) and the scheduled-start counts
(3,615/3,616 and 3,494/3,495). §7.4's "90th percentile in the high hundreds of seconds" is the
qualitative form of §5.3's 549 s, not a competing value.

**Regression sweep.** Fourteen invariants re-checked and all held: section numbering contiguous 1–9,
tables sequential 1–5, §6.6 Condition 1 verbatim, tripwire present, post-evidence disclosure present,
no "plausibly common-mode" language, 28.2% confined to the provenance note, 28.6% as the reported
value, the modal row at 42 of 57, "all seven" reproduction, the matchup-group unit stated, no bare
572/579 standing as the figure, and both precision clarifications intact.

**The SR-1 bound drifted again, as the manuscript says it does.** The series is now 579 (08-10),
572 (08-11), 565 (08-17), 568 (08-18), **567 (08-22)**. The manuscript's claim is dated — "568
seconds as of 2026-08-18" — so it remains accurate as a historical statement and was deliberately not
updated. The fifth observation strengthens rather than undermines the treatment: no single value is
canonical, and the stable fact is the order of magnitude, roughly forty times the 15 s criterion.

**Collector state, incidentally confirmed.** 365 checkpoints have landed since the shard fix on
08-18, with data current to 2026-08-22T16:40Z. The persistence failure recorded as Gap 3 has not
recurred in four days of continuous operation.

**Item 7.3 remains unresolved** and is unchanged: quantifying the truncated-matchup effect on
per-matchup interval statistics requires a new analysis, which both the original and repeated
instructions exclude.
