# Design review — SR-1's median sync-lag threshold

- **Date:** 2026-07-06
- **Question posed:** Is SR-1's `median sync lag < 15 s` sub-gate theoretically achievable with the current feeds? If not, propose a replacement criterion grounded in observable data properties.
- **Status:** Analysis complete. **The 15 s threshold is unchanged** (per instruction, not lowered). This document proposes a replacement for the owner's decision; no code threshold was modified.

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

## Is < 15 s achievable? No, for two independent reasons.

1. **Poll cadence.** The collector samples every ~30 s. A wall-clock median under 15 s would
   require sub-15 s polling *and* both books refreshing live sub-15 s. At a 30 s cadence, only
   same-poll pairs clear 15 s; adjacent-poll pairs are already ~30 s. The target sits below the
   instrument's own resolution.
2. **Second-book sparsity.** The lag is dominated by the *sparser* live feed. bovada is dense
   (every poll); fanduel is bursty (p75 gap 122 s, tail to 97 min); pinnacle emits no live quotes
   at all. We do not control how often an external book refreshes its in-play line, so no amount of
   "keep collecting" pulls the median toward 15 s. The threshold is aspirational: it silently
   assumes two books that both refresh live faster than 15 s, which this feed mix does not provide.

The 15 s number appears to have been imported as a generic "near-real-time" figure without
reference to the collector's poll cadence or the books' observed refresh behavior.

## The metric also mismeasures what leadership analysis needs

Leadership analysis needs **moments where two books are both genuinely, freshly live close together
in time** so that who-moved-first is attributable. The forward-fill lag instead penalizes healthy
asymmetric coverage: whenever one book is denser than the other, the metric reports a large lag
even though the collector captured every co-live moment perfectly. Proof: restricting to pairs
where **both** quotes are fresh (each ≤ one poll interval old) yields a median lag of **0 s** across
~100 pairs / 14 games. When both books are actually live, the collector already captures them
simultaneously. There is no synchronization defect to gate on; the 640 s figure is an artifact.

| Freshness window `W` | Fresh pairs | Games | Median lag |
|---|---|---|---|
| 45 s | 101 | 14 | 0 s |
| 60 s | 103 | 14 | 0 s |
| 90 s | 132 | 14 | 0 s |

## Proposed replacement criterion (observable, achievable-in-principle)

Replace the single unreachable wall-clock target with two criteria built from properties the
collector actually controls:

1. **Fresh co-observation lag.** Among pairs where *both* books' live quotes are no older than one
   poll interval (`W`, currently ~45 s), require the median lag `< W`. This measures real
   synchronization, is not gamed by the sparse book's stale quotes, and the instrument can meet it
   whenever two books are co-live (today: median 0 s). It scales automatically with the poll
   cadence rather than fixing an external number.
2. **Fresh co-observation volume.** Require at least *N* fresh co-observed pairs across at least
   *K* games, where a pair counts only if both quotes are ≤ `W` old. This gates on the genuinely
   scarce resource, the density of attributable co-live moments, which grows observably as more
   games are collected. (`N`, `K` to be set from a leadership-estimator power analysis; the current
   ~100 pairs / 14 games is the present standing.)

Also redefine the existing "simultaneous live quote pairs" sub-gate to use the same freshness gate,
so the count and the lag stop disagreeing.

**If a true sub-15 s lag is ever a hard requirement**, it is an engineering decision with two
prerequisites, not a matter of patience: (i) drop the poll cadence toward ~10 s, and (ii) secure a
second book that refreshes its in-play line at that cadence (or add a third dense feed to replace
silent pinnacle). Both are feasible; neither is the current default.

## Recommendation

Do not lower the 15 s number in place; **replace** the sub-gate with the freshness-gated lag +
volume pair above, which are observable, achievable when two books are co-live, and aligned with
what leadership analysis actually consumes. This is a proposal for the owner's decision; SR-1 in
`protocol/stopping_rules.md` and the health tool remain unchanged until that decision is made.
