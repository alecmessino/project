# Driftwood — Greenfield Redesign (2026 concept prototype)

A ground-up redesign of the Driftwood Wealth customer site, built to maximize **trust,
comprehension, and qualified consultation requests**. This directory holds **concept prototypes**,
not production templates. Nothing here has been wired into `src/drift/web/` or `docs/`, and nothing
here should be deployed without the review gates listed at the bottom.

The redesign inverts the site's revealed positioning: proof and coordination move to the front,
the tools are consolidated into one instrument, and every path resolves to one door.

## What's here

```
previews/     Self-contained HTML (fonts + art inlined). Open directly in a browser.
  index.html          The homepage
  the-practice.html   How the engagement runs (the $395k coordination-delta proof)
  the-record.html     The proof-tier archive (9 governance pages consolidated to 3 surfaces)
  tax-atlas.html      Merged State Atlas + Diagnostic (tap a state, math follows)
src/          The same pages as readable templates (placeholder tokens, no inlined blobs)
  gen_engraving.py    Generates the flow-field engravings (limestone/ink, seeded, deterministic)
assets/       The three generated engraving headers (steady / reach / shore)
research/     The evidence and structure behind the build
  evidence-palette.json      Sourced datapoints (cited-public vs illustrative), with compliance flags
  state-tax-data-2025.json   Verified 51-jurisdiction dataset powering the Atlas
  wireframe-the-record.md    Section-by-section wireframe (design-council resolved)
  wireframe-the-practice.md  Section-by-section wireframe (design-council resolved)
```

## Live previews (private artifacts)

- Homepage: https://claude.ai/code/artifact/a674ba89-ca4b-4f21-ad30-a8fbddfe9ef1
- The Practice: https://claude.ai/code/artifact/9722765a-ac64-45af-b366-1f0953d1ee15
- The Record: https://claude.ai/code/artifact/9ab01171-1300-44de-8493-68c548cc10e4
- Tax Atlas: https://claude.ai/code/artifact/fd1339c3-c5f1-445e-b5bd-eda534c77931

## Architecture at a glance

Five identity-phrased nav destinations (no calculator dropdown): **The Firm · The Practice ·
The Record · The Library · Tax Atlas**, plus a quiet **Client Access** utility and one persistent
**Request a Coordination Review** CTA. Every page ends at that single door.

- **Home** leads with thinking, not tools: the "coordination becomes the constraint" hero, the
  counter-positioning line ("we charge to coordinate decisions"), the seven-system lattice, the
  method, the Opportunity Register as live proof, and one invitation.
- **The Practice** promotes the worked example (tumor-board / attending analogy) and re-attributes
  the ~$395,000 Illinois-vs-Texas result to the **coordination delta**, not a lone estate lever.
- **The Record** turns nine overlapping governance pages (~11,000 words) into three surfaces:
  this index, the Opportunity Register, and the Annual Wealth Operating Review. The composite
  Harris household is introduced once. Finding-cards, a dated decision timeline, and an IL/TX
  diptych replace the old wall of documents.
- **Tax Atlas** merges the State Atlas and the Tax Diagnostic. Tapping a state writes to a
  browser-only household profile (`dw.profile` in `localStorage`); the diagnostic below reads it and
  personalizes in place. No form, no gate, nothing transmitted.

## Design system

Reuses the existing Driftwood tokens (limestone `#f1efe9`, slate ink `#1e2833`, editorial blue
`#2c5878`, teal `#15806a` for data only), Satoshi + Erode, square corners, no shadows. Committed to
the single limestone light world (a deliberate letterpress choice, not a missing dark mode).

**Engravings** are generated, not stock: `src/gen_engraving.py` draws seeded flow-field streamlines
in the brand palette. One header per inner page (`steady` = Practice, `reach` = Record,
`shore` = Atlas), so the site reads as one unfolding map. The homepage's four flow-field plates and
the founder headshot are external assets (user-supplied) and are inlined into the previews only.

## Data provenance and corrections

State and advisor-value figures were verified against 2025-2026 sources (Tax Foundation 2025,
IRS/CMS/SSA schedules, OBBBA P.L. 119-21, named studies). Two corrections captured during research:

- The Texas death-tax ban is **2025 Proposition 8** (approved Nov 4 2025), not "Prop 9."
- Washington raised its estate exemption to **~$3M** (mid-2025); Iowa's inheritance tax is fully
  repealed for 2025.

## Compliance gates (do NOT skip before any production use)

This is marketing material for a fee-only RIA under **SEC Marketing Rule 206(4)-1**. Before any of
this ships to `driftwoodwealth.com`:

1. Every figure tagged **Illustrative** (the $395k, the ~$24k fund drag, the $220k charitable
   figure, the ~$30k translation of Vanguard's 3%, all Harris register rows) must be labeled
   hypothetical, carry its assumptions, and **must not** be presented as an actual client result or
   the firm's track record. Enter each in the Evidence Register with a guard and review date.
2. Third-party study figures (Vanguard 3%, Morningstar Gamma / Mind the Gap / tax-cost, Russell,
   the FAJ tax-loss-harvesting study) may be **cited** but never restated as Driftwood-generated
   results. Confirm each source's exact as-of at build.
3. Principal sign-off required on all illustrative figures and all cited study claims.
4. State law changes frequently; the Atlas dataset needs a maintained as-of and a re-verification
   cadence before it is presented as current.
5. Re-lay-out of any performance exhibit (ledger/tearsheet) is a conscious re-signing of the
   existing disclosure posture, not a silent change.

These prototypes keep the illustrative/cited distinction visible on the page (the evidence key on
The Record, the "Illustrative" tags, the sources colophon) precisely so the compliance review has
something honest to sign off on.
