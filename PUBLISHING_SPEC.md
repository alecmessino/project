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

1. Add the spacing tokens + two header partials to `driftwood.css` / `statepage.py`.
2. Normalize page by page, family by family — mechanical, one commit per family.
3. Deliver as **one PR for review** with before/after screenshots per family and the
   exception list. No auto-merge.

This is an editorial systems pass, **not a redesign**. No page loses content; pages
lose repetition.
