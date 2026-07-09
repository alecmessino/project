# Engineering Debt & Known Unknowns

The platform's running list of (a) things that are wrong or fragile and owe a fix, (b) health/gate
metrics whose value depends on the implementation rather than the world, and (c) honest unanswered
questions. Distinct from the decisions log (which records *settled* choices) and the safeguard
registry (which records *rules*): this file records *open* engineering and epistemic obligations.

Ranked by risk-to-the-research-platform, not by ease.

## Engineering Debt

| ID | Item | Risk | Status | Action |
|---|---|---|---|---|
| **ED-1** | **Pinnacle is stillborn and the root cause is unknown.** 6 pregame rows in a single 07-06 06:25 Z burst, **0 live quotes ever**. | **Top.** Unknown infrastructure is dangerous infrastructure: it silently blocks SR-1 (books 2/3) *and* SR-2 (the sole sharp implied-PMF source), and we cannot say whether it is a config, auth, subscription, endpoint, or parsing failure. Nothing here is "maturing." | Open | Diagnose the pinnacle adapter path end-to-end (auth/subscription/endpoint/parse) with a controlled fetch. Do **not** assume collecting longer helps (EP-5). Until diagnosed, treat every gate that depends on a 3rd book or a sharp source as blocked by an unexplained fault, not a data lag. |
| **ED-2** | **SR-1 sync-lag sub-gate is implementation-dependent** (quantized to {0} ∪ [30 s, ∞) by the 30 s poll interval). | High — a future PASS would certify collector co-capture, not market contemporaneity. | Open (Candidate design defect; **not** revised) | Flag only, per owner directive. Bring the volume/fraction redesign (`SR1_sync_lag_design_review.md`) back with a power analysis before any threshold changes. Leave SR-1 and the health tool untouched. |
| **ED-3** | **`book_panel` interleaves alternate total lines** (≈95% of (game,book,ts) groups carry 2–3 lines) with **no main-vs-alt discriminator**. | High — corrupts naive pair-counting (softens the one passing SR-1 sub-gate) and any future microstructure / SR-3 work. | Open | Add a `line_type` / main-line flag at collection or a documented derivation. Until then, verify whether the SR-1 pairs count double-counts alt-line fan-out (unresolved from the 07-09 audit). |
| **ED-4** | **Integrity gate validates only `ts/game/book/line`.** 61 fanduel rows (36 live) carry null odds and pass; odds/status/line-type are unchecked. | Medium — "integrity clean" reads stronger than it is; the null-odds rows sit inside the exact instants SR-1 pair analysis would consume. | Open | Either widen the required-field set or surface an explicit "clean under this field definition; N rows null-odds" line in the health report so the claim is not over-read. |
| **ED-5** | **`marketStatus` is single-book** — bovada emits a status value on 0 of 27,988 rows, so any SUSPENDED/REMOVED staleness filter silently no-ops for one live book. Safeguard **S-14 registry entry is stale** (says "field not yet collected"; it has been collected since 2026-07-05). | Medium | Open | Refresh the S-14 registry entry to reflect that `status` is now collected but single-book. Do not trust a suspension filter for microstructure work until bovada status coverage exists (or the filter is documented as fanduel-only). |
| **ED-6** | **Two residual re-arm failure modes remain uncovered** — a hard runner loss skips even the `always()` step, and the ≥60-min crash-loop guard leaves no successor if a cancellation lands under 60 min. | Medium — a full out-of-band watchdog needs default-branch cron/`workflow_run`, which is outside this feature branch. | Open (owner decision) | Recommend accepting the `always()` mitigation for now; revisit a default-branch watchdog only if a hard-loss outage recurs (documented in the 07-06 postmortem). |
| **ED-7** | **Cosmetic metric inconsistency** — `collection_health.py` reports SR-1 as 61% (`render()` truncates) vs 62% (`trend()` rounds) from the same 0.617. | Low | Open | One-line fix: use a single rounding convention across `render()`/`summary()`/`update_history()`. |

## Implementation-dependent health metrics (redesign candidates — flag, do not silently revise)

Per the owner's 07-09 directive: a metric whose *value* is set by our implementation rather than by
the world is a **candidate for redesign**, surfaced here, not quietly re-specified. Each is a
hypothesis about a better metric, awaiting a decision.

| Metric | Implementation dependence | Consequence | Debt link |
|---|---|---|---|
| SR-1 median sync lag | Quantized by `poll_interval_seconds = 30` | Only value below 15 s is 0; a PASS certifies co-capture, not synchronization | ED-2 |
| SR-1 "simultaneous live pairs" | Depends on an **undefined forward-fill staleness horizon** and on **alt-line multiplicity** | Count may include stale legs and/or alt-line fan-out; margin over threshold is soft | ED-3 |
| Fix-verification "marketStatus populated" | True on fanduel only; bovada emits none | Half-true; suspension filtering is single-book | ED-5 |
| Integrity "clean" | Narrow required-field set (`ts/game/book/line`) | Excludes odds/status/line-type from validation | ED-4 |

## Known Unknowns

Not problems — unanswered questions a mature program tracks so it does not mistake silence for an
answer. None is on the analysis critical path today; each is a candidate research/engineering question.

| ID | Question | Why it matters | How it would resolve |
|---|---|---|---|
| **KU-1** | **Why is Pinnacle stillborn?** | It is the sharp source SR-2 needs and the 3rd book SR-1 needs; the failure is currently unexplained. | ED-1 diagnosis. |
| **KU-2** | **Are alternate totals economically useful** (vs just present in the feed)? | They are ~95% of `book_panel` rows; if useful they are an asset, if not they are noise to filter. | A scoped SR-3-adjacent study *after* SR-3 instrumentation — not now. |
| **KU-3** | **Do three books materially improve leadership estimation**, or would two dense books suffice? | Determines whether the SR-1 "≥3 books" gate is load-bearing or an over-conservative design assumption. | A power/identifiability analysis once a real 3rd live source exists. |
| **KU-4** | **Is SR-2 (distribution dynamics) actually the better paper** than the SR-1 leadership path? | The two gated research directions compete for the same scarce sharp-source data; picking wrong wastes months. | A framing/feasibility comparison once the sharp PMF stream exists (blocked on KU-1/ED-1). |

## Discipline

Items leave this file in one direction only: an ED closes when the fix ships *and* a prediction or
check confirms it (log the confirmation in the Engineering Prediction Log); a KU closes when it is
answered with evidence, and its answer is recorded — never assumed.
