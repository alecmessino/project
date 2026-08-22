# The Third Turn — Program Review, August 2026

**Prepared** 2026-08-22 · **As-of** `2026-08-22T18:22Z` · **Reviewed state:** `alecmessino/project`,
branch `claude/third-turn-service-x7m4vr`, commit `721f388`.

This is a decision memorandum, not a research output. **No frozen analysis, methodology, gate,
governance decision, or historical record was modified in producing it.** No new empirical research
was conducted; the only computations run were inventory counts and re-verification of existing
reproducibility claims, both reported as such and neither written back into any register.

Every claim below is tagged:
**[F]** established fact, verified against the repository ·
**[R]** publication/reproducibility work required ·
**[O]** optional future research ·
**[C]** commercial/product opportunity ·
**[S]** speculative, requires new validation.

---

## 1. Source-of-truth reconciliation

### 1.1 The authoritative state was not where a default checkout puts you

**[F]** The active research program lives on a **non-default branch**:
`claude/third-turn-service-x7m4vr`. The repository's default branch (`master`) contains a
`the_third_turn/` tree that is a **pre-research skeleton** — 39 files, no `ops/`, no `paper/`, no
`decisions/`, no `protocol/`, no `benchmark/`, no `release/`, none of the panels. A reviewer who
clones the repository and reads `the_third_turn/` sees essentially none of this program.

Branch reconciliation, verified:

| Ref | `the_third_turn/` contents | Verdict |
|---|---|---|
| `master` (`534321d`) | 39 files, no research dirs | **Not authoritative** — skeleton only |
| `main` (`0a27a57`) | identical skeleton | **Stale duplicate**, no Third Turn work |
| **`claude/third-turn-service-x7m4vr`** | 66 entries incl. `ops/`, `paper/`, `decisions/`, `protocol/`, `benchmark/`, `release/`, `docs/`, all panels | **AUTHORITATIVE** |
| `alecmessino/third-turn` (`82fc298`, 2026-07-29) | Paper 1 publication snapshot | **Superseded**, 24 days stale |

**[F]** The named checkpoint `b5789b8` (*"ledger + odds/state panels + health checkpoint"*,
`github-actions[bot]`, 2026-08-18T01:19Z) exists and is an ancestor of the authoritative branch. It
is one of a continuous stream of automated collector checkpoints, not a landmark commit.

**[F]** The branch is **actively advancing**. Its head moved from `9979595` to `721f388` during this
review. **91 checkpoints landed in the trailing 24 hours** (~15-minute cadence, as designed). Any
count in this memo is a snapshot with the as-of stamp above.

### 1.2 Everything the mandate listed was found

All twelve items named as "should exist somewhere" were located on the authoritative branch. Nothing
was missing and no diagnosis of absence was required.

| Item | Location | Status |
|---|---|---|
| Outcome C | `ops/GATE_DETERMINATION_66.md`, `paper/paper2.md` §7.1 | Determined 2026-08-11 |
| GD-21 | `ops/GOVERNANCE_DECISION_LOG.md` L191 | APPROVED 2026-08-11 |
| Paper 2 Results/Discussion | `paper/paper2.md` §7, §8 | Complete |
| `PAPER2_DRAFT_QC.md` | `paper/` | Drafted 08-18, re-verified 08-22 |
| §6.6 gate determination | `ops/GATE_DETERMINATION_66.md` | Complete |
| E-021 … E-026 | `ops/EVIDENCE_LEDGER.md` | All present (+ E-023a/b, E-025r) |
| Live two-book panel | `output/book_panel.part0{0..3}.jsonl` | Accumulating |
| Game-state panel | `output/game_state_panel.part0{0,1}.jsonl` | Accumulating |
| Provenance panel | `output/provenance_probe.part0{0..2}.jsonl`, `market_provenance.jsonl` | Accumulating |
| Panel sharding/reassembly | `panel_shards.py` | Operating |
| Freshness-aware watchdog | `.github/workflows/the_third_turn_watchdog.yml` | Operating |
| Repaired checkpoint workflow | `.github/workflows/the_third_turn_live.yml` | Operating |

### 1.3 Divergence that must be resolved before submission

**[R] Paper 1 has silently forked between the two repositories, and the newer copy is the one making
false claims.** `paper/paper1.md` is **not** identical across repos. The active copy is *newer* and
differs in exactly two places — both in the reproducibility/availability language, both now
inaccurate. See §3.2. The standalone repo's older wording ("materials are available from the
author") was, ironically, true; the active repo's replacement is not.

**[F]** Everything scientific is stable across the fork: `data/trajectories.jsonl` is
**byte-identical**, and every frozen Paper-1 result cache in `output/*.json` is **byte-identical**
except `health_report.json` (an operational artifact that is expected to move).

**[R] Structural fragility.** The authoritative research state, the collector, and ~284 MB of
irreplaceable data live on a feature branch that no default checkout reaches, that carries the
program's only copy of the manuscripts, and that a branch cleanup would destroy. The watchdog even
documents the split: it *must* live on the default branch (GitHub schedules cron only there) while
the collector it guards runs from the feature branch. This is a genuine single point of failure and
the highest-severity infrastructure finding in this review.

---

## 2. Executive assessment

**What has actually been built** is three distinct things, of quite different maturity and value:

1. **A finished, reproducible empirical paper** (Paper 1) whose result — no publicly observable
   baseball state variable improves on a sharp live market's own forecast — is frozen, verified, and
   defensible. Its blockers are entirely clerical.
2. **A genuinely unusual methodological paper** (Paper 2) that ran a pre-registered gate against its
   own evidence, the gate returned *non-identification*, and the paper reports that instead of
   quietly reaching for a weaker estimate. This is rarer and, in the long run, probably more
   citable than a positive result would have been.
3. **A research-governance and data-collection apparatus** — evidence ledger, assumption register,
   governance decision log, stopping rules, continuity register, postmortems, outcome-based
   watchdog, sharded append-only panels — that is the most transferable asset in the program and the
   one nobody is currently treating as an asset.

**The honest headline:** the science is in better shape than the packaging, and the packaging is in
better shape than the legal position. Two papers are substantively ready. Neither can be archived to
a DOI today, because the repository currently **relicenses third-party sportsbook data under CC BY
4.0** — data it scraped from private endpoints and licensed APIs and does not own (§4.4). That is
the single most important finding in this review, and it is a *pre-publication* blocker, not a
someday-problem.

**The second most important finding** is that the SR-1 gate is not merely blocked, it is
**structurally unreachable with this instrument**. Its contemporaneity criterion requires < 15 s;
the measured bound is **567 s** and has been re-measured five times at 579/572/565/568/567. That is
not a sample-size problem that more collection fixes — it is a property of CDN-cached public
endpoints. Continuing to collect *in order to pass SR-1* is the clearest example of work that should
stop (§10).

**Program verdict:** Papers 1 and 2 should be treated as a **completed first research program**.
The correct next move is to close them out properly — tag, archive, resolve rights, submit — not to
extend either one. The infrastructure should be demoted from "research engine" to "reusable
platform, running only against defined questions."

---

## 3. Paper 1 readiness

### Verdict: **READY AFTER EDITORIAL / REPRODUCIBILITY CLEANUP**

The empirical analysis is not reopened, and should not be. More data existing is not a reason to
disturb a deliberately frozen sample.

### 3.1 The frozen object is still the right object — **[F]**

`data/trajectories.jsonl` holds **163 records, 163 unique `game_pk`, 32,880 quote points**, first
pitch **2026-06-01 → 2026-06-23**. Paper 1's stated sample is exactly this. It is a clean,
self-contained, temporally disjoint object, and every documented collection gap (§6.4) falls in July
and August — **no gap touches Paper 1's sample**. The frozen 163-game analysis remains the correct
publication object.

### 3.2 Carried-forward audit findings, re-verified in the active repo

| Prior finding | Re-verification result |
|---|---|
| All figures regenerate pixel-identically | **Confirmed, with a caveat.** All **21/21** figures are byte-identical when regenerated by `make_figures.py` alone. |
| Output JSON regenerates byte-identically | **Confirmed.** `encompass.json`, `calibration.json`, `program_a.json` all byte-identical after re-running their generators. |
| 113 tests pass | **Confirmed.** `pytest tests/` → **113 passed** in 3.43 s. |
| Stale §6 limitation language may remain | **Confirmed, one item.** See L4 below. |
| README/dependency instructions incomplete | **Confirmed, and worse than "incomplete."** See L1, L2. |
| CITATION/repository metadata may need correction | **Confirmed.** See L3. |

### 3.3 What must be fixed before submission — **[R]**

**L1 · The replication instructions do not reproduce the committed figures.** `README.md` documents
running `make_figures.py` **then** `make_concept_figures.py`. Both scripts write the same three
filenames — `appendix_vig.png`, `concept_encompassing.png`, `concept_laboratory.png` — and the
second **overwrites** them with different images. Verified by isolation: after `make_figures.py`
alone, all three are byte-identical to the committed versions; after `make_concept_figures.py`
alone, all three differ. A referee following the published instructions gets three figures that do
not match the paper. *Fix:* drop `make_concept_figures.py` from the documented path (its unique
outputs are already produced by `make_figures.py`), or rename its outputs.

**L2 · Paper 1 §3.5 states dependencies are pinned. They are not.** The manuscript says *"dependencies
pinned in `requirements.txt`"* and *"installing the pinned requirements … regenerates every figure
and the manuscript."* `requirements.txt` contains only floor constraints (`pybaseball>=2.2`,
`pandas>=2.0`, `numpy>=1.26`, …) with **no upper bounds and no lockfile**. This is a false
reproducibility claim in the manuscript body. *Fix:* ship a real lock (`pip freeze` / `uv.lock`) and
state the interpreter version, or soften the sentence. Ship the lock — it is an hour's work and it
is what the claim promises. (Note also that the listed set is not sufficient *or* necessary as
written: reproducing the paper required `matplotlib` and `markdown`, which are in
`paper/requirements.txt`, while `streamlit` and `pybaseball` are not needed for replication at all.)

**L3 · The paper cites a release tag that does not exist.** §3.5 and *Data and code availability*
both direct readers to `https://github.com/alecmessino/third-turn` under **release tag `v1.0`**.
That repository has **zero tags and zero releases** (`git ls-remote --tags` returns nothing). Its
head commit is *messaged* "The Third Turn v1.0" but was never tagged. As published, the paper's
availability statement is unfollowable. *Fix:* actually cut and push the tag, or change the
citation.

**L4 · Stale forward-looking limitation.** §6 states that *"a temporal replication on a later,
non-overlapping month is reported separately rather than pooled into these estimates."* No such
replication exists anywhere in the program. The sentence promises a deliverable to a referee.
*Fix:* change to conditional/intended language, or delete the clause. **This is a wording
correction, not a call to run the replication** — see §10.

**L5 · Resolve the two-repo fork before either is cited.** Decide which `paper1.md` is canonical and
make the other match. Today the two repos hold different manuscripts under one title, and the
citation in the newer one points at the older one.

**L6 · Data-rights review before any archival deposit.** Blocking for the DOI step specifically.
See §4.4.

### 3.4 Does Paper 2 force any change to Paper 1? — **[F]**

**No correction. One clarification worth making, and one cross-reference.**

- **No correction is required.** Paper 1's claim is that the market's forecast *error* is not
  predictable from public state variables. Paper 2 concerns *when* information entered prices.
  Different estimand, different instrument; Paper 2 falsifies nothing in Paper 1. Paper 2 itself
  says so structurally — §5.4 is titled *"Why no comparison with the companion study is possible."*
- **One clarification is now cheap and materially strengthens the paper.** Paper 1 §6 already
  concedes that with a one-minute single-book feed *"we cannot separate genuine price-formation
  latency from feed cadence, and the uniform sub-one response ratio in the transfer function is
  consistent with either."* Paper 2 turns that hedge into a **measured** fact: delivered objects
  carry median staleness of 30 s (FanDuel) to 121 s (Bovada), with p90 up to 536 s. A one-sentence
  addition citing the companion study converts a speculative caveat into an evidenced one. This is
  a strengthening, not a retraction.
- **[R] Add the cross-reference.** Paper 1 currently gestures at "the follow-on work sketched in
  Section 7" without naming Paper 2, which now exists.

### 3.5 Does any language overstate the instrument? — **[F]** Largely no.

Paper 1 is unusually disciplined here: §6 volunteers the single-book limitation, the feed-cadence
confound, and the inability to test cross-book leadership. Two residual items:

- **[R]** The phrase *"a single Pinnacle-grade feed"* (§6) does rhetorical work that the data no
  longer support. **Pinnacle contributes 6 rows total across 1 day** in the entire live panel
  (§6.1); the Paper-1 trajectories come from The Odds API. "Pinnacle-grade" is an unverifiable
  quality assertion about a book that is effectively absent from the program's own collection.
  Recommend "a single sharp-book feed."
- **[F]** The central claim itself is correctly scoped. The abstract says *"None does"* and
  immediately bounds it with the R² and the power statement; §6 states the conditions without
  editorializing. No change needed.

---

## 4. Paper 2 readiness

### Verdict: **READY AFTER EDITORIAL / REPRODUCIBILITY CLEANUP**

Substantively the manuscript is in better shape than Paper 1. Its gap is packaging: it has **no data
availability section at all** (§5.2), which every plausible venue requires.

Outcome C and GD-21 are confirmed authoritative in the active repository and are used as such below.

### 4.1 Bounded QC status — **[F]** three of four closed, one open

Verified against `paper/PAPER2_DRAFT_QC.md` (drafted 08-18, re-verified 08-22 with no change of
disposition and no regression found).

| Item | Disposition | Classification |
|---|---|---|
| 7.1 Agreement rate 28.2 / 28.6 / 28.8 % | **RESOLVED** — authoritative **28.6%**; the three values are one computation under three cutoffs, and the as-of is an *instant* (`2026-07-19T17:29:50Z`), not a date | Closed |
| 7.2 Gap 1 mechanism | **UPGRADED** — species established (persistence failure, not outage); specific cause unrecoverable because the July checkpoint ran under `-q` with no error surface | **Disclosure-only** — correctly disclosed in `DATA_CONTINUITY.md` |
| 7.3 Truncated-matchup effect on per-matchup interval statistics | **UNRESOLVED** | **Appropriately deferred** — see below |
| 7.4 §5.3 vs §7.4 | **RESOLVED** — no substantive divergence; two precision gaps closed | Closed |

**[F] Item 7.3 is appropriately deferred, and I did not resolve it.** Quantifying the distortion
requires computing per-matchup interval statistics with and without the partial observations — a
**new bounded analysis**, which this review is barred from running. Per the mandate: *the analysis
that would be required is a paired recomputation of the per-matchup interval statistics under the
DROP-SLICE exclusion versus the full sample, reporting the distribution of per-matchup differences.*
It is **not publication-blocking**, because the concern is already bounded in practice from the
other direction: E-023b shows the committed DROP-SLICE exclusion leaves every figure in Table 5
unchanged, and the deliberately over-aggressive DROP-MATCHUP exclusion preserves every direction. The
manuscript claims exactly that and no more.

### 4.2 Required consistency checks — all pass — **[F]**

| Check | Result |
|---|---|
| §5.3 and §7.4 substantively consistent | **Pass.** All six shared quantities agree (3,500 cache hits / 116 misses / 1,094 of 1,094 price changes / 98.6% / 0.27% / 28.4% out-of-order). Section-exclusive figures are depth differences, enumerated in the QC record. |
| Contemporaneity as a *dated cumulative statistic* | **Pass.** Quoted as "**568 s as of 2026-08-18**", with the full drift series listed (579 / 572 / 565 / 568), the argument resting on the order of magnitude (~40× the 15 s criterion). A fifth observation, **567 s (08-22)**, has since been recorded in the QC log and the manuscript was *deliberately* not updated — correct, because the claim is dated. |
| 28.6% used consistently as authoritative | **Pass in the manuscript.** `paper2.md` uses 28.6% at §6.6 Table 4 and §7.2; 28.2% appears only inside the provenance note that explains the bracketing. |
| `game` / matchup terminology | **Pass.** Reported as "53 of 60 **matchup groups**", with an explicit note that `game` is a matchup string, not a unique game identifier. Independently confirmed: the panel's `game` field holds strings like `STL@CHC` that recur across dates (§6.1). |
| `λ_price` / `λ_feed` / `λ_deliv` / `λ_samp` distinct | **Pass.** §7 restates all four and states only `λ_deliv` and `λ_samp` are measured; every occurrence of `λ_feed` asserts it is unmeasured. E-021 is described as establishing `λ_deliv`, never `λ_feed`. |
| Conditions 1, 2, 4 remain non-passes scoped by GD-21 | **Pass.** Table 4 marks them Failed / Unsatisfied / Failed. §8.4 restates that GD-21 *scopes* rather than *satisfies*. The tripwire is present: if any estimate is ever reported, all three bind again in original form. |
| No implied identified pricing-leadership estimate | **Pass.** No interval or bound on the pricing contrast appears anywhere. The only two sentences containing "incorporates information first" are explicit negations. Table 5's 4.7× / 1.1× / 9.5× are labelled a *re-pricing frequency ratio* with an in-text disclaimer. §7.8 names the leadership-shaped statistics as **withheld, without values**. |

### 4.3 One disclosure-only inconsistency — **[R]**, and it must **not** be silently fixed

**[F]** `ops/GATE_DETERMINATION_66.md` (L27, L44) and the GD-21 entry in
`ops/GOVERNANCE_DECISION_LOG.md` (L193) still cite **28.2%**, while the manuscript now reports
**28.6%**.

**This is correct as it stands and I have not changed it.** Both are dated governance records of
what was determined on 2026-08-11, using the value known then; the instant-vs-date resolution came
later (E-025r, QC 7.1). Rewriting a historical determination to match a later correction is exactly
the practice this program's governance exists to prevent.

*Recommended action (disclosure, not correction):* append a dated forward-pointer footnote to
`GATE_DETERMINATION_66.md` — *"the agreement figure was subsequently resolved to 28.6% at the
record's as-of instant; see PAPER2_DRAFT_QC §7.1. The determination is unaffected"* — leaving the
original text intact. The determination genuinely is unaffected: 28.2% and 28.6% both fail the
invariance requirement, and the condition failed on the 4.7× / 1.1× / 9.5× spread, not on the
agreement rate.

### 4.4 What must be fixed before submission — **[R]**

**P2-1 · Add a Data and Code Availability section.** Paper 2 has none. Confirmed by search: the
manuscript contains no availability statement, no repository URL, and no archive reference. Every
realistic venue requires one. **This is the single largest packaging gap in the program.**

**P2-2 · Resolve the collector-branch problem before citing a repository.** Paper 2 cannot honestly
point a referee at `alecmessino/project` while its material sits on a feature branch that a default
clone does not show.

**P2-3 · Data-rights review before deposit.** Paper 2 depends far more heavily than Paper 1 on raw
third-party quote and **HTTP-header** data. See below.

**P2-4 · Reproducibility path for Paper 2's own figures.** Paper 1 has a documented (if flawed) path.
Paper 2's 12 `p2_*.png` figures regenerate from `make_paper2_figures.py` — verified byte-identical —
but this is not documented anywhere a referee would find it.

---

## 5. Publication package

### 5.1 Checklist

| Component | Paper 1 | Paper 2 | Priority |
|---|---|---|---|
| Manuscript | ✅ `paper1.md` + `.pdf` (frozen, two-repo fork to resolve) | ✅ `paper2.md` + `.pdf` (DRAFT complete) | — |
| Figures/tables | ✅ 21 figures, pixel-reproducible | ✅ 12 `p2_*` figures, byte-reproducible | — |
| Appendix | ✅ A, B, C | ✅ *Where this sits in the research program* | — |
| Supplement / visual companion | ✅ `docs/VISUAL_COMPANION.md` + `.pdf` | ⚠️ `docs/identification.html` (unversioned) | Nice-to-have |
| Data | ⚠️ `trajectories.jsonl` — **rights unresolved** | ⚠️ panels + headers — **rights unresolved** | **Must-have** |
| Code | ✅ committed, deterministic | ✅ committed | — |
| README | ⚠️ replication steps wrong (L1) | ❌ none paper-specific | **Must-have** |
| Environment / dependency lock | ❌ **unpinned**, claimed pinned (L2) | ❌ none | **Must-have** |
| Replication instructions | ⚠️ present but incorrect | ❌ absent | **Must-have** |
| CITATION metadata | ⚠️ `release/CITATION.cff` exists; `date-released` 2026-07-14 predates current manuscript | ❌ none | **Must-have** |
| Release / tag | ❌ **no tag exists in either repo** (L3) | ❌ none | **Must-have** |
| Persistent archive / DOI | ❌ "being minted" — not deposited | ❌ none | **Must-have** (gated on rights) |
| Data dictionary / schema | ✅ `benchmark/dataset/schema.md` | ⚠️ panel schemas undocumented | **Must-have** for P2 |
| Provenance / limitations statement | ✅ §6 (one stale clause) | ✅ §7.7, §8, `DATA_CONTINUITY.md` — exemplary | — |
| Cover letter / venue materials | ❌ | ❌ | Nice-to-have until venue chosen |

**Must-have before submission (both papers):** dependency lock; corrected replication instructions;
a real release tag; CITATION metadata that matches the manuscript; a data-availability statement
whose claims are true. **For Paper 2 specifically:** the availability section and panel schema docs.

**Nice-to-have:** DOI (can follow acceptance); packaged benchmark v2; HTML renderings; cover letters.

### 5.2 Recommended venues

**[O] Paper 1.** The contribution actually established is a *forecast-encompassing* result — a
public variable must beat an incumbent forecast, not merely predict the outcome — demonstrated with
a clean null and an honest power statement.
1. **International Journal of Forecasting** — best fit. Chong–Hendry encompassing is the journal's
   home ground, and it publishes well-powered nulls.
2. **Journal of Sports Economics** — strong secondary; market-efficiency framing lands directly.
3. **Journal of Quantitative Analysis in Sports** — reliable fallback, lower reach.
   *Economics Letters* is viable for a compressed version but wastes the protocol contribution.

**[O] Paper 2.** Harder to place, because a non-identification result has no natural empirical home —
and this is worth planning for rather than discovering at desk-reject.
1. **ACM Internet Measurement Conference (IMC)** or **PAM** — the non-obvious and, I think,
   strongest recommendation. Paper 2's load-bearing evidence is a *measurement* result about
   delivery infrastructure: CDN cache hit/miss behaviour, `cache-control` policy divergence between
   two operators, delivered-object staleness distributions, out-of-order delivery at 28.4%. That is
   squarely an IMC contribution, and IMC actively values negative and measurement-limit results.
2. **Journal of Economic and Social Measurement** — fits the "timestamps are observations; latency
   is an inference" thesis.
3. **Journal of Financial Markets / Journal of Futures Markets** — right audience for the
   microstructure framing, but a null identification result faces an uphill review.

**[S]** Splitting Paper 2 — the measurement paper to IMC, the identification/econometrics argument
to an economics venue — would likely place both, but it is a restructuring decision, not a
recommendation this review can validate on existing evidence.

### 5.3 Data-rights check — **the blocking finding**

**[F] Raw third-party sportsbook data is currently packaged for redistribution under a licence the
program has no authority to grant.**

`release/README.md` states: *"**Data and paper text:** Creative Commons Attribution 4.0 (CC BY
4.0)."* CC BY 4.0 grants the world an irrevocable right to redistribute, modify, and **commercially
exploit** the licensed material. The material includes:

**[F] Where the data actually comes from** (verified from `sources/` and the collectors):

| Endpoint | Nature | Redistribution posture |
|---|---|---|
| `api.the-odds-api.com/v4/...` | **Commercial licensed API** | Subscriber ToS almost certainly prohibits redistribution and relicensing |
| `www.bovada.lv/services/sports/event/coupon/...` | **Undocumented internal endpoint** | Site ToS; not a public data API |
| `sportsbook.fanduel.com` / `sbapi...` | **Undocumented internal endpoint** | Site ToS; not a public data API |
| `guest.api.arcadia.pinnacle.com` | Semi-public internal endpoint | Site ToS |
| `statsapi.mlb.com` | MLB StatsAPI | MLB terms restrict commercial use |

`RESEARCH_LOG.md` L132 is explicit about the method — *"the feeds we **scrape** (DK 403s our IP)"* —
which both confirms the collection mode and records that one operator actively blocked it.

**[F] There is no terms-of-service review anywhere in the repository.** A full-text search for
terms-of-service, licensing, or redistribution analysis returns only incidental mentions. For a
program with this quality of governance elsewhere, that is a conspicuous gap.

**Required separation before any deposit — [R]:**

| Tier | Contents | Archival posture |
|---|---|---|
| **A. Derived reproducibility artifacts** | `output/*.json` frozen caches, figures, test fixtures, `health_report.*` | **Safe.** Derived statistics, no redistributable third-party expression. Archive freely. |
| **B. Transformed / cleaned research data** | `trajectories.jsonl`, panel aggregates, `reference_results.md` | **Probably safe, review first.** Substantially transformed, but still contains verbatim quoted prices. Prefer publishing at a transformation level that supports replication without republishing the quote stream. |
| **C. Raw third-party quote & header data** | `book_panel.*`, `market_provenance.jsonl`, `provenance_probe.*`, `game_state_panel.*` | **DO NOT ARCHIVE OR RELICENSE** pending review. Verbatim third-party pricing and HTTP headers from licensed and scraped endpoints. |

**[R] Immediate actions:** (i) remove the blanket "Data: CC BY 4.0" claim and replace it with a
per-tier statement; (ii) read The Odds API subscriber terms and each book's ToS and record the
findings in a new `ops/DATA_RIGHTS.md`; (iii) obtain counsel before any Zenodo deposit that includes
Tier C; (iv) do not commercially exploit **any** tier until (ii) is complete. The current README
caveat — *"Verify the relevant terms before redistribution or commercial use"* — pushes the program's
own obligation onto downstream users while the License section grants them rights anyway. Those two
sentences contradict each other and the contradiction resolves against the program.

**[F]** Note this does **not** block *publication*. Papers can be submitted with a restricted-access
data statement. It blocks **open archival deposit and commercialization**.

---

## 6. Dataset inventory and quality

All counts computed from `721f388`, **as-of `2026-08-22T18:22Z`**. Panels are append-only and grow
~15 min; no count here is stable.

### 6.1 Live two-book panel — `book_panel.part0{0..3}.jsonl`

| Measure | Value |
|---|---|
| Rows | **745,840** |
| Span | 2026-07-03T14:37:45Z → 2026-08-22T18:07:59Z |
| Days with data | **43** of 51 calendar days |
| Pregame / live rows | 562,468 / **183,372** |
| Books | fanduel **460,209** · bovada **285,625** · pinnacle **6** |
| Distinct `game` values | 200 **matchup strings** (not unique game IDs) |
| (matchup, day) pairs | **828** |
| Polling cadence | **median 30 s** (p10 30 s, p90 31 s), both books |
| Distinct poll instants | fanduel 46,153 · bovada 32,621 |
| Quote-change events | **460,169** |
| Main vs alternate lines | 0.0% of *live* groups carry >1 posted line; **54.1% of pregame groups carry two** (E-025r) |
| Fields | `ts, game, book, line, over_odds, under_odds, live` |

**[F] Pinnacle is not in this dataset in any meaningful sense — 6 rows on 1 day, last seen ~47 days
ago.** The health report flags it `⚠STALE`. Calling this a "two-book panel" is accurate; any
description implying three books is not.

**[F] Cross-book simultaneity** (my inventory computation, ±5 s, FanDuel↔Bovada, matched within
matchup-day-state): **253,311 simultaneous pairs** across **1,139 matchup-day-state groups**, of
which **58.4%** post the same line. This is an inventory statistic for scale only. It is *not*
comparable to, and does not bear on, Paper 2's frozen 28.6% figure, which is a three-rule extraction
agreement rate at a fixed historical instant — a different quantity entirely.

### 6.2 Other panels

| Panel | Rows | Span | Days | Notes |
|---|---|---|---|---|
| `game_state_panel` | **121,652** | 07-03 → 08-22 | 43 | 182 matchups, 525 matchup-days; innings 1–12; `tto`, `pitch_count`, `starter_tier` {Ace/Mid/Back/Unknown}, `bases`, `outs`, `pitcher_id` |
| `team_total_panel` | **34,976** | 07-03 → 08-22 | 43 | **Pregame only** (0 live rows); 193 matchups, 29 teams; carries a full 0–8+ probability vector, `sd`, `skew` |
| `market_provenance` | **57,567** | 08-05 → 08-22 | 12 | 27,370 pregame / 30,197 live; `x_cache` Hit/Miss; **two distinct `cache-control` policies** (`max-age=30` vs `max-age=600, s-maxage=600`); `event_times`, `market_times`, `fetch_id` |
| `provenance_probe` | **65,927** | 08-02 → 08-22 | 15 | fanduel 32,964 / bovada 32,963; states live 21,465 / pregame 43,924 / empty 538; full payload time-field path enumeration |

**[F] Delivered-object staleness** (`recv_minus_server_s`, n = 65,927): median **1.04 s**, p95
**31.45 s**, max **66.6 s**; **32,900 observations (49.9%) exceed 30 s**; 854 exceed 60 s; **zero
negative values** (no clock-skew contamination). The current health report's per-book delivered
staleness: bovada median 121 s / p90 536 s; fanduel median 30 s / p90 31 s — the asymmetry that
makes the contemporaneity bound **567 s**.

### 6.3 Paper 1 benchmark dataset — frozen

**[F]** `data/trajectories.jsonl`: **163 records, 163 unique `game_pk`, 32,880 quote points**,
2026-06-01 → 2026-06-23, 2.6 MB. **Byte-identical across both repositories.** Fields: `game_pk`,
`fixture_id`, `start_time`, teams, and a `points[]` series of `{ts, line, over_dec, under_dec}`.
This is the only part of the program with true unique game identifiers.

### 6.4 Continuity — **[F]** three documented gaps, and the record is complete

Eight calendar days are missing: **07-13, 07-14, 08-07, 08-08, 08-09, 08-15, 08-16, 08-17.**
Independently verified: **all eight map exactly onto the three gaps in `ops/DATA_CONTINUITY.md`**,
with no undocumented outage.

| Gap | Window | Species | Detection failure |
|---|---|---|---|
| 1 | 07-12 → 07-15 (~56.6 h) | Persistence failure; specific cause unrecoverable | Self-reported health |
| 2 | 08-06 → 08-10 (101.9 h) | **True collection outage** — one HTTP 500 on the self-re-arm dispatch | No external observer |
| 3 | 08-14 → 08-17 (~79 h) | Persistence failure — `book_panel.jsonl` hit the **100 MiB** ceiling at 104,857,591 bytes, nine bytes under | Watchdog asked "is a run in progress?", which stayed *yes* |

**[F]** Only Gap 1 truncated live data (three games mid-slate); E-023b establishes those games carry
none of the July results. **No gap touches Paper 1.**

**[F] Storage & rate:** `the_third_turn/` **284 MB** (output/ 275 MB); ~91 checkpoints/24 h.
**Integrity, current health report:** rows 745,840 · malformed 0 · missing-fields 0 · duplicates 0 ·
future-ts 0 — clean.

### 6.5 Classification

**1 · Scientifically clean now**
- The frozen 163-game Paper-1 benchmark (unique IDs, disjoint, byte-stable, fully reproducible).
- Delivery/provenance measurements: cache hit/miss, `cache-control` divergence, delivered staleness,
  out-of-order rate. Self-contained facts about the *delivery path*, measured with the right
  instrument for that question.
- Panel integrity metadata (zero malformed/duplicate/future rows across 745k rows).

**2 · Useful with qualifications**
- The two-book quote panel, for **within-book** dynamics: re-pricing frequency, vig behaviour, quote
  lifecycle (OPEN 89,047 / SUSPENDED 6,949 / REMOVED 455). Qualifications: 30 s sampling floor, three
  gaps, pregame/live structural asymmetry in alternate lines.
- The game-state panel, joinable to quotes on (matchup, ts). Qualification: the join key is a
  matchup string.
- Team totals — but **pregame only**, which rules out the live analyses one would most want.

**3 · Structurally limited in interpretation**
- **Anything requiring cross-book timing or leadership.** Not a sample-size limitation: the 567 s
  contemporaneity bound is a property of CDN-cached public endpoints. Paper 2's Outcome C *is* this
  finding.
- **Anything requiring per-game identity in the live panels.** `game` is a matchup string; ARI@LAD
  on 07-11 and 07-12 are one key. Per-game statistics pool across dates and clustered inference
  clusters on matchups.
- **Three-book comparisons.** Pinnacle: 6 rows.
- **Level-based main-line metrics.** Three defensible extraction rules agree only 28.6% of the time
  and flip magnitudes 4.7× / 1.1× / 9.5% (E-017, unresolved and deferred, not cured).

### 6.6 How valuable is this, honestly?

**Not flattering it: the quote panel itself is the least valuable component.** Roughly seven weeks of
30-second MLB totals from two books is reconstructible by any competent engineer with an API key and
seven weeks of patience. Commercial vendors hold years of it at better cadence across more books.
Sample extension buys very little.

**Three things are genuinely hard to recreate, and they are not the quotes:**

1. **The provenance/delivery instrumentation.** 65,927 probes with recorded HTTP cache semantics,
   server-vs-receipt deltas, payload time-field enumeration, and out-of-order measurement.
   Essentially nobody instruments a sportsbook feed's *delivery path* as a first-class object.
   Recreating it requires knowing to ask the question — which took this program a documented
   sequence of failures to learn.
2. **The failure record.** Three postmortemed gaps, each with an established mechanism, each
   converted into a control (outcome-based watchdog, sharded persistence, error-surfaced
   checkpoints). Nine-bytes-under-100-MiB is not a bug anyone finds by reasoning; you find it by
   losing 79 hours of data. That record is worth more than the data it explains.
3. **The governance apparatus.** Evidence ledger with retraction discipline, assumption register
   with refutation status, pre-registered gate honoured against interest, as-of-instant
   reproducibility. Verified end-to-end: 113 tests pass, three JSON caches byte-identical, 21/21
   figures pixel-identical. Extremely rare in applied empirical work at any scale.

**What is expensive for others to recreate:** calendar time (seven weeks is seven weeks), the
willingness to instrument delivery rather than prices, and the discipline to record a failed gate
rather than route around it. **What is cheap for others to recreate:** the quotes.

---

## 7. Research opportunity map — **[O]** (no analysis started)

Ranked by expected value, combining scientific importance, identification quality with data in hand,
novelty, and probability of becoming a credible paper.

| # | Question | Identification | Novelty | Incremental work | P(paper) |
|---|---|---|---|---|---|
| 1 | **Delivery infrastructure as market microstructure** — the delivered object, not the price, as the unit of analysis: cache policy divergence, staleness asymmetry, out-of-order delivery | **Identified** | **High** — near-unoccupied | Low; data exists | **High** |
| 2 | **Methodology of public-endpoint measurement** — what is and is not estimable from cached public endpoints; a checklist the literature currently lacks | **Identified** (it is a methods claim) | High | Low; largely written inside Paper 2 §9 | **High** |
| 3 | **Within-book vig / inventory dynamics** — single-book, immune to the contemporaneity problem | **Identified** | Moderate | Moderate | Moderate-High |
| 4 | **Update-frequency microstructure** — hazard of re-pricing conditional on state, within book | **Identified** | Moderate | Moderate | Moderate-High |
| 5 | **Response to discrete game events** — the game-state panel gives exogenous, precisely dated arrivals | **Partially identified** — event timing clean, price timing bounded by `λ_deliv` | Moderate | Moderate | Moderate |
| 6 | **Event-dependent availability/liquidity** — SUSPENDED/REMOVED transitions around events (6,949 / 455 observed) | **Partially identified** | **High** — genuinely under-studied | Moderate | Moderate |
| 7 | **Pregame→live transition** — the alternate-line structure collapses from 54.1% to 0.0% at the boundary; a real structural break | **Identified** for structure; **partial** for pricing | Moderate | Low | Moderate |
| 8 | **Stale-object / reordering behaviour** — 28.4% out-of-order, 49.9% of probes >30 s stale | **Identified** | High | Low | Moderate |
| 9 | **Price-path calibration** — do live paths behave like martingales under the book's own measure | **Partially identified** | Moderate | Moderate | Moderate |
| 10 | **Market disagreement / dispersion** — *level* disagreement, deliberately not *timing* | **Partially identified** — level-based metrics inherit the E-017 extraction problem | Moderate | Moderate | Low-Moderate |
| 11 | **Paper 1 replication on a later month** | **Identified** — the July/August panels support it | Low (that is the point) | Low-Moderate | Moderate (as a note, not a paper) |
| 12 | **Market robustness around shocks** | **Requires new instrumentation** — no shock sample | High if achieved | High | Low |
| 13 | **Cross-book leadership / pricing contrast** | **NOT identified** — Outcome C; requires an instrument this class cannot provide | — | Very high | **Effectively zero** without new instrumentation |

**The shape of this table is the finding.** Everything identified with data in hand is a
*within-book* or *delivery-path* question. Everything blocked is *cross-book timing*. The program's
comparative advantage is the axis it discovered by accident — delivery — not the axis it set out to
measure.

---

## 8. Commercial and monetization map — **[C]**, with heavy skepticism

**Precondition applying to every row: nothing here may be pursued until §5.3's rights review is
complete.** Several rows are dead on arrival if The Odds API's terms prohibit derivative commercial
use, which is the normal case.

| # | Opportunity | Customer | Problem solved | Differentiation | Extra requirements | Model | Defensibility | Principal risk | Viability |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Third Turn Protocol as a validation standard** | Quant teams, sports-analytics firms, forecasting groups | "Does my signal beat the incumbent forecast?" — most teams test prediction, not incremental information | Domain-general, published, benchmark-backed; **wholly owned IP** | Docs, worked examples outside baseball | Open method + paid audits/workshops | Moderate — reputational, not legal | Methods rarely monetize directly | **Now** |
| 2 | **Signal-validation audit service** | Betting syndicates, small funds, analytics vendors | Independent adjudication that a claimed edge survives conditioning | The governance apparatus *is* the product; almost nobody can show a refuted-assumption register | Engagement templates, liability terms | Fixed-fee per audit | Moderate — trust-based | Doesn't scale; founder-bound | **Now** |
| 3 | **Feed-quality / delivery monitoring** | Sportsbooks, data vendors, latency-sensitive bettors | "Is my feed telling me what I think, and how stale is the object I acted on?" | **Nobody else instruments this.** Directly productizes `provenance_probe` | Multi-book generalization, alerting, SLA | SaaS subscription | **Strongest in the list** — method + hard-won know-how | Buyers may not know they have the problem | **Modest additional work** |
| 4 | **Research/intelligence reports on market microstructure** | Media, data publishers, industry analysts | Credible, citable analysis of how betting markets actually behave | Reproducibility standard far above industry norm | Editorial cadence | Subscription / commissioned | Weak — content | Effort-intensive, low margin | **Modest additional work** |
| 5 | **Benchmark Dataset licensing** | Academics, ML groups | A ready evaluation set with incumbent forecast + outcome | First mover for encompassing-style evaluation | **Rights clearance (blocking)** | Free academic / paid commercial | Weak | **Likely unlicensable** — Tier C | **Blocked on rights** |
| 6 | **Historical odds data product** | Bettors, vendors, researchers | Historical two-book quote access | **None.** Commodity; vendors have more, longer, cheaper | Rights clearance | Subscription | **None** | Redistribution almost certainly prohibited | **Do not pursue** |
| 7 | **Live signal / betting product** | Bettors | Profitable edge | **The program's own Paper 1 result argues against it** | Everything | Subscription / stake | None | Paper 1 found no public variable beats the market | **Do not pursue** |
| 8 | **Collection-infrastructure consulting** | Any team running long-horizon automated collection | Silent-failure-proof pipelines | Three postmortemed silent failures and the controls that fixed them | Packaging | Consulting / retainer | Moderate | Small market | **Modest additional work** |
| 9 | **Prediction-market / microstructure academic collaboration** | Academic groups | Access to instrumented delivery data | Unique instrument | Data-sharing agreement within Tier A/B | Co-authorship, grants | Moderate | Slow; non-cash | **Long term** |

**[C] The honest read.** The commercially defensible assets are **the method (#1, #2), the delivery
instrumentation (#3), and the operational know-how (#8)** — all of which the program *owns
outright*. Everything that depends on **redistributing collected quotes (#5, #6) is legally
exposed and commercially undifferentiated**, and #7 is contradicted by the program's own published
finding. Row **#3 is the single most interesting commercial idea in this program** and is the one
nobody has framed as a product.

**[S]** #3's premise — that sportsbooks and vendors would pay to learn their delivered objects are
minutes stale — is untested and is the assumption to falsify first, before any engineering.

**Flagged: do not commercialize until rights are confirmed** — #5, #6, and any use of `book_panel`,
`market_provenance`, `provenance_probe`, or `game_state_panel` beyond internal research.

---

## 9. Ranked strategic priorities

### By academic/research value
1. Close out Paper 2 packaging and submit (measurement venue).
2. Close out Paper 1 cleanup and submit.
3. Delivery-infrastructure-as-microstructure paper (opportunity #1).
4. Public-endpoint measurement methodology (#2).
5. Within-book vig/update dynamics (#3, #4).

### By commercial/economic value
1. Rights review — unblocks or kills everything else.
2. Feed-quality/delivery monitoring concept validation (#3).
3. Protocol as validation standard + audit service (#1, #2).
4. Infrastructure consulting (#8).
5. Academic collaboration (#9).

### By combined strategic value

| # | Path | Upside | Effort | Principal dependency | Fastest falsification / abandonment |
|---|---|---|---|---|---|
| 1 | **Resolve source-of-truth + branch architecture** | Prevents catastrophic loss of the entire program | ~1 day | None | N/A — do it regardless |
| 2 | **Data-rights review** (`ops/DATA_RIGHTS.md`) | Unblocks archival + all commercial paths | 2–5 days | Reading ToS; possibly counsel | Odds API terms prohibit derivative redistribution → Tier C is internal-only, permanently |
| 3 | **Paper 1 cleanup + tag + submit** | Converts finished work into a publication | 3–5 days | #1, #2 (DOI only) | Desk reject at IJF → reposition to JSE |
| 4 | **Paper 2 packaging + submit** | Publishes the more novel contribution | 5–8 days | #1, #2 | Two measurement-venue rejects → the identification framing needs a co-author |
| 5 | **Delivery-microstructure paper** | New line on the program's real advantage | 3–4 weeks | Data in hand | Literature search finds it already done |
| 6 | **Feed-quality monitoring validation** | Only credible business | 2–3 weeks | #2; customer access | 5–10 discovery calls; no one recognizes the problem → stop |
| 7 | **Protocol standardization** | Durable, owned IP | 2–4 weeks | None | No external adoption in 6 months → keep as a paper artifact only |
| 8 | **Within-book microstructure paper** | Solid second-tier output | 4–6 weeks | Data in hand | Effects vanish under the 30 s sampling floor |
| 9 | **Paper 1 temporal replication** | Closes the §6 promise | 1–2 weeks | Data in hand | Only worth it *if* a referee asks |

---

## 10. Stop-doing list

**[F] 1 · Stop collecting in order to pass SR-1.** The gate stands at 67% and two criteria are
structurally unreachable: contemporaneity requires < 15 s against a measured 567 s (five
re-measurements: 579/572/565/568/567), and "3 books live" requires Pinnacle, which has produced 6
rows in 50 days. Outcome C already established that no amount of this data identifies the pricing
contrast. **More collection cannot move either criterion.** Continuing to run the collector *for
this purpose* is the single clearest waste in the program.

**2 · Stop all cross-book leadership/timing analysis.** Unidentifiable by the program's own
pre-registered gate. Any such analysis also trips the GD-21 tripwire and would re-bind Conditions 1,
2 and 4 in their original form.

**3 · Stop level-based main-line metrics** until the E-017 extraction problem is resolved. Three
defensible rules agree 28.6% of the time and flip magnitudes 4.7× / 1.1× / 9.5×. Any level-based
result is a statement about the extraction rule.

**4 · Stop low-value sample extension.** The marginal week of 30 s two-book MLB totals adds almost
nothing to any identified question. Every question in §7 that the data can answer is already
answerable.

**5 · Stop further infrastructure hardening absent a failure.** The collector has survived three
postmortemed failure classes and 91 clean checkpoints/day. It is past the knee of the curve. The
*one* exception is the branch-architecture fix (§9 #1), which is not hardening but a genuine single
point of failure.

**6 · Stop treating Paper 1's frozen sample as reopenable.** More data existing is not a reason to
disturb it. The replication belongs in a separate note, if anywhere.

**7 · Do not build a betting product.** Paper 1's own result is the argument against it.

**8 · Watch for scope drift and p-hacking risk.** The program has been unusually disciplined —
E-025's reproduction failure was recorded before it was resolved, and GD-21 explicitly refused the
self-serving move of declaring Conditions 1/2/4 satisfied. The risk is not past behaviour; it is
that an unbounded dataset plus an open-ended mandate makes rule-selection-after-seeing-results
easy. **Every future analysis should be pre-registered against a specific hypothesis before it is
run**, as §6.5 already requires.

**9 · Do not collect anything further without a named research question or product hypothesis.**

---

## 11. Recommended operating state

### Answers to the specific questions

**Should the collector keep running?** **Yes, but at reduced intent and with a defined stop
condition.** Not for SR-1 (unreachable), and not for sample size (marginal value ~0). Keep it
running for exactly two purposes: (a) the **provenance/delivery panel**, which feeds the program's
most promising research and commercial line and is genuinely accumulating novel measurements; and
(b) **operational continuity** of a system already built and paid for. **Set an explicit review date
— end of the MLB regular season — and default to stopping the quote panels then** unless a named
question requires them.

**What should be frozen and versioned now?** Paper 1 (already frozen — now *tag* it); Paper 2 at
submission; Benchmark Dataset v1; Protocol v1.0; the panels as a dated snapshot for each paper's
citation; and the entire `ops/` governance record, which should be treated as a citable artifact in
its own right.

**What should stay live?** The provenance probe, the watchdog, the health report, and the checkpoint
pipeline.

**What future data should be collected only against a hypothesis?** Everything not in the two
purposes above — in particular any new book, market type, sport, or field. **Add a rule: no new
collection stream without a written hypothesis or product requirement recorded in `ops/` first.**

**Should Papers 1 and 2 be a completed first research program?** **Yes, unambiguously.** They form
a coherent pair — *information in prices* and *formation of prices* — with the second honestly
reporting that its estimand is not identifiable. That is a complete arc. Extending either dilutes
it; the third paper should start from the delivery-infrastructure question, which is a new program.

**What should become a reusable platform?** The **Third Turn Protocol** (method), the **governance
apparatus** (ledger/register/gate/stopping-rule pattern), and the **outcome-based collection
harness** (sharded append-only panels, freshness watchdog, error-surfaced checkpoints). All three are
domain-general and wholly owned.

**What has credible business potential?** In order: **feed-quality/delivery monitoring** (#3 — the
real one), **signal-validation audits** (#2), **infrastructure consulting** (#8). Everything
depending on redistributing collected quotes is legally exposed and commercially undifferentiated.

**Repository architecture — should `alecmessino/third-turn` remain the clean publication repo?**
**Yes in principle, but the current implementation is broken and must change.** Today: the
publication repo is 24 days stale, has **no tags** despite being cited by tag, and holds a
*different* `paper1.md` than the active repo; meanwhile the active source of truth is a feature
branch invisible to a default clone.

Recommended target state:

| Repo | Role | Required change |
|---|---|---|
| `alecmessino/project` | Active research source of truth | **Merge `claude/third-turn-service-x7m4vr` into the default branch, or make it the default.** The collector keeps checkpointing to its own branch; the research state must not live only there. |
| `alecmessino/third-turn` | Clean publication/release repo | Sync to the final manuscripts; **cut and push real `v1.0` / `v2.0` tags**; carry only Tier A/B data; make CITATION and DOI match. |

That two-repo split is sound — it keeps 275 MB of accumulating panels out of the artifact readers
cite. It just has to actually be *executed*, which it currently is not.

### The one-line recommendation

**Treat Third Turn as a completed two-paper program with a valuable by-product.** Spend the next
month closing it out properly — rights, tags, archives, submissions — rather than extending it. Then
decide, on evidence rather than momentum, whether the delivery-infrastructure line is worth starting
as a genuinely new program.

---

## 12. Roadmap

### Next 1 week — highest expected return: **de-risk and unblock**

1. **Fix the branch architecture** (½ day). Merge/promote the authoritative branch. This protects
   284 MB of irreplaceable data and the program's only copy of both manuscripts. *Highest
   return-per-hour in this document.*
2. **Write `ops/DATA_RIGHTS.md`** (2 days). Read The Odds API terms and each book's ToS; classify
   Tier A/B/C; correct the CC BY 4.0 over-claim in `release/README.md`. Blocks every archival and
   commercial path.
3. **Fix Paper 1's three false claims** (1 day): the pinning claim (L2), the release-tag citation
   (L3), the replication order (L1). Ship a dependency lock.
4. **Cut and push a real `v1.0` tag.** (~1 hour, and it makes the paper's own citation true.)

*One week's highest return is entirely non-research: the program's biggest risks are a branch
deletion, a licence over-claim, and three sentences that a referee can falsify in five minutes.*

### Next 1 month — highest expected return: **convert finished work into publications**

5. Resolve the two-repo Paper 1 fork; sync the publication repo (week 2).
6. **Add Paper 2's Data & Code Availability section** + panel schema docs + reproducibility path
   (week 2). Largest packaging gap in the program.
7. Add the Paper 1 ↔ Paper 2 cross-reference and the strengthened §6 feed-cadence limitation; fix
   the stale replication clause and "Pinnacle-grade" (week 2).
8. Append the dated forward-pointer note to `GATE_DETERMINATION_66.md` — **without altering the
   determination** (week 2).
9. **Submit Paper 1** to *International Journal of Forecasting* (week 3).
10. **Submit Paper 2** to *IMC*/*PAM* or an economic-measurement venue (week 4).
11. Deposit Tier A (+ Tier B if cleared) to Zenodo; mint the DOI (week 4, gated on #2).

*One month's highest return is submission. Both papers are substantively done; every additional week
unsubmitted is pure decay.*

### Next 6 months — highest expected return: **one new research line, one business test, then stop or commit**

12. **Months 1–2:** manage review cycles. Run the Paper 1 temporal replication *only* if a referee
    asks.
13. **Months 2–4:** write the **delivery-infrastructure-as-microstructure** paper (§7 #1) from data
    already held. The program's genuine comparative advantage, and the natural start of a second
    program.
14. **Months 2–3, in parallel:** run 5–10 customer-discovery conversations for **feed-quality
    monitoring** (#3). Cheap, fast, and decisive. *Falsification: if sportsbooks and vendors do not
    recognize delivered-object staleness as a problem they would pay to see, drop the commercial
    thread entirely and keep Third Turn as a research program.*
15. **Month 4:** end-of-season collector review. Default to **stopping the quote panels**; keep the
    provenance probe only if #13 or #14 justifies it.
16. **Months 5–6:** commit to whichever of the two lines survived, or close the program cleanly with
    two published papers, a citable protocol, an archived benchmark, and a governance record worth
    more than either paper.

**Where an additional unit of work has the highest expected return, stated plainly:**
- **1 week → the branch fix and the rights review.** Not research. Risk reduction and unblocking.
- **1 month → submitting both papers.** The work is done; only the packaging is not.
- **6 months → the delivery-infrastructure paper, plus a cheap falsification test of the one real
  business idea.** Everything else is the endless-hobby failure mode this review exists to prevent.

---

*Prepared 2026-08-22 against `721f388`. No frozen analysis, gate, governance decision, or historical
record was modified. Item 7.3 of the Paper 2 QC remains open by design; the analysis that would close
it is specified in §4.1 and was deliberately not run.*
