# Design review — SR-1's median sync-lag threshold

- **Date:** 2026-07-06 (updated 2026-07-09 to correct overreaching language)
- **Question posed:** Is SR-1's `median sync lag < 15 s` sub-gate behaving as intended with the current feeds, and if not, what redesign would the observable data support?
- **Classification:** **Candidate design defect** (an architectural hypothesis, not an established fact). The *observed* behavior (poll-cadence quantization; second-book dependence) is fact; the conclusion that the gate is "mis-specified" is a Candidate for the owner to adjudicate.
- **Status:** Proposal only. **No threshold changed**; SR-1 and the health tool are untouched. Flagged as a redesign Candidate in the Engineering Debt register, per the owner's directive that implementation-dependent metrics be flagged, not silently revised.

## What the metric currently measures

`collection_health.py` (and `microstructure_probe.py`) define a *simultaneous live pair* by
forward-filling each book's most recent live quote to every observation time `t`, and the sync lag
is the gap between the two books' quote timestamps at `t`. A fresh quote from a dense book is
therefore paired against the **most recent live quote of the other book, however stale**.

## Evidence (from the banked 47,832-row book panel)

Measured directly from `output/book_panel.jsonl`:

| Quantity | Value |
|---|---|
| Poll cadence (any-quote inter-arrival, median) | **~30 s**, both books |
| bovada live-quote inter-arrival | median **31 s**, p75 31 s (dense, every poll) |
| fanduel live-quote inter-arrival | median 31 s, **p75 122 s** (bursty, long gaps) |
| pinnacle live quotes | **0** |
| Sync lag over 1,066 pairs | min 0, p25 273 s, **median 640 s**, p75 1,093 s, max 5,822 s |
| Fraction of pairs with lag < 15 s | **7.3 %** |
| Fraction with lag < 30 s / 60 s / 120 s | 7.3 % / 9.5 % / 14.6 % |

The 7.3 % of pairs under 15 s are the moments both books refreshed in the **same poll cycle**. The
rest of the distribution is inflated by bovada continuing to tick every 30 s while fanduel sits in
a live-coverage gap (up to 97 minutes), each bovada tick pairing against the same stale fanduel
quote.

## Classification: Candidate design defect (observed behavior; the architectural conclusion is NOT established)

> Language discipline (owner directive, 2026-07-09): distinguish an *observed property* of the
> implementation from an *architectural conclusion* about the design. The first is fact; the second
> is a hypothesis. This section does the former plainly and marks the latter as a **Candidate**.

Two properties of the sub-gate are **observed facts**:

1. **Poll-cadence quantization [observed].** The collector samples every ~30 s
   (`poll_interval_seconds = 30`), so paired sync lags take values in {0} ∪ [30 s, ∞): nothing falls
   in (0, 30). A median below 15 s is therefore attainable only at exactly median = 0 (both books
   captured in the same poll cycle), never at an intermediate wall-clock value.
2. **Second-book dependence [observed].** The lag is dominated by the sparser live feed. When one
   book is bursty (fanduel: p75 gap 122 s at the 07-06 snapshot, tail to 97 min) the forward-fill
   pairs its stale quote against the dense book and inflates the median; when both feeds densify,
   the median collapses toward the 0-rung. Confirmed 07-09: fanduel densified from ~1k to ~10k live
   quotes and the cumulative median fell 640 s → 30 s (logged in the Engineering Prediction Log).

What these facts do **not** establish is the stronger, architectural claim that the gate is
*mis-specified* or *measures the wrong thing*. That is a **Candidate design defect**, stated here as
a hypothesis for the owner to adjudicate, not as a conclusion:

> **Candidate:** a PASS at median = 0 certifies collector *co-capture at 30 s granularity*, which
> may be a weaker property than the sub-15 s market *contemporaneity* S-11 intends. Whether that gap
> is material for leadership estimation is an architectural judgment, not a measurement.

The earlier framing "< 15 s is unachievable / the gate can never clear" is **too strong and was
falsified** by the 07-09 audit: median = 0 is a legal, reachable value and the within-day median has
already reached it on recent days. The open question is *what a PASS would certify*, not *whether a
PASS is possible*.

## Evidence for the Candidate: forward-fill lag penalizes healthy asymmetric coverage

When one book is denser than the other, the forward-fill lag reports a large value even though the
collector captured every genuinely co-live moment. Restricting to pairs where **both** quotes are
fresh (each ≤ one poll interval old) yields a median lag of **0 s**:

| Freshness window `W` | Fresh pairs | Games | Median lag |
|---|---|---|---|
| 45 s | 101 | 14 | 0 s |
| 60 s | 103 | 14 | 0 s |
| 90 s | 132 | 14 | 0 s |

This shows the *inflated* lag is a forward-fill artifact of sparse-vs-dense coverage. It is **not**,
on its own, proof that the co-capture a PASS certifies is inadequate for leadership work; that
remains the open Candidate above.

## Candidate replacement criterion (proposal only — do not revise the gate yet)

If the owner accepts the Candidate defect, the redesign should be built from properties the
collector controls, and should **not** be the naive fresh-pair lag: the 07-09 audit showed a
"median fresh-pair lag < W" test is **near-tautological** (it reads 0 s whenever any co-live pair
exists), so it certifies almost nothing. The substantive criterion is **volume / fraction**, not lag:

1. **Fresh co-observation fraction/volume.** Require at least *N* fresh co-observed pairs (both quotes
   ≤ one poll interval old) across at least *K* games, and/or a minimum *fraction* of live pair-instants
   that are fresh. This gates on the genuinely scarce resource, the density of attributable co-live
   moments, which grows observably as games accrue. `N`, `K`, and the fraction are to be set from a
   leadership-estimator power analysis, not asserted.
2. **Retire the wall-clock lag threshold** (or keep it only as a diagnostic, never a pass/fail gate),
   since on a 30 s-quantized instrument any value in (0, 30] yields the identical partition.

**If a true sub-15 s lag is ever a hard requirement**, it is an engineering decision with two
prerequisites, not a matter of patience: drop the poll cadence toward ~10 s, and secure a second
book that refreshes its in-play line at that cadence. Both are feasible; neither is the current default.

## Recommendation

**Do not revise the gate now.** Per the owner's 07-09 direction, an implementation-dependent metric
is *flagged as a redesign Candidate*, not silently re-specified. Actions: (1) record the sync-lag
sub-gate as a Candidate design defect in the Engineering Debt register and the stopping-rule
classification; (2) leave SR-1 in `protocol/stopping_rules.md` and the health tool **unchanged**;
(3) bring the volume/fraction redesign back for an explicit decision, backed by a power analysis,
before any threshold changes. SR-1 remains BLOCKED and correct in the meantime.
