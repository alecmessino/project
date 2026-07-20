# Phase Ω — Institutional Experience Audit

**Driftwood Wealth · public site · July 2026.**
Auditor stance: creative director, editorial director, product designer, UX researcher,
conversion strategist, information architect — and a partner deciding whether to hand this
firm a nine-figure family. Benchmark set: Bessemer Trust, Rockefeller, ICONIQ, Howard
Marks' memos, Ferrari annual reports, Apple HIG, Linear, Stripe docs.

**Method.** All 44 core public pages (plus 2 sampled state pages) walked headless at
1280px and 390px with a metrics harness: opening geometry, H1/body typography, identity
and motif frequency, CTA inventory, body-link graph (dead ends), footer variants, mobile
overflow. Key pages reviewed visually desktop + mobile. The full conversion path followed
as a first-time visitor. Measured data tables in the Appendix. Sunk cost ignored
throughout, per the brief.

**Verdict in one line.** This is a top-decile institutional site with one severe
conversion flaw, one page-level duplication, and a layer of measurable typographic
variance — all fixable inside the existing system, none requiring redesign.

---

## 1 · Executive Summary — the 15 changes that buy 80% of the quality

Ranked by perceived-quality-per-effort.

1. **Replace the conversion terminus.** Every path on the site — the nav CTA on all 44
   pages, the homepage close, taxlab's primary — ends at a **`mailto:` to a personal
   gmail.com address**. Forty-three pages of institutional grammar, then a personal inbox
   at the moment of commitment. This is the single largest trust break on the site and it
   sits at its most important pixel. *Fix:* a quiet conversation page (or inline section)
   with a firm-domain address and a scheduling affordance. **Blocked on real facts
   (domain, email, scheduler) — principal input required; nothing may be invented.**
2. **Unify the opening pad for real.** Measured nav→first-element distance runs
   **22px → 158px** across the site (target: one value, 44px, with sanctioned §9
   exceptions). The §6 token governs the eyebrow's margin but each template's container
   padding still varies. One pass over container paddings makes QA-gate #1 true sitewide.
3. **Collapse the H1 ladder.** Nine distinct rendered H1 sizes (25→55px). The spec allows
   three: hero (homepage), standard, document/denser-research. Everything else is
   template archaeology.
4. **Ration the word "coordination."** 225 occurrences site-wide; 24 on the homepage
   alone; 18 on coordination.html; 15 on howitworks. The site's central word is being
   spent like a common one. Target: roughly half, with the homepage under 10. Scarcity is
   what keeps the thesis word precious.
5. **Resolve `inside` vs `howitworks`.** Both answer "what actually happens?" — inside
   opens with a numbered engagement loop (Discovery → Coordination Index → …) that
   howitworks then re-narrates week-by-week; the new transition-plan sample narrates it a
   third time. One question, three tellings. *Recommendation:* inside re-scopes to purely
   **the system and its artifacts** (the archive, the registers, the records — no
   engagement steps); howitworks keeps the sequence; the transition plan stays the
   document-form proof. No page deleted; each answers one question.
6. **One name per destination; quieter verbs.** The Tax Diagnostic is called three
   different things in CTAs ("Run the Tax Diagnostic →", "See what you'd keep →",
   "Measure your tax drag →"). Canonicalize on "Run the Tax Diagnostic →" and retire the
   flagged marketing phrasings. Also: the hero's dark filled button is the loudest object
   on the front door — the institutional-friction principle argues for the quiet text-link
   treatment there.
7. **Kill the two dead ends with series navigation.** `equities` (Nº 001) and `tearsheet`
   (Nº 003) have zero body links — a reader finishes and stops. The series already has
   numbers; give every Core Alpha page a quiet prev/next series line (Nº 001 ↔ 002 ↔ 003
   ↔ 004). Fixes the dead ends and makes the series feel bound.
8. **Normalize the disclosure feet.** Ten distinct footer-disclosure phrasings across 44
   pages. Legitimate variance is by *family* (sample · research · tool · narrative);
   define the four canonical forms and apply them.
9. **Put the human in the funnel.** The conversion walk peaks at the archive ("these
   people run a system") and then hits an anonymous terminus. Nowhere between homepage
   and the ask does a prospect meet the person they'd be trusting. The queued
   boutique-positioning + human-story pass is *conversion* work, not brand work — raise
   its priority to immediately after the terminus fix.
10. **Ship "How we work together" before the Tools pass.** The journey's biggest
    unanswered question ("what is it like to be a client?") already has a queued page.
    The audit confirms it's the missing step between evidence and the ask — sequence it
    right after №9 rather than pre-freeze.
11. **Give the homepage exhibit one more degree of ink.** At rest the radial thesis
    diagram reads as near-empty whitespace at 1280px, and its interaction is hover-only —
    invisible on touch. Raise resting opacity slightly; add a tap affordance on mobile.
    (Museum-quiet, yes — but a museum lights the exhibit.)
12. **Fix the taxlab loop.** taxlab's primary CTA sends the reader *back* to the homepage
    anchor (`index.html#conversation`) — momentum earned on the strongest evidence page is
    spent on a scroll-jump to a mailto. Point it at the №1 conversation destination.
13. **Eyebrow grammar stragglers.** `inside` names the firm in its eyebrow ("INSIDE
    DRIFTWOOD · …" — the nav already does); `manual` says "THE RESERVED TIER" (internal
    jargon a client shouldn't need); `familyoffice`'s "THE OPERATING MODEL" collides with
    the Operating System vocabulary. Three small renames.
14. **Title-tag grammar.** `<title>` endings vary ("— a sample", "— a sample.", none) and
    the "Driftwood Wealth" suffix is inconsistent. One pattern:
    `Page Name — Driftwood Wealth`, samples as `Page Name — a sample — Driftwood Wealth`.
15. **Apply the 20% test to the six heaviest pages.** coordination (1,640 words), ledger
    (1,528), decision-register (1,510), capital-allocation (1,471), constitution (1,354),
    opportunity-register (1,264) — each far over its family's reading budget. Every one
    improves with a fifth fewer words; the quiet pages (insights 308, principles 340,
    score 369, taxlab 370) prove the register the heavy ones should hit.

---

## 2 · Critical Issues — what materially hurts trust

**C1 · The gmail terminus (severity: critical).** Detailed above (№1). A $25M prospect
reads "Schedule a conversation →" and their mail client opens addressed to a personal
gmail. Every hour of institutional signal upstream is discounted at that moment. Nothing
else on this list matters as much.

**C2 · The anonymous institution (severity: high).** The site never introduces a human
being. For a boutique whose true product is judgment, the absence reads as evasive above
$10M. (Queued with principal-provided language — this audit only re-ranks it.)

**C3 · Hover-only exhibits on touch (severity: high).** The homepage thesis diagram and
several exhibit interactions are hover-gated; on phones — half of first visits — the
site's centerpiece is inert and undiscoverable. Needs tap parity, not redesign.

**C4 · One question, three pages (severity: medium-high).** inside / howitworks /
transition-plan overlap (Exec №5). Duplication reads as organizational, not editorial —
the one thing this site otherwise never does.

**C5 · Research dead ends (severity: medium).** Nº 001 and Nº 003 strand the reader —
in the *credibility* family, where a bound-series feel matters most.

**C6 · The loud ask (severity: medium).** Two dark filled buttons (hero, close) on the
homepage against an otherwise hairline-and-type system; plus "Measure your tax drag."
The most institutional sites whisper their asks; this one raises its voice exactly twice,
in the wrong register.

**C7 · Disclosure drift (severity: medium).** Ten footer variants — compliance-adjacent
copy is where inconsistency is most noticed by exactly the wrong readers (attorneys, CPAs,
diligence teams).

*Explicitly checked, and clean:* no fabricated operational facts anywhere (foundation
facts remain blank rather than invented — correct); no pre-2026 firm history; every
sample labeled illustrative; hypothetical marking consistent at point-of-performance;
no mobile horizontal overflow on any audited page; RIA identity + ADV/CRS present on
every client-facing surface.

---

## 3 · Polish Backlog — ranked micro-improvements

Effort: S (<1h) · M (half-day) · L (day+). Impact: trust/perceived-quality H/M/L.
**Tier 1 = do before anything else. Within tiers, ordered by impact.**

### Tier 1 — Conversion & trust (12)

| # | Page | Issue | Recommendation | Effort | Impact |
|---|---|---|---|---|---|
| 1 | all (nav) | CTA → mailto:gmail | Firm-domain conversation destination (facts from principal) | M | H |
| 2 | index #conversation | Primary ask is a mailto | Quiet conversation section: address + scheduler + what-happens-next | M | H |
| 3 | taxlab | Primary CTA loops to index anchor | Point at conversation destination directly | S | H |
| 4 | index hero | "Measure your tax drag →" filled button | "Run the Tax Diagnostic →" as quiet link/outline | S | H |
| 5 | index close | Second filled button | Outline/text treatment; one visual register for asks | S | M |
| 6 | howitworks | CTA "Measure your tax drag →" | Canonical label | S | M |
| 7 | statemap/others | CTA "See what you'd keep →" | Canonical label | S | M |
| 8 | site | No human before the ask | Boutique + human passage (principal language, queued) | M | H |
| 9 | site | "What it's like" gap | Ship "How we work together" next | M | H |
| 10 | equities | Zero body links (dead end) | Series prev/next line | S | H |
| 11 | tearsheet | Zero body links (dead end) | Series prev/next line | S | H |
| 12 | ledger, equities_case_studies | Series incomplete without nav | Same series line for Nº 002/004 | S | M |

### Tier 2 — One rhythm (the measured variance; 34)

Opening pad → one 44px value (container-padding pass), per measured deviation:

| # | Pages (measured pad) | Effort | Impact |
|---|---|---|---|
| 13 | index (77) — hero exception: *document* as intentional in §9 | S | M |
| 14–21 | case-* ×8 (92) | S | H |
| 22–27 | coordination, familyoffice, fees, howitworks, inside, review (94) | S | H |
| 28 | thesis (88) | S | M |
| 29 | taxlab (84) | S | M |
| 30 | score (90) | S | M |
| 31 | statemap (97) | S | M |
| 32 | leakage (99) | S | M |
| 33 | decision-register (123) | S | M |
| 34 | awor (158) | S | M |
| 35–40 | record family: manual 70 · constitution 76 · opportunity-register 79 · capital-allocation/ic-memo/record/transition-plan 80 — pick one document pad (56?) and apply to all seven | S | H |
| 41 | states (22), texas/illinois-tax (52) — statepage.py template | S | M |
| 42 | research (23–32) — sanctioned denser, but make all four equal | S | M |
| 43 | site | H1: 9 sizes → 3 tokens (hero 55 / standard 36 / document 32; research 25 stays) | M | H |
| 44 | about/inside/thesis/howitworks/taxlab/score +13 more | H1 33px → standard token | S | M |
| 45 | principles, concentration (34) | → standard token | S | L |
| 46 | ledger, leakage, equities (38) | → standard token | S | L |
| 47 | decision-register (40); capital-allocation/ic-memo/transition-plan (42) | → document token | S | L |

### Tier 3 — Editorial (identity, motifs, weight; 26)

| # | Page | Issue | Recommendation | Effort | Impact |
|---|---|---|---|---|---|
| 48 | index | "coordinat-" ×24 | Halve; the hero + thesis section carry it, others paraphrase | M | H |
| 49 | coordination | ×18 | The page named Coordination may say it least — trim to ~8 | M | M |
| 50 | howitworks | ×15 | Trim to ~6 | S | M |
| 51 | inside | Duplicated engagement narrative | Re-scope to system-and-artifacts (Exec №5) | M | H |
| 52 | inside | Eyebrow "INSIDE DRIFTWOOD · THE FINANCIAL OPERATING SYSTEM" | → "THE OPERATING SYSTEM" | S | M |
| 53 | manual | Eyebrow "· THE RESERVED TIER" jargon | → "PERMANENT OPERATING RECORD" | S | M |
| 54 | familyoffice | Eyebrow "THE OPERATING MODEL" collides with OS vocabulary | → "THE MODEL" or fold under Essay family label | S | L |
| 55 | decision-register | Eyebrow carries "A SAMPLE…" while work-product pages carry "SAMPLE WORK PRODUCT" | One sample-label convention across archive | S | M |
| 56–61 | coordination, ledger, decision-register, capital-allocation, constitution, opportunity-register | 20% test (each >1,250 words vs family budget) | Cut one-fifth each | M×6 | H |
| 62 | opportunity-register | 12 brand mentions (frontmatter fields legitimate; prose isn't) | Delete-"Driftwood" heuristic on prose only | S | M |
| 63 | manual | 11 mentions (changelog "By" cells legitimate) | Same — prose only | S | M |
| 64 | constitution | 10 mentions | Same | S | M |
| 65 | index | "what you keep" ×2 + "operating system" ×3 + "coordination" ×24 stacked | One motif per section | M | M |
| 66 | case-stock-options | "what you keep" ×3 | Keep one | S | L |
| 67 | familyoffice | "family office" ×5 on the page arguing you don't need one | Trim to 2–3 | S | M |
| 68 | fees | Brand ×6 in 820 words | Prose trim per heuristic | S | L |
| 69–73 | titles: about ("—" variants), samples (". " variance), research (mixed) | One title grammar | S | M |

### Tier 4 — Chrome, feet, wayfinding (21)

| # | Scope | Issue | Recommendation | Effort | Impact |
|---|---|---|---|---|---|
| 74–77 | 4 canonical disclosure feet (sample / research / tool / narrative) | 10 variants today | Define + apply | M | H |
| 78 | statemap/states/state-* | Foot leads "Driftwood." bare | Align to tool foot | S | L |
| 79 | awor | Eyebrow slot resolves to H1 (mast has no .eyebrow) | Add proper eyebrow to mast | S | L |
| 80 | record | Shelf metas mix "· as of July 2026" and none | One meta grammar | S | L |
| 81 | site | "You are here" context (Phase Z) — confirmed needed on archive + research | Quiet context line, folio-style | M | M |
| 82 | og images | Every page ships og/index.png | Per-family OG cards (post-freeze fine) | L | L |
| 83 | index | Page height 5,400px — evidence section repeats leakage's claim | Trim Exhibit 3 intro (say once, link diagnostic) | S | M |
| 84 | mobile nav | Two-row label groups wrap tall at 390px | Compress labels row on mobile | M | M |
| 85 | index mobile | Hero button full-width dark slab | Match quiet treatment (item 4) | S | M |
| 86–89 | thesis diagram | Resting ink; tap affordance; "Hover any system" says *hover* on touch; focus states for keyboard | Raise rest opacity; tap = select; copy → "Select any system"; :focus-visible on nodes | M | H |
| 90 | statemap map tiles | Hover-only detail on touch | Tap parity (may exist — verify on device) | S | M |
| 91 | score | CTA weight consistent with new ask register | Align | S | L |
| 92 | review | Overlaps awor's role in one paragraph | Cross-link instead of re-describe | S | L |
| 93 | library | Item metas mix quote-style and label-style | One meta grammar | S | L |
| 94 | insights index | Item 1 meta "WORKED EXAMPLE · 6 MIN READ" vs others "JULY 2026 · 4 MIN READ" | One meta grammar (type · time) | S | L |

### Tier 5 — Fit and finish (one-pixel class; 16)

| # | Scope | Issue | Effort |
|---|---|---|---|
| 95 | hr/rule weights | `.rule` 1px vs `border-top:3px` research header vs 2px ledger-head — document the three sanctioned weights, kill strays | S |
| 96 | `.edition` vs `.frontmatter` duplication check on non-frontmatter pages | keep one per page | S |
| 97 | stamp borders (`--ghost-line`) vs card borders (`--line`) adjacency | intentional? document | S |
| 98 | research hyp-pill vertical alignment at 11px eyebrows | optical align | S |
| 99 | archive-memory link underlines: hairline vs body-link style | one link treatment in memory blocks | S |
| 100 | foliobar tracking (.16em) vs eyebrow (.2em) | document as intentional or unify | S |
| 101 | case pages: quoted sub-question typography vs essay dek | verify same serif size | S |
| 102 | taxlab exhibit-readout number tabular alignment | verify tnum applied | S |
| 103 | ledger summary-card "Hypothetical backtest" position after eyebrow change | re-check hierarchy | S |
| 104 | states index vs state pages opening pad (22 vs 52) | unify statepage template | S |
| 105 | close/navy panels: constitution 40px pad vs manual 40 vs awor cta variant | one close spec | S |
| 106 | footer generated-stamp presence (index only) | either every data page or none | S |
| 107 | favicon/mask on sample pages | verify all carry full icon set | S |
| 108 | print stylesheet for archive/samples ("print and bind" bar) | add @media print pass post-freeze | L |
| 109 | brand.html noindex + exclusion from any index | verify | S |
| 110 | workspace.html linked from public? | boundary check — evidence vs operation | S |

*(Items 13–47 expand to one row per page in practice; counted individually the backlog is
~130 items.)*

---

## 4 · The Conversion Journey

Walked as a skeptical principal, homepage → meeting.

| Step | Moment | Momentum |
|---|---|---|
| 1 | **Hero.** "Most advisers manage investments. / Driftwood coordinates your financial life as one system." | **Gain.** Positioning lands in four seconds. |
| 2 | **Operating System section.** Archive named, samples linked. | **Gain.** "They keep records like an institution." |
| 3 | **Thesis diagram.** | **Flat.** Quiet to the point of invisible; on phone, inert (C3). The best idea on the page is the easiest to scroll past. |
| 4 | **How it works (I–IV).** | Gain. The sequence reads institutional. |
| 5 | **Evidence exhibits.** Drag table → 30-year chart with methodology + version stamp. | **Strong gain.** This is where belief forms. |
| 6 | **Click-out: Tax Diagnostic.** Personalized state figures, honest "modeled" framing, single CTA. | Gain. |
| 7 | **After-Tax Review (taxlab).** The strongest single page. Its CTA… | **Loss.** …bounces back to the homepage anchor (C6/№12). |
| 8 | **The archive** (record → constitution → register → IC memo → transition plan). | **Peak trust.** Nothing else in the RIA world looks like this. The cross-referenced fiction audits itself. |
| 9 | **"Who are these people?"** | **Loss.** No human anywhere (C2). The about page explains *why* Driftwood exists but no one is home. |
| 10 | **The ask.** `mailto:` → personal gmail. | **Critical loss** (C1). The journey's last step is its weakest — and the only one a prospect must take. |

**Net:** the site *earns* the meeting by step 8 and then declines to accept it. Momentum
is built by evidence and the archive; it is lost exclusively at interaction seams (7) and
the final ask (9–10). Fix №1/№8/№9/№12 and the journey has no down-steps until the
close — which is then a formality.

---

## 5 · Institutional Readiness Score

| Dimension | Score | Why |
|---|---|---|
| Narrative | **9.0** | One thesis, held everywhere; five systems named; family questions defined. Docked for the inside/howitworks overlap and coordination-word fatigue. |
| Editorial | **8.5** | Say-it-once discipline visibly applied; every recent pass subtracted. The six heavy pages and motif saturation remain. |
| Visual Design | **8.8** | The limestone/ink system, exhibit plates, and archive chrome are genuinely distinguished. Two loud buttons and an under-inked centerpiece cost it. |
| Typography | **7.5** | The faces and ladder are right; the *execution* shows 9 H1 sizes and 22–158px openings. Entirely mechanical to fix — but today a trained eye sees template eras. |
| Navigation | **7.5** | Nav + folio are sound; dead ends in Research, no series navigation, no "you are here" on deep pages, work-product shelf reachable only via record.html. |
| Conversion | **5.5** | The funnel design is intelligent (diagnostic → review → ask) but the terminus is a personal gmail mailto, the strongest page loops backward, and no scheduler exists. The lowest score on the card, for the most fixable reasons. |
| Trust | **7.5** | Honesty infrastructure is exceptional (labels, hypothetical marking, no invented facts, client-archive-not-firm-history). Docked hard for C1 and C2 — trust is a chain, and those are its last links. |
| Institutional Presence | **8.7** | The Record, versioning, Authority/Status vocabulary, series numbering: no competitor set does this. The remaining tells are §3's variance items. |
| Luxury Feel | **8.3** | Quiet, paper-like, unhurried — genuinely expensive-feeling on the editorial pages. Loud CTAs and pad jumps break the spell at seams. |
| Product Differentiation | **9.5** | A published institution with an internally consistent archive is close to uncopyable. This is the moat, and it's real. |
| **Overall** | **8.2** | A great institutional site one conversion fix, one merge, and one variance pass away from a 9+. |

---

## 6 · The Final Question

> *"If I had never met Alec, would this website alone convince me to trust Driftwood
> Capital with $25 million?"*

**Not yet — but it is one honest afternoon of decisions away, and almost nothing else in
the category comes closer.**

What would convince me: the archive. No advisory site I have seen publishes a versioned
constitution, an append-only decision register with reopen-triggers, an IC memo whose
citations actually resolve, and a transition plan whose promises are already kept
elsewhere in the record. That corpus reads like an institution that *operates*, and it
would get Driftwood the meeting against any name on the benchmark list.

What stops me at $25M, in order: **(1)** the ask resolves to a personal gmail address —
at that moment the institution evaporates; **(2)** I have never met a human — no
principal, no bio, no accountability surface, which at this asset level reads as a risk,
not a mystique; **(3)** I cannot find what engaging actually involves — cadence,
responsibilities, communication (the queued "How we work together" page is precisely
this); **(4)** the small variance layer (openings, H1s, feet) that a diligence-minded
reader subconsciously tallies as "website," not "institution."

None of these are design problems, and none require invention. Items 2 and 3 are already
queued with principal-provided language; item 1 needs three real facts; item 4 is
mechanical. When those land, my answer changes to **yes — for the meeting and the
mandate conversation** — which is all a website should ever be asked to do.

---

## Appendix — measured data (July 2026)

- **Opening pads (nav→first element, px):** 22 states · 23 tearsheet/studies · 30–32
  research · 44 essays/indexes (post-foundation) · 52 state pages · 70–80 archive ·
  84–99 tools/essays-unmigrated · 92 cases · 123 decision-register · 158 awor · 77 hero.
- **H1 sizes:** 25 ×2 · 32 ×4 · 33 ×19 · 34 ×2 · 36 ×9 · 38 ×3 · 40 ×1 · 42 ×3 · 55 ×1.
- **Identity:** median 4–6 "Driftwood"/page (nav+disclosure baseline); archive documents
  10–12 (frontmatter/changelog fields — legitimate); no page pathological.
- **Motifs:** coordination 225 · what-you-keep 20 · family-office 12 · operating-system 9.
- **Dead ends:** equities, tearsheet (0 body links). **No-CTA pages:** none.
- **Mobile:** no horizontal overflow on any of 44 pages at 390px.
- **Feet:** 10 disclosure variants (14× "Illustrative and educational…", 5× "Educational…",
  3× state-atlas form, 2× research form, 6 singletons).
- **Word counts:** heaviest — coordination 1,640 · ledger 1,528 · decision-register 1,510 ·
  capital-allocation 1,471 · constitution 1,354 · opportunity-register 1,264; quietest —
  insights 308 · principles 340 · score 369 · taxlab 370.
