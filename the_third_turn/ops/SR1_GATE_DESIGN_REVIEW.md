# Gate Design Review — SR-1 (leadership analysis stopping rule)

- **Date:** 2026-07-19
- **Commissioned by:** research owner, in response to the 07-19 governance review, which
  prematurely framed the third-book blocker as "replace the book or amend the gate."
- **Mandate (verbatim intent):** *Do not recommend changing SR-1.* Instead answer, for each
  criterion, five questions — and only after answering them may any modification be considered.
- **Status:** **Review only. No criterion changed. No threshold moved.** SR-1 and
  `collection_health.py` are untouched. Any change requires a separate, evidence-backed decision
  logged to `GOVERNANCE_DECISION_LOG.md`.

## The reframing that governs this review

The question is **not** "should SR-1 require three books?" That jumps to the remedy. The question
is: **what scientific property was each criterion introduced to guarantee, and is that property
still (a) necessary and (b) unobtainable another way?** A criterion is only a proxy for a property;
we defend properties, not thresholds.

## Block-type classification (new standing distinction)

Every SR-1 criterion is now tagged by the *kind* of thing that blocks it. A gate blocked for a
**data-accumulation** reason resolves itself with time; a gate blocked for an **engineering** reason
never does. Conflating the two is what produced the premature 07-19 recommendation.

| Criterion | Current | Block type | Self-resolving? |
|---|---|---|---|
| Simultaneous live pairs ≥ 2,000 | 27,950 ✅ | Dataset | n/a (passed) |
| Median sync lag < 15 s | 0.0 s ✅ | Measurement | n/a (passed) |
| Overlap games ≥ 100 | 60 ⬜ | Scientific sampling | **Yes** — time solves it |
| Books quoting live ≥ 3 | 2 ⬜ | Engineering | **No** — waiting never fixes it |

---

## Criterion 1 — Simultaneous live pairs ≥ 2,000

1. **Why introduced?** To guarantee enough paired cross-book observations that a sync-lag statistic
   (and any later cross-book comparison) has a stable sampling distribution rather than being driven
   by a handful of coincidences.
2. **Failure mode prevented.** A cross-book number computed on tens of pairs that reverses on the
   next game-day; false precision from a tiny sample.
3. **Still relevant?** Yes — it is the dataset-size floor for any paired analysis.
4. **Achievable another way?** No substitute; it *is* the sample-size property, stated directly.
5. **Evidence to change it?** A power calculation showing the eventual paired estimator is stable at
   a different N. None exists yet; leave at 2,000. **(Passed 14× over — not the issue.)**

## Criterion 2 — Median sync lag < 15 s

1. **Why introduced?** To ensure that when we compare two books at "the same moment," they really are
   contemporaneous, so a measured lead/lag is price discovery and not clock skew.
2. **Failure mode prevented.** Attributing information leadership to a book when the "lag" is just
   forward-filling one book's stale quote against the other's fresh one.
3. **Still relevant?** Yes — and it is the criterion most entangled with *how* we measure. The
   companion `SR1_sync_lag_design_review.md` already flags the metric as a **Candidate design
   defect**: the median is quantized by the 30 s poll cadence and inflated by forward-filled stale
   quotes.
4. **Achievable another way?** Yes — potentially better. An event-aligned measure (lag between a
   book's reaction and a game-state change) would capture the same "contemporaneity" property
   without the forward-fill artifact. This is a measurement-redesign candidate, **flagged not
   revised**, pending the Book Characterization event-alignment work.
5. **Evidence to change it?** A demonstration that the event-aligned lag and the current pairwise lag
   diverge materially on the same data. Until that exists, keep the threshold; treat the metric as
   provisional. **(Reads 0.0 s today — but that number is exactly what the design review distrusts.)**

## Criterion 3 — Overlap games ≥ 100

1. **Why introduced?** To ensure leadership/efficiency conclusions rest on enough *independent games*
   — the true unit of replication — not on many correlated observations within a few games.
2. **Failure mode prevented.** Game-clustered inference: 27,950 pairs drawn from 6 games would look
   like a huge sample while being 6 independent draws. The MDE work already showed the binding floor
   is game-clustered, not snapshot-clustered.
3. **Still relevant?** Yes — this is the single most important criterion for valid inference, and the
   one whose satisfaction is genuine scientific progress rather than mere volume.
4. **Achievable another way?** No. Independent games are the replication unit; nothing substitutes
   for accumulating them. This is **scientific sampling**, and time is the only cure.
5. **Evidence to change it?** A clustered power analysis pinning the game-count MDE to a specific
   target; if 100 is too low for the effect size we care about it should *rise*, not fall. **Do not
   touch. It is behaving exactly as designed (60/100, climbing with the schedule).**

## Criterion 4 — Books quoting live ≥ 3  *(the one under scrutiny)*

1. **Why introduced?** Not for its own sake. The property it proxies is **single-book-artifact
   protection**: any efficiency claim must not be an artifact of one book's idiosyncratic pricing,
   and we need a way to detect and reject an erroneous/outlier book. Three books allow a
   *majority vote*; two books can disagree but cannot adjudicate which is wrong.
2. **Failure mode prevented.** Publishing "the live market is efficient" when the result is really
   "FanDuel's pricing engine behaves this way," with no independent check.
3. **Still relevant?** **The property is entirely relevant. The specific threshold of 3 is what is in
   question.** The failure mode it guards against is real and unaddressed.
4. **Achievable another way?** *Possibly — and this is the crux.* Two candidate substitutes for the
   third book's majority-vote function:
   - **(a) Behavioral independence.** If the two live books are shown to span the behavioral space
     (the first-pass characterization already shows FanDuel is high-frequency/tight-vig and Bovada
     is coarse/sticky — very different instruments), a two-book consensus may already be robust to
     single-book quirks.
   - **(b) An external outlier check.** A model anchor (RE24 / matchup) or a collected closing line
     can serve as the third reference for outlier rejection without a third live feed.
   Neither substitute is *established* yet. Establishing (a) is precisely the job of the **Book
   Characterization Report**; (b) depends on the forward-collected closing-line set maturing.
5. **Evidence to change it?** A completed Book Characterization showing (i) the two live books are
   sufficiently independent that their consensus is not one book in disguise, **and** (ii) a working
   outlier-detection mechanism that does not require a third live book. **Absent that evidence, the
   criterion stands unchanged.** Pinnacle being dead (ED-1) is *not* evidence that the property is
   unnecessary — it is only evidence that this particular third book is unavailable.

---

## Disposition

- **No change to any SR-1 criterion.** Criteria 1–2 pass; 3 is self-resolving scientific sampling; 4
  guards a real property whose alternative satisfaction is **not yet demonstrated**.
- **Prerequisite for revisiting Criterion 4:** the Book Characterization Report must first establish
  two-book behavioral independence and an outlier-detection substitute. Until then, "≥3 books"
  remains the guardian of single-book-artifact protection.
- **Criterion 2 remains a flagged measurement-redesign candidate** (per the sync-lag review), to be
  resolved by the same event-alignment method the characterization needs.
- The near-term binding constraint is **Criterion 3 (overlap games, 60/100)**, which requires only
  patience. The third-book question does **not** become live until Criterion 3 nears satisfaction.

## What this review deliberately did **not** do

It did not recommend replacing Pinnacle, did not propose a two-book gate, and did not lower any
number. Those are remedies; this document only established which property each criterion defends and
what evidence would license reopening it.
