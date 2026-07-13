# Institutional Publishing System — Specification v1 (for approval)

The public Driftwood site is feature-complete. What remains is not design but
**editorial consistency**: every page should feel like one authored publication,
not an accumulation of excellent individual pages. This document defines the
publishing system. Once approved, the site-wide normalization is mostly
mechanical.

**Nothing in this document has been implemented.** It is the contract to approve
first.

---

## 0 · The principle

Every page, within the first viewport, answers four questions in the same order:

1. **What kind of document is this?** — the family (eyebrow)
2. **Why does it exist?** — the title + one-sentence deck
3. **Where am I in the larger system?** — nav + (for documents) the family folio
4. **What should I do next?** — a single, quiet next step

Today those answers vary page to page. The fix is one grammar, six families, and
a rule that **the site says everything once**.

---

## 0.5 · Editorial principles

The voice, distilled. Every heading, label, and sentence is filtered through these
before it ships. They are the reason the site reads as one authored institution.

1. **Coordination is the product; the evidence is downstream.** Every page reinforces
   that Driftwood coordinates a system. Tax, estate, liquidity, and returns are where
   coordination becomes *measurable* — never the product itself.
2. **Say it once.** The firm is named once (nav), the page once (title), each idea
   once. A repeated word or idea weakens the original.
3. **One voice — quiet, confident, observational, evidence-first.** No product copy
   ("get started," "unlock"), no hype ("up to," "supercharge"), no factor-strategy
   jargon the reader must decode.
4. **Teach, don't sell.** Where a page can show the mechanism, it shows it; the
   exhibit or the interaction does the persuading.
5. **Show on identical terms.** Claims are demonstrated on the same holdings, the same
   exposure — credibility before persuasion.
6. **Restraint over completeness.** Cut anything that competes with the page's one
   thesis. A good section that is redundant still goes.
7. **Honesty is the house style.** Hypothetical is labeled hypothetical; nothing is
   claimed the firm cannot stand behind; no operational fact is fabricated.
8. **Read it aloud.** Copy that trips when spoken gets rewritten. Institutions sound
   composed.

---

## 0.6 · The one-question test

Every page answers **exactly one question.** If a page answers two, split it. If it
answers none, delete it. This is the sharpest editorial filter we have — it decides
what a page is *for* before a word is written.

| Page | The one question |
|---|---|
| Home | *Why Driftwood?* |
| Operating System | *What actually happens?* |
| After-Tax Review | *Can coordination be measured?* |
| Manual | *How is this household run?* |
| Decision Register | *Why was each decision made?* |
| Opportunity Register | *What should happen next?* |
| Research | *Why should I believe this?* |

This is the page-level twin of the family question (§2): the family says what *kind* of
document this is; the one-question test says what *this* document is for.

## 0.7 · The publishing checklist (run against every page during normalization)

Not "does it compile?" — "is it authored?" Every page is walked against this list before
its family PR opens.

- **Identity** — one institution · one page title · one document family.
- **Narrative** — one thesis · one deck · no duplicated idea.
- **Headline integrity** — no heading may imply something the methodology or data
  qualifies differently. ("Across three decades" over a 40-year method line; "long-term"
  over rolling ten-year windows.) Little mismatches quietly erode trust; the headline
  never carries a number the data owns.
- **Structure** — consistent opening rhythm · spacing · measure · rule treatment.
- **Navigation** — a clear next document · a clear relationship to the wider body.
- **Editorial** — read it aloud once · **remove one unnecessary sentence.**

**Every page loses something during normalization.** That is a requirement, not an
aspiration. A normalization commit that only adds is suspect.

## 0.8 · The 30-second rule

A sophisticated prospect lands on *any* page — not necessarily the homepage. Within
thirty seconds they can answer three questions:

1. **What kind of document is this?** (the family)
2. **Why does it exist?** (its singular purpose)
3. **What should I read next?** (the natural continuation)

If a page fails any one of the three, it is not finished. This is the page-level twin of
the one-institution test: §0.6 decides what a page is for; this decides whether a reader
can *tell*.

---

## 1 · The audit — what's inconsistent today

Surveyed all 40 shipped pages. Findings, worst first:

| Problem | Evidence |
|---|---|
| **Triple naming** | `insights.html` opens **Insights** (running bar) · **Insights** (eyebrow) · **Insights** (title) before one idea. |
| **Double naming** | `about.html`: **Our Story** in the running bar *and* the eyebrow. Also `statemap`, `review`, `workspace` repeat their name across marker + title. |
| **Firm named twice** | The thin `.run` bar above the nav repeats "Driftwood Capital," which is already the nav lockup — on ~20 pages. |
| **~6 header systems** | `run+doc`, `run` only, Record masthead (`run+doc+masthead+foliobar`), `doc` only, `hero`, and pages with *no* standard header (`philosophy`, `report`, `tearsheet`). |
| **Eyebrow semantics vary** | Sometimes the family ("Coordination Library"), sometimes the page name, sometimes a descriptive phrase ("Too much of a good thing"), sometimes absent. |
| **Decks inconsistent** | Present on ~25 pages, absent on the rest with no rule. |
| **Stale mark** | Record running headers still show the **old "D" monogram**, not the frozen confluence mark. |
| **Two fictional families** | Samples say **"Harris"** (Decision Register) and **"Merrell"** (Manual). Pick one. |
| **Opening spacing varies** | Some pages land immediately under the nav; others 120px lower. |

The `.run` running bar is the single biggest offender: it duplicates the nav
identity *and* the page eyebrow. It should be **removed from narrative pages** and
**repurposed as a folio** on documents only (see §4).

---

## 2 · The six document families

Every page belongs to exactly one family. A visitor should feel the family
without reading a label — through density, measure, and framing.

| Family | Voice | Pages |
|---|---|---|
| **Essay** | Editorial, large type, long measure, breathes | about · philosophy · principles · thesis (How We Invest) · fees · howitworks · familyoffice · the 3 Insights essays · insights & library (indexes) |
| **Case** *(essay sub-family)* | Narrative, worked example, one lesson | the 8 `case-*` pages |
| **Research** | Dense, academic, citations, hypothetical-labeled | equities (Core Alpha) · ledger · tearsheet · report · concentration |
| **Record** | Archival — folio, stamp, append-only tone | decision-register · opportunity-register · awor · record (bound volume) |
| **Reference** | Procedural, governing, sectioned | manual · constitution · capital-allocation |
| **Exhibit** | Observation-first, interactive, minimal copy | homepage thesis · After-Tax Review (taxlab) · coordination |
| **Tool** | Utility, minimal framing, do-something | State Tax Atlas · Tax Diagnostic · Coordination Assessment |

**The question each family answers.** A family isn't a look — it's an editorial job.
Every page in a family opens by answering its family's one question, and its density,
measure, and framing all serve that answer:

| Family | The one question it answers |
|---|---|
| **Essay** | *Why does Driftwood think this?* |
| **Case** | *What did coordination change for one household?* |
| **Research** | *What does the evidence actually show?* |
| **Record** | *What was decided — and what does the archive hold?* |
| **Reference** | *How is this household run?* |
| **Exhibit** | *Can I see coordination happen?* |
| **Tool** | *What does this mean for me?* |

If a page can't answer its family's question in its first viewport, it's either in the
wrong family or missing its thesis.

*(Record + Reference share one masthead treatment — "the Driftwood Record" — since
they are one bound archive. Exhibits and Tools are the two families that may break
the reading measure.)*

---

## 3 · The canonical opening (all pages)

One grammar. Read top to bottom:

```
┌ NAV ─────────────────────────────────────────────────────────┐
│  ⟜ Driftwood Capital  ·  Understand / Discover  ·  CTA        │   ← the ONLY place the firm names itself
└──────────────────────────────────────────────────────────────┘
   [ family folio ]        ← documents only (§4B); never on narrative pages
   EYEBROW                 ← the family or section, in tracked caps. Never the title.
   Primary Title           ← the page's own thesis, said once
   One-sentence deck.      ← serif, dim, 1–2 sentences max
   ────────────────        ← hairline
   Body
```

**Absolute rules**
- The firm names itself **once** — in the nav lockup. Kill the `.run` bar's "Driftwood Capital."
- The page names itself **once** — in the title. The eyebrow is the *family*, never a repeat of the title.
- Exactly **one deck**, 1–2 sentences. No page opens straight into body; none stacks three paragraphs before the first idea.
- Everything below the hairline is body.

---

## 4 · The two header systems

Reduce ~6 systems to **two**. Everything else is a named exception (§9).

### A · Narrative header — Essay, Case, Exhibit, Tool
No running bar, no folio. The nav is the only chrome.

```
EYEBROW (family / section)
Primary Title
One-sentence deck.
──────────────
```
- Top padding: `--open-pad` (§6), identical on every narrative page.
- Eyebrow examples: `ESSAY`, `COORDINATION LIBRARY`, `EXHIBIT`, `THE STATE TAX ATLAS` (a tool may use its own name as eyebrow only when there is no separate title).

### B · Document masthead — Record, Reference
The archival treatment that already works on `manual.html`, cleaned up.

```
[folio]  THE DRIFTWOOD RECORD · Constitution · Capital Allocation · The Manual · …
EYEBROW (record type, e.g. PERMANENT OPERATING RECORD)
Primary Title
One-sentence deck.
                                          [ CONFIDENTIAL · prepared for the Harris household ]
```
- The folio replaces the `.run` bar and provides family wayfinding.
- Uses the **frozen confluence mark**, never the old "D."
- One fictional household name site-wide: **Harris**.

**Record & Reference are also a historical-integrity pass.** These are the pages
sophisticated visitors scrutinize most closely, so every archival artifact must answer:
is the branding **current** (frozen mark, never the old "D")? Are the **names**
internally consistent (one household: Harris)? Are the **dates** consistent? Are the
**version numbers** consistent? Are examples clearly labeled **illustrative** where
appropriate?

---

## 5 · Typography hierarchy (one ladder)

Never invent a hierarchy on one page. The ladder, all in the existing tokens:

| Level | Token | Spec |
|---|---|---|
| Eyebrow | `--sans` | 11px · 700 · .2em · uppercase · `--accent-strike` |
| Title (h1) | `--sans` | `clamp(30px,2.8vw+15px,44px)` · 700 · -.022em · `--ink` · max 18ch |
| Deck | `--serif` | 18px · `--dim` · max `--reading-measure` |
| Section head (h2) | `--sans` | 11px · 700 · .18em · uppercase · `--accent-strike` (narrative) — or the record `.sech` for documents |
| Body | `--sans` | 15–16.5px · `--body` · max `--reading-measure` |
| Caption / source | `--sans` | 10.5–12px · `--muted` |

Research may step body down to 14.5px for density; Essays step the title up. Those
are the only sanctioned deviations.

---

## 6 · Spacing & horizontal rhythm

One vertical rhythm so no one can guess which template made a page. Proposed tokens
(added to `driftwood.css` `:root`):

```
--open-pad:      44px   /* nav → header top, every page */
--eyebrow-gap:   15px   /* eyebrow → title */
--title-gap:     16px   /* title → deck */
--deck-gap:      26px   /* deck → hairline */
--rule-gap:      30px   /* hairline → body */
--reading-measure: 62ch /* already exists; the one prose measure */
```

Horizontal: one page gutter, one title max-width (18ch), one prose measure (62ch),
one hairline weight (1px `--line`). Only **Exhibits and Tools** may exceed the
measure, and only for a diagram or table.

---

## 7 · Navigation & wayfinding

- The nav lockup (mark + Driftwood Capital) is the sole firm identity per page.
- Narrative pages rely on the nav alone.
- Document pages add the **family folio** so a record always says "I am one of the
  Driftwood Record."
- Every page's eyebrow tells you the family; the `aria-current` nav state tells you
  the section. Between them, no page feels "entered from Google."

---

## 8 · Redundancy rules ("say it once")

Applied site-wide, the same discipline already applied to the homepage:

1. The firm is named once (nav).
2. The page is named once (title). Eyebrow ≠ title.
3. No running bar duplicating nav or eyebrow.
4. One fictional household: **Harris**.
5. Every repeated *idea* (not just word) is cut — if a sentence is said elsewhere,
   the weaker instance goes.
6. One institutional voice: quiet, confident, observational, evidence-first. Product
   copy ("Get started," "Unlock…") is removed.

## 8.5 · The institutional QA gate (before every merge)

No PR merges until every answer is **yes**, or the exception is intentional and documented
(§9). The checklist a reviewer can run in thirty seconds:

1. Does the page load with the **same top spacing** as every other page?
2. Is there exactly **one identity**?
3. Is there exactly **one eyebrow**?
4. Is there exactly **one H1**?
5. Is there exactly **one thesis**?
6. Is there exactly **one primary action**?
7. Does the **first screen** tell me where I am?
8. Does this page **earn its existence**?
9. Could **one paragraph** be deleted?
10. Does it feel like it belongs to the **same institution** as every other page?

---

## 9 · Sanctioned exceptions

Consistency is not uniformity. These stay unique **on purpose**:

- **Homepage** (`hub`): the hero is the one full-bleed opening; it may skip the eyebrow.
- **Record masthead**: keeps its folio + confidential stamp (it *is* the different family).
- **Exhibits / Tools**: may exceed the reading measure for a diagram or table.
- **Research dashboards**: may open denser, with the hypothetical banner above the deck.

Every other page conforms.

---

## 10 · Before → After (representative)

**`insights.html`**
- *Before:* `Driftwood Capital · Insights` (running bar) → `INSIGHTS` (eyebrow) → **Insights** (title) → deck. The word "Insights" three times; the firm twice.
- *After:* nav only → eyebrow `INSIGHTS` (the family) → title **How a financial life fits together.** (the index's own thesis) → deck. Named once. Follows the shipped `library.html` grammar — eyebrow = the collection, title = a thesis — rather than repeating the label as the title (a bare label isn't a thesis; see §3).

**`about.html`**
- *Before:* running bar `Driftwood Capital · Our Story` → eyebrow `OUR STORY` → title "Why Driftwood exists."
- *After:* nav only → eyebrow `OUR STORY` → title "Why Driftwood exists." (Good title kept; running bar removed.)

**`manual.html`**
- *Before:* running bar with old "D" monogram → folio → eyebrow → title; family = "Merrell."
- *After:* folio (frozen mark) → eyebrow → title; family = "Harris." Masthead treatment kept — it earns its difference.

---

## 11 · Rollout (after approval)

**The public website is now assumed complete.** From here, every change must justify
itself by *deleting complexity, not adding it* — no new content, no new capability, no
redesign. What remains is editorial normalization only.

**Phase A — finish the public editorial polish.** One PR per slice, reviewed, not
auto-merged. Two tracks are separated on purpose:

1. **Spacing foundation** (infrastructure — its own PR): the §6 tokens in `driftwood.css`
   plus the centralized opening rhythm. Reviewed alone so spacing never changes silently
   inside an editorial PR.
2. **Editorial normalization**, family by family, in the order a first-time visitor
   encounters the site — thinking, then evidence, then proof, then records, then examples,
   then tools: **Essay → Research → Exhibits → Record/Reference → Cases → Tools.**
   (Research and Exhibits shape first impressions far more than the archive.) Header
   grammar, duplicate removal, typography rhythm, page framing, taxonomy. Nothing
   conceptual.

Every slice is run against §0.7 (the checklist) and §8.5 (the QA gate) before it opens.

**The Research brief — the print-and-bind bar.** Research is the credibility family, so
its test is physical: *if someone printed every research page and bound them, would they
read as one series?* Normalize title hierarchy, abstract/deck placement, methodology
placement, disclosure treatment, citations, figures, footnotes, version numbers, and
update dates until the answer is yes.

**Series identity.** Every research document is visibly one of a numbered series — quiet,
NBER-not-flashy. The family eyebrow carries the series and the number
(`CORE ALPHA RESEARCH · Nº 003 · LONG-HISTORY TEARSHEET`); the data-injected as-of line is
the date of record. A new series (e.g. wealth-planning research) numbers independently
once it has a sibling. Institutional publishers win by being unmistakably consistent, not
clever — the numbering compounds.

**The Exhibits brief — what prospects remember.** The interactive thesis, the After-Tax
Review, the coordination diagrams: these are Driftwood's famous charts, and they get
*more* care than Research, not less. Treat them as **museum exhibits** — not tools, not
graphics, not UI. Observation-first, minimal copy, the interaction does the persuading.

**The Record brief — the moat.** The Record is not "another document family"; it is the
thing no other RIA publishes. **Slow down here — spend twice as long as on any other
family.** It asks a bigger question than consistency: *what makes the Driftwood Record
unlike anything else?* The bar, as questions: Can every document cite another? Can every
decision point to its evidence? Can every research paper point to the decisions it
informed? Can amendments be followed historically? Can a reader understand how Driftwood
thinks *over time*? Pursue the archive mechanics — version history, amendment history,
cross-references, linked decisions ↔ research ↔ exhibits, document relationships. Think
institutional archive, never blog. That becomes genuinely difficult to copy.

**Reading time is an editorial decision.** Every document family has an intentional
reading commitment, not an accidental one: Essays 3–5 min · Research 8–15 min · Records
2–4 min · Reference/Manuals 5–10 min · Tools 30–90 seconds. Audit each page against its
family budget during its pass; a page far over budget is answering two questions (§0.6).
Where it helps a reader commit — the longer documents — the budget may be displayed
quietly ("Research · 12 minute read"); never as chrome on every page.

**Phase B — walk the whole site.** Then stop shipping and *use* the site. Every page, on
desktop, tablet, and phone. This review surfaces the last ~50 small issues and is worth
more than any feature.

**Phase Y — performance & friction audit (experience, not speed).** At this maturity,
friction matters more than new ideas. Walk for: scroll jumps · image-load smoothness ·
typography shifts on load · hover states that all feel identical · consistent transitions
· correct scroll restoration · equally-polished mobile · identical touch targets. Nothing
conceptual ships from this phase — only smoothness.

**Phase Z — cross-document coherence (the last pass before the freeze).** Not editing
pages — walking the *links between* them, until the site is a network rather than a
collection: every page leads naturally to another; every research paper has a related
exhibit; every exhibit points back to research; every tool points back to philosophy;
every philosophy page points to evidence. Readers don't experience pages — they
experience transitions (Home → Operating System → Manual → Decision Register →
After-Tax Review; Research → Thesis → Tax Diagnostic). The test of every transition:
*does the next click feel inevitable?* This is also where quiet "you are here" context
belongs (not breadcrumbs — context: *Understand · Research · After-Tax Wealth
Architecture*), so a reader always knows where they stand inside the publication.

**The cover-to-cover read.** Before declaring the freeze, perform one editorial read of
the whole site as if it went to print tomorrow — ignore templates and code, read every
page in sequence (Home → Our Story → Operating System → Manual → Tax Diagnostic →
After-Tax Review → Research → Home), and flag every moment the illusion of one
institution breaks: repetition, tone, spacing, hierarchy, terminology, navigation, visual
rhythm. It catches what family-by-family passes cannot — the seams that only show when
moving *between* pages. Recommend only changes that strengthen the sense that one
editorial team authored this over years.

**v1 is complete when this is true:** *no page visibly reveals which template generated
it.* Someone should feel they are reading one publication, not traversing page generators.

This remains an editorial systems pass, **not a redesign**. No page loses content; pages
lose repetition.

---

## 12 · The close: a constitution, then a freeze

Before design gravity shifts off the public site, produce one final artifact:

**Public Site Constitution v1** — a single document capturing design principles ·
publishing grammar · identity rules · document families · editorial principles ·
intentional exceptions · version history. It becomes the canonical reference so every
future change is an *amendment to a defined system*, not an ad-hoc improvement.

**The freeze is real.** Written into the Constitution verbatim:

> **Public Site Freeze — v1.** After approval, only the following may change without
> constitutional amendment: research publications · new exhibits · regulatory updates ·
> bug fixes · factual corrections. Everything else requires a deliberate editorial
> review.

Then the center of gravity moves to the **Advisor Workspace**: the flagship, built in a
deliberately different, product design language (dense, purposeful, keyboard-first —
Bloomberg / Foundry / Stripe / Linear, not the editorial museum). Internally it is the
*Coordination Engine*; the client never sees that name, but it changes how it is built.

---

## 13 · Trust calibration — making the institution feel like it already exists

The principal's client's-eye review (July 2026): design is no longer the gap. The
remaining gap is **trust and perceived permanence** — convincing a sophisticated prospect
that this institution already operates. The standing directives, in priority order:

1. **Boutique is a feature.** The site's institutional grammar makes the firm read as 25
   people; the dissonance on discovering otherwise costs trust. Lean in, on the record:
   *"Driftwood is intentionally small. Every household works directly with Alec Messino
   while leveraging institutional research, custodians, and outside specialists when
   appropriate."* (Principal-provided language.) Ship in the human-story pass.
2. **Show the human earlier.** The site teaches, proves, explains — but the person a
   prospect is trusting with $8M appears too late. Move the story up: professional, not
   emotional; why he built this. **Alec is the coordination engine** — the conductor, not
   the software.
3. **Proof of practice, not just proof of thinking.** Nothing builds trust faster than
   documents: an example household followed end-to-end (timeline · estate · portfolio ·
   tax · decision log · annual review), a real meeting agenda, Manual pages, an
   investment-committee memo, a research memo, a withdrawal memo, a transition plan.
   Every sample is fictional and labeled illustrative — that rule is absolute (§0.5·7).
4. **Less "Driftwood."** Institutional writing assumes the publisher — the NYT never
   writes "The New York Times believes." Nav + RIA disclosures legitimately name the firm
   (~6–8 mentions/page); body copy beyond that is audited down in the QA pass. The
   codified heuristic: **if a paragraph still makes sense after deleting "Driftwood,"
   delete "Driftwood."**
5. **Reduce cleverness.** Retire copy that *tries* — "Keep more of what you've earned,"
   "Measure your tax drag," "One place coordination becomes measurable." The rest of the
   site doesn't try; it explains. Quieter rewrites land in each page's family pass.
6. **Institutional memory (the Record pass).** Version history (v1.2 → v1.3 · Amended),
   cross-references (Referenced by · Used in · Superseded by), citations both directions
   (research ↔ decisions ↔ exhibits ↔ manuals). Institutions have memory; show it.
   Three approved components beyond the base design:
   - **Related** — surface the *thinking*, not just the links: a decision lists the
     research, reviews, register entries, and manual sections that bear on it.
   - **Supersedes** — institutions don't just amend; they replace. "Supersedes Decision
     № 11" reads differently from "amended," and the wording matters.
   - **Status** — every archival document carries one: *Current · Amended · Superseded ·
     Archived · Withdrawn · Draft · Historical.* Permanence you can see.
   **The fictional-history guardrail (absolute):** the archive simulates a *client
   archive*, never firm history. `v1.1 → v1.2` works; "March 2022 committee amendment"
   does not — no date may precede what Driftwood can stand behind. All sample dates stay
   inside the current fiction (2026), versions stay shallow, and every page keeps its
   illustrative-sample labeling.
7. **Introduce time.** *Published July 2026 · Revised September 2026 · Last reviewed ·
   Current edition · First published.* Little stamps create permanence. (The taxlab
   exhibit plate's "As of · v1.0 · reviewed quarterly" is the pattern to extend.)
8. **Quiet.** Sometimes the most institutional move is nothing: more whitespace, one
   sentence, then begin.
9. **Make the research harder.** White papers, appendices, methodology, sensitivity
   analysis, references, footnotes — AQR/NBER/Dimensional grade. Not because prospects
   read them; because they'll believe someone else did. (New research stays shippable
   post-freeze by constitution.)
10. **Institutional friction.** Elite firms aren't frictionless. Prefer "Request
    document · Read appendix · View methodology · Continue reading" to giant buttons.
11. **Navigation, eventually.** The identity is institutional; the nav still reads as
    website navigation (Understand / Discover). A publication-style nav (Library ·
    Operating System · Research · Tax Lab · Conversation) is approved *in direction* —
    it is an IA change requiring its own design + review PR, after the passes below.

**The operating roadmap (supersedes the family order alone; reordered July 2026 —
Proof of Practice moves ahead of Tools/QA because its artifacts inform both):**

1. ~~Cases~~ *(merged, #76)*
2. **Record/Reference institutional-memory pass** — design approved: edition lines,
   amendment history, № citations, Draws on / Referenced by / Related / Supersedes /
   Status, archival integrity (frozen mark, one household, consistent 2026 dates).
3. **Proof of practice:** the sample-document shelf — Sample Annual Review · Sample
   Operating Manual · Sample Investment Committee Memo · Sample Decision Register ·
   Sample Transition Plan (all fictional, all labeled).
4. **Tools pass** (leakage · statemap · score), with the cleverness rewrites.
5. **Front-to-back QA pass** (Phases B + Y): consistency, loading rhythm, typography,
   spacing, disclosures, mobile, interaction polish — plus the "less Driftwood" audit.
6. **The human story, earlier + boutique positioning** (principal-provided language).
7. **Public Site Constitution v1**, carrying the freeze rules (§12) and the filter:
   **"The website is not the product. It is the public record of the institution."**
   Every proposed feature is asked: does this belong in the public record, or in the
   operating system? If the latter, it goes to the Advisor Workspace, never the site.
8. **Freeze at v1** and move the center of gravity to the Workspace.
