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
   implementation reproduces six of seven at 2026-07-19; the same code on the full panel returns
   different numbers, which is a property of an append-only dataset rather than a discrepancy.
8. **Delivery-staleness figures in §5.3/§7.4 come from the frozen one-slate provenance experiment**,
   not from the cumulative panel, which now reports different medians as it grows.

## 7. Unresolved inconsistencies

1. **`E-017` agreement rate: 28.2% (regenerated) vs 28.6% (recorded).** The neighbouring cutoff
   returns 28.8%, bracketing the recorded value, so the original evidently ran mid-day on a partial
   2026-07-19. The draft uses **28.2%**, the figure the committed code produces. Not resolvable
   without the original run's exact timestamp; recorded rather than reconciled.
2. **Gap 1 (2026-07-12 → 07-15) has no established mechanism.** It predates the run-log review. The
   draft does not speculate.
3. **Truncated-matchup effect on per-matchup interval statistics is unquantified.** DROP-SLICE leaves
   the reported figures unchanged, which bounds the concern in practice but does not measure it.
4. **§5.3 and §7.4 both describe the provenance measurements**, at different depths. Intentional —
   one is data description, the other is the gate determination — but a future editing pass should
   confirm they have not drifted apart.

## 8. Not done, deliberately

Final-publication formatting, figure regeneration, PDF build, and any dissemination step. The draft
is committed for review only.
