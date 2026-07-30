# Figure Provenance

*Standing mandate (2026-07-26): every public dollar or percent figure shipped on the site has a row
here, classified DERIVED / ASSUMED / UNSOURCED. No new public figure ships without one. This is the
launch-audit companion to the pre-existing **[`docs/Evidence_Register.md`](docs/Evidence_Register.md)**
— see "Relationship to the Evidence Register" below before assuming this is a second, competing system.*

## Taxonomy

- **DERIVED** — a specific, named function/module in this repo computes the figure, live or from a
  test-guarded frozen cache, and a test would catch drift or a hand-edit.
- **ASSUMED** — illustrative/hypothetical; honestly labeled as such at or near the figure (a fictional
  household, a stated formula, a cited external study/law), but not itself a tested code path. Hand-typed
  numbers are ASSUMED, not UNSOURCED, *only if* the illustrative/hypothetical label is actually present.
- **UNSOURCED** — no code path derives it **and** it is not clearly labeled illustrative/hypothetical, or
  the label exists but gestures at authority it doesn't have (e.g. citing "published research" with no
  citation). Becomes a Phase 2 work item; a fiduciary's site should not carry these indefinitely.

## Relationship to the Evidence Register

`docs/Evidence_Register.md` already covers the equities/leakage/tax-lab figure family in depth (12
entries, each with methodology, owner, review cadence, and named test guard) using its own three-tier
model (Level 1 Authority / Level 2 Internal modeling / Level 3 Opinion). It predates the 2026 site
redesign (last verified 2026-07-05) and its protocol is sound — this file does not replace it.

This file exists because the 2026 redesign shipped several new pages (`hub.html`'s rewritten register
sample, `tax-atlas.html`, `the-practice.html`, `the-record.html`, `coordination.html`'s worked example,
`opportunity-register.html`, `decision-register.html`, the `case-*.html` pages) whose figures are **not**
in the Evidence Register, plus this audit found the Register itself has gone stale in one place (entry 3,
noted below). Where a figure is already a Register entry, this file cross-references it by number instead
of duplicating its write-up. **Phase 2: consolidate into one register** rather than maintaining two —
tracked in `OPERATIONS.md`.

## Corrections to this mandate's own starting premises

This audit was launched on the explicit premise that two figures were UNSOURCED. Verification (an
independent research pass, a second adversarial verification pass per figure, and my own direct
reproduction) found one of those premises does not hold, and surfaced a further correction to the
initial pass's classifications:

- **"$14,800/yr register rows... hardcoded HTML samples"** — confirmed hardcoded, but *not* unlabeled:
  `hub.html` carries an adjacent disclosure ("Illustrative sample, a fictional household...") directly
  under the table. Classified **ASSUMED**, not UNSOURCED — see row below for the caveat (the specific
  household/assumption set behind the number still isn't stated, which is real Phase 2 work).
- **"3.7–4.7% is a hardcoded table in leakage.py with no derivation in-repo"** — this is incorrect as
  stated. `scripts/tax_alpha.py::all_state_alpha()` computes it from the committed 30-year proxy-spliced
  cache (`tests/data/matrix_history.json`), and `tests/test_leakage_alpha_lineage.py::
  test_state_alpha_matches_tax_alpha_recompute` re-derives the table from that cache and asserts it still
  matches — confirmed passing (not skipped) by two independent runs. It is also Evidence Register entry
  2. Classified **DERIVED** (frozen-cache, test-guarded — not live-recomputed per build, which is a real
  but different caveat from "no derivation").
- **A follow-up input to this audit additionally claimed "$6,200 gifting" and "$5,200 reserve" register
  rows exist on `hub.html` needing the same treatment.** Verified: neither string appears anywhere in the
  current repo. These numbers belong to an *earlier* version of `hub.html` (referenced in this session's
  own git history — a diff hunk that no longer applied because Phase 1 had already replaced that markup).
  The current register table has exactly five rows; only three carry dollar figures ($14,800, $4,100,
  $11,300 — all below). Noted here so the discrepancy isn't silently dropped.
- The initial research pass classified the `taxlab.html` $410k/$90k/$320k exhibit chart and the
  homepage's "$320,000" hero line as DERIVED "via `leakage.py` linkage." Independent verification
  disagreed and reclassified both **ASSUMED**: the personalization *rescale* uses real `STATE_ALPHA` data,
  but the unscaled baseline numbers are static, untested HTML/SVG. See the "known drift risk" note below
  — this is a real and distinct figure from the tested `hub.html` pillar stat that happens to share the
  same underlying numbers.

## Figures

| # | Figure | Appears | Derivation | Status |
|---|---|---|---|---|
| 1 | +3.7–4.7%/yr Structural Alpha (headline band, four representative jurisdictions) | `leakage.html` hero, `taxlab.html`, homepage, all 51 state pages | `scripts/tax_alpha.py::all_state_alpha()` over `tests/data/matrix_history.json`; `src/drift/leakage.py::STATE_ALPHA`. Guard: `tests/test_leakage_alpha_lineage.py` (4 tests, real-cache recompute passes). = Evidence Register #2 | **DERIVED** |
| 2 | Pretax before/after CAGR 9.4% → 9.1% (the honest inversion) | `leakage.html` headline, homepage | `src/drift/leakage.py::build_leakage()["headline"]`, same cache lineage as #1. Guard: `tests/test_drift_leakage.py`, `tests/test_drift_hub.py`. = Evidence Register #4 | **DERIVED** |
| 3 | After-tax CAGR ranges: before 0.4–2.7%, after 5.1–6.3% | `leakage.html` before/after cards | `src/drift/leakage.py::build_leakage()`, min/max of the four displayed states from `STATE_ALPHA`. Guard: `tests/test_leakage_alpha_lineage.py`, `tests/test_drift_leakage.py` | **DERIVED** |
| 4 | $90,000 → $410,000 kept of $1M in gains, 30y (canonical pillar stat) | Homepage "value adds" pillar 3 | `src/drift/leakage.py` `keep_pct` × $10,000, assembled in `src/drift/hub.py::build_hub()`. Guard: `tests/test_drift_hub.py` asserts the exact `"${lo:,.0f} → ${hi:,.0f}"` string against a live recompute. = Evidence Register #3 | **DERIVED** |
| 5 | Full jurisdiction range +3.3–4.8%/yr (WA low, MA/NYC high) | `leakage.html` "Read it honestly" guardrail (added in this launch, see below) | Same `STATE_ALPHA` table as #1, true min/max across all 54 jurisdictions rather than the 4 displayed. Guard: new `tests/test_leakage_alpha_lineage.py::test_read_it_honestly_guardrail_cites_the_true_full_range` | **DERIVED** |
| 6 | Per-state "$Xk/$1M" Coordination Opportunity bars | `statemap.html` | `src/drift/statemap.py::build_statemap()` → `coordination_opportunity_per_m()` in `src/drift/leakage.py`, off `STATE_ALPHA`. Guard: `tests/test_drift_statemap.py` (structure + no-fabrication), plus the same lineage recompute test | **DERIVED** |
| 7 | CAGR figures, strategy vs. buy-and-hold (train/test) | `tearsheet.html`, `thesis.html` | `src/drift/analytics.py::cagr()`, live market data via `feed/resolve.py`, built by `tearsheet.py`/`thesis.py`. Guard: `tests/test_drift_tearsheet.py`, `tests/test_drift_thesis.py` | **DERIVED** |
| 8 | Out-of-sample Sharpe 0.65 ≈ in-sample 0.648 | Homepage pillar 2, tearsheet | Walk-forward split, `scripts/tilt_optimize.py` lineage. = Evidence Register #5 | **DERIVED** |
| 9 | Live ledger figures (+41.4%, Sharpe 1.37 vs 1.23/1.10, −16% max DD) | Homepage appendix, dashboard, ledger | Append-only `docs/ledger.json`, nightly cron. = Evidence Register #6 | **DERIVED** |
| 10 | Equities case-study metrics (six backtests) | `report.html` (equities case studies) | `src/drift/case_studies.py::build_report()` / `render_report()`/`export_report()` over the committed 18-ETF cache. Guard: `tests/test_drift_case_studies.py`, `tests/test_drift_backtest.py`. = Evidence Register #11 | **DERIVED** |
| 11 | Equities dashboard numbers | `index.html` (equities) | `src/drift/exhibit.py` (ledger-derived operational dashboard, distinct module from #10). Guard: `tests/test_drift_exhibit.py`, `tests/test_blotter_source.py` | **DERIVED** |
| 12 | $400 million moved (founder's DFA story) | `about.html` | Attested professional narrative, not a Driftwood performance claim. = Evidence Register #1 | **DERIVED*** (narrative attestation, not a model — no automated guard by design) |
| 13 | State tax dataset (rates, estate cliffs, QSBS, munis, step-up) | `statemap.html`, 51 state pages, `leakage.html` state table, `taxlab.html` | `src/drift/statemap.py`, `src/drift/statepage.py`, compiled from public 2026 state law. Guard: `tests/test_drift_statemap.py`. = Evidence Register #8 | **DERIVED** (facts) — annual review required per Register protocol |
| 14 | Tax Lab default household + assumptions ($2.5M split, 7% growth, turnover, ER) | `taxlab.html` | `src/drift/tax*.py`, editable inputs, sensitivity-banded outputs. = Evidence Register #9 | **ASSUMED** (labeled, editable, sensitivity-ranged — the intended design) |
| 15 | Estate figures (IL cliff, 2026 federal exemption, HB2601) | `taxlab.html` estate view | Enacted 2026 law + HB2601 as introduced, explicitly labeled proposed. = Evidence Register #10 | **ASSUMED** (accurate law citation) |
| 16 | Concentration tool scores (22 strategies × 6 axes) | `concentration.html` | `src/drift/concentration.py`, one analyst's labeled orientation, not a performance claim. = Evidence Register #12 | **ASSUMED** (explicitly qualitative) |
| 17 | ~~$14,800/yr — Asset location (register sample row)~~ | **RETIRED 2026-07-29** — removed from the site | The Plate III register replaced its "Potential" dollar column with "Next review" (a date). The figure no longer ships, so it needs no provenance. A review date proves the matter is *carried*, which was the actual claim; the dollar was an un-derived estimate standing in for it. | **RETIRED** (resolved by removal, not by derivation) |
| 18 | ~~$4,100/yr — Roth conversion window (register sample row)~~ | **RETIRED 2026-07-29** | Same removal as #17. | **RETIRED** |
| 19 | ~~$11,300 kept — Loss carryforward (register sample row, "Resolved")~~ | **RETIRED 2026-07-29** | Same removal as #17. The resolved row now reads "Closed Mar 2026" instead of a captured amount, which is the stronger and cheaper claim. | **RETIRED** |
| 20 | ~0.6–1.5%/yr "vs. an ordinary broadly-diversified index... consistent with published tax-alpha research" | `leakage.html` guardrail text + index card (`atc_low:6.18, atc_high:6.89`) | No function, no test, no citation. The `atc_low`/`atc_high` literals live only in `src/drift/leakage.py::build_leakage()`; "published tax-alpha research" names no source | **UNSOURCED** — invokes external authority with no citation. **Phase 2: either cite the specific research this figure is "consistent with," or drop the appeal-to-research framing and label it purely illustrative** |
| 21 | Exhibit I waterfall: $80,000 → ($21,000) tax → ($2,000) fees → ($25,000) inflation → $32,000 | `leakage.html` "Where a gross return goes" | Hardcoded, but arithmetically self-consistent with the stated 8.0%/20bps/2.5% CPI assumptions shown in the same exhibit; labeled "Modeled, illustrative, not a forecast or advice" | **ASSUMED** |
| 22 | Tax Lab 30y chart baseline: $410,000 / $90,000 / $320,000 (`taxlab.html` Exhibit) | `taxlab.html` | Static SVG + hardcoded `<b id="exco/exis/exkept">` text. Note: these are the **same numbers** as row #4 above, which *is* tested via `hub.py`/`test_drift_hub.py` — but this rendering is a separate, untested copy; `?state=` personalization JS rescales it, the unpersonalized baseline does not trace to a test | **ASSUMED** — known drift risk: if `STATE_ALPHA` moves, row #4 updates automatically (tested) and this baseline does not (untested copy). **Phase 2: either template this from the same `build_hub()` output or add a consistency test between the two** |
| 23 | ~~Homepage hero: "that gap was $320,000"~~ | **RETIRED 2026-07-29** — the four-step "Measure" step left the homepage | The capability sequence moved to `the-practice.html` and this figure was not carried with it, so the homepage now ships **no** dollar or percent claim at all. Row #22 (the same figure on `taxlab.html`) still stands and keeps its ASSUMED caveat. | **RETIRED** (from the homepage) |
| 24 | Tax-Atlas income drag default (Illinois): $78,268 | `tax-atlas.html` "What it means for you" | Client-side JS: `20000 × (4.95/100) × ((1.06³⁰−1)/0.06) = 78,267.6 → $78,268`. Formula and its assumptions ($1,000,000 taxable account, 2% yield, 6% growth, 30y) are stated in the page's `#assump` text | **ASSUMED** — reproducible from the stated formula, but it's untested JS arithmetic, not a Python module. **Phase 2: port to a tested `src/drift/*.py` function alongside `location_alpha3`/`compounded_fee_drag`** |
| 25 | Tax-Atlas per-state rate/exemption tiles (51 jurisdictions, e.g. IL 4.95% / $4,000,000 estate exemption) | `tax-atlas.html` `STATES` JS array | Hand-duplicated from the canonical `src/drift/state_facts.py` (`RATES`/`ESTATE`, consumed elsewhere by `statemap.py`). Spot-checked correct today (IL matches exactly) | **ASSUMED** — real drift hazard: zero test or generation pipeline ties this 562-line hand-typed array to `state_facts.py`; it is "coincidentally correct," not derived. **Phase 2: generate this array from `state_facts.py` at build time, or add a consistency test** |
| 26 | Harris household worked example: $8,000,000 total; IL estate-tax sequence $680,634 → $395,000 → $285,714; $0 in Texas; ~$69,000 avoided | `coordination.html`, echoed on `the-record.html`, `the-practice.html`, `decision-register.html`, `opportunity-register.html` | Explicitly labeled "an illustrative sample for a fictional family." Cites real law (IL 35 ILCS 405, $4M state exemption, $15M federal exemption). The nearest real function, `taxlab.py::il_estate_tax()`, produces *different* rounded values ($690,000/$285,000) on the same inputs — confirming these exact digits are hand-typed narrative, not code output, though internally consistent as a story. `src/drift/web/COORDINATION_ALPHA_MATH.md` §5 independently corroborates the ~$395,000 figure as a real, intentionally-uncounted gap | **ASSUMED** |
| 27 | ~3% / ~$30k/yr "what disciplined advice can add on $1M" | `the-record.html` | Cites Vanguard Advisor's Alpha, 2025 for the 3%; the dollar figure is a manual multiply, labeled as such ("The 3% is the study; the dollars are illustrative") | **ASSUMED** (cited study, illustrative dollarization) |
| 28 | $96,700 0% LTCG ceiling; $19k/$38k gift exclusion; $15M/$30M federal estate exemption | `the-record.html` | Real 2025–26 IRS figures, statute/Rev. Proc. citable; `taxlab.py` mirrors the exemption constants separately (`ASSUMPTIONS["estate"]`) but doesn't feed this page | **ASSUMED** (external law, accurately stated) |
| 29 | Case-study hypotheticals: $100,000 charitable gift, $3M inheritance, $900,000 vacation home, $600,000 conversation | `case-charitable-giving.html`, `case-inheritance.html`, `case-vacation-home.html`, and cross-links | No computation; scenario inputs for illustrative narratives, consistently labeled hypothetical | **ASSUMED** |
| 30 | Lattice edge weights: 6 of 21 edges drawn "structural", 15 "situational" | `hub.html` Plate II Coordination Engine + its rest caption | Derived from the page's own `TRIG` decision traces: an edge is structural iff BOTH its systems appear in **every** published trace (currently 5). Yields the core {Investments, Taxes, Cash Flow, Family / Purpose}. Guard: `tests/test_hub_lattice_weights.py` (4 tests) recomputes the set from the traces and fails if markup and traces diverge. A continuous "correlation strength" ramp was explicitly rejected: nothing derives pairwise correlation between systems, and inventing one would be an unfalsifiable front-page claim. | **DERIVED** |
| 31 | "N of 7 systems" on the coordination-surface map | `score.html` | A count of distinct systems touched by the checked factors, via a `FACTOR_SYS` map from each of the 10 inventory factors to the systems it moves. The mapping is **editorial** (a scope claim: is this system in play, yes or no) and asserts no magnitude, no rating, and no score. Deliberately not a 1–10 self-rating radar, which would be UNSOURCED by construction and drawn with the authority of an instrument. | **ASSUMED** (scope claim, no magnitude asserted) |
| — | `score.html` (Coordination Assessment) | — | No dollar/percent claims found — the page is explicitly "an inventory, not a grade/score/meter" | **N/A** |

## Enforcement

An automated test that fails whenever *any* dollar/percent figure appears in `docs/` without a
provenance row is **not feasible without an unacceptable false-positive rate**: the vast majority of
numeric strings in the shipped HTML are not claims at all — years, CSS percentages, table column widths,
disclosure boilerplate ("not FDIC insured"), phone-formatted sequences, `<meta>` values, and so on. A
regex sweep would need a maintained allowlist as large as this document itself, which is the document.

**Enforcement is therefore by review**, per the original mandate's own fallback: this file is the
checklist for any change that introduces or edits a public number. Two things *are* automated and will be
kept that way going forward:
- Every **DERIVED** figure above already has a named test in `tests/` that fails on drift — that's the
  strongest guard available and doesn't need duplicating here.
- New pinning tests should be added whenever an ASSUMED figure is formalized with a stated parameter set
  (see the Phase 2 items on rows 17–19, 22, 24–25) — each such test both derives *and* enforces its figure,
  moving it from "ASSUMED, weak" toward "DERIVED."

## Phase 2 backlog (from this audit)

1. **Row 20** — cite or remove the "consistent with published tax-alpha research" appeal in `leakage.html`.
2. ~~**Rows 17–19** — pin a canonical illustrative household for the `hub.html` register sample.~~
   **CLOSED 2026-07-29 by removal.** The four-plate homepage replaced the register's "Potential" dollar
   column with "Next review" (a date), so there is no longer a figure to derive. This is the cheaper and
   more honest resolution of the two: the claim the register actually makes is that a matter is *carried
   with an owner and a date*, and a date is verifiable on its face. Should a dollar column ever return,
   the original instruction stands: derive it, do not reverse-fit it.
3. **Rows 22–23 vs. row 4** — resolve the untested duplicate of the tested $410k/$90k/$320k figure (either
   template from the same source or add a consistency test).
4. **Row 24** — port the Tax-Atlas income-drag formula into a tested `src/drift/*.py` function.
5. **Row 25** — tie `tax-atlas.html`'s 51-jurisdiction JS array to `state_facts.py` (generation or test).
6. **Consolidate** this file with `docs/Evidence_Register.md` into one register (noted above).
7. Conversion/UX ideas raised alongside this audit (lead with the prospect's own `before` figure when
   personalized, dollarize the alpha at the prospect's portfolio size, protect the resolved-row ratio on
   the register) are product decisions, not provenance fixes — logged in `OPERATIONS.md`, not implemented
   here; they touch live funnel copy and warrant their own review pass.
8. Stale-sitemap-entries cleanup (`library.html`, `familyoffice.html`) — already logged in `OPERATIONS.md`,
   unrelated to figure provenance but found during the same launch pass.

## What shipped in this pass (already committed)

`leakage.html`'s "Read it honestly" guardrail previously stated only the four-representative-state
range (+3.7–4.7%/yr) with no acknowledgment that individual jurisdictions (WA at 3.3%, MA/NYC at 4.8%)
fall outside it — a real risk that a personalized WA or MA/NYC visitor reads a static paragraph
contradicting their own number. Fixed to also state the true full-table range (+3.3–4.8%/yr), with a new
regression test (row 5 above) pinning the copy to `STATE_ALPHA`'s real min/max so it can't drift back out
of sync. This is a local commit on the review branch pending the same review gate as every other
production content change this launch.
