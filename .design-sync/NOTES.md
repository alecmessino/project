# design-sync notes — Driftwood

## Critical: this repo is NOT the source of the Driftwood Design System project
- Target project: **Driftwood Design System** (`230c9097-1a5c-4f53-be2c-12858f7096b2`), owner Alec, `PROJECT_TYPE_DESIGN_SYSTEM`.
- That project is a full, hand-curated React design system: `components/*` (Button, DWNav, HeroNumber, PullQuote, EmailCapture, …) with real `.jsx`/`.d.ts`/`.prompt.md`, `ui_kits/website/*` screens (Home/Atlas/Diagnostic/Review), `tokens/*.css`, `guidelines/*`, `templates/*`. **None of it is generated from this repo** — this repo is a Python static-site generator with no React components.
- Its `tokens/colors.css` already carries the July-2026 rebrand (matches this repo's `driftwood.css` `:root`).

## What a sync from THIS repo may do
- **Reference refresh only.** Overwrite `reference/*` (the mirror of the shipped site) from this repo's current `docs/`: `reference/driftwood.css` ← `docs/driftwood.css`, `reference/dw-context.js`, and the page copies. That is the sole safe, additive update.
- **NEVER full-sync / never run the converter here.** There is no JS component library / `dist` / Storybook; a converter run finds nothing (`[ZERO_MATCH]`), and a full-plan upload would DELETE the curated React components. The design-sync converter path does not apply to this repo.
- Do **not** overwrite `tokens/`, `components/`, `guidelines/`, `templates/`, `ui_kits/` — curated DS artifacts, authored outside this repo, already current.
- `reference/report.html` exists in the project but has no `docs/` source anymore — leave it.

## Re-sync risks
- If a future run "creates a new project," it will collide on the name and duplicate a superior existing system — always re-adopt `230c9097` and refresh `reference/` only.
- The project was authored WITHOUT the design-sync converter (no `_ds_sync.json` anchor; component cards use a `<group>.card.html` convention, not per-component `@dsCard`). Do not write `_ds_needs_recompile`/`_ds_sync.json` for a reference-only refresh — it could disturb the curated `_ds_manifest.json`.
