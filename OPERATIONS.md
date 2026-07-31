# Driftwood — Operations Runbook

Continuity guide for the Driftwood site. The architecture lives in
`src/drift/README.md`; the compliance posture in `docs/Structural_Alpha_Methodology.md`. This is the
**how-to-run-it** so the site survives a maintainer handoff.

## What it is
A static marketing + research site served from `docs/` via **GitHub Pages**, built from
`src/drift/web/*.html` templates by the `drift` CLI. No backend. Leads post to **Web3Forms**; analytics
is **Plausible** (privacy-first); booking is **Calendly**.

## Full local refresh
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Offline-safe (use the committed cache): ledger/tearsheet/equities need market data; the rest do not.
drift ledger   --config config/drift.yaml          # docs/ledger.* (needs data; falls back gracefully)
drift export   --config config/drift.yaml --out docs/equities.html   # projects the ledger; run AFTER drift ledger
drift tearsheet --config config/drift.yaml --out docs/tearsheet.html
drift taxlab   --docs docs --out docs/taxlab.html
drift thesis   --docs docs --out docs/thesis.html
drift leakage  --out docs/leakage.html             # fixed figures, no network
drift statemap --out docs/statemap.html            # static dataset, no network
drift states   --out-dir docs                      # 51 per-state SEO pages + states.html + sitemap.xml
drift hub      --docs docs --out docs/index.html   # reads the other exhibits; run last
python scripts/stamp_provenance.py                 # refresh docs/_provenance.json
```
`driftwood.css` and `docs/fonts/`, `docs/og/`, `favicon.svg`, `robots.txt`, `sitemap.xml` are committed
static assets — the nightly job does NOT regenerate them. Edit `src/drift/web/driftwood.css` and copy it
to `docs/driftwood.css`. Regenerate OG cards with `node scripts/og_cards.mjs` (needs playwright-core +
the bundled Chromium).

## Daily automation
`.github/workflows/drift-pages.yml` runs at 22:20 UTC (after the US close): pulls data via
**Tiingo → Stooq → Yahoo**, rebuilds the exhibits, and commits to `master`; GitHub Pages then deploys.
`.github/workflows/ci.yml` runs `pytest` + `node tests/web/run.js` on every PR.
- Secret: **`TIINGO_API_KEY`** (repo secret). Without it the chain falls back to Stooq/Yahoo (slower,
  occasionally rate-limited on Actions runners). Rotate in repo Settings → Secrets → Actions.

## Interpreting a failed nightly run
1. **Research-flag gate failed** → a shipped config turned on `tilt_overlay`/`lot_protect`. Revert it;
   these are research-only and must never publish (see Compliance gates below).
2. **Data thin / ledger frozen** → Tiingo budget exhausted or a feed outage. The ledger runs first to
   get a fresh budget; the 40y tearsheet runs last so its retry storm can't starve it. Re-run from the
   Actions tab once the feed recovers; exhibits degrade gracefully to the prior snapshot.
3. **`pytest` red on the lineage test** → see "When the performance figures change" below.

## When the performance figures change (annual / on data update)
The headline per-state Tax-Leakage figures are committed in `src/drift/leakage.py` (`STATE_ALPHA`).
To regenerate after a cache update:
```bash
TAX_ALPHA_STATES=1 python scripts/tax_alpha.py        # prints the per-state JSON (re-execs with PYTHONHASHSEED=0)
```
Paste the result into `STATE_ALPHA`, keep the `headline.alpha_low/high` band equal to the representative
states (Federal → IL → NY → CA), then run `pytest tests/test_leakage_alpha_lineage.py`. That test
re-derives the table from the engine and fails if a figure drifts — it is the substantiation guard.

## Compliance gates (all in CI; do not bypass)
- `tests/test_drift_disclosures.py` — every exhibit carries RIA identity + Form ADV/CRS + hypothetical
  language.
- `tests/test_drift_tax.py::test_shipped_configs_keep_research_flags_off` + the drift-pages.yml
  pre-publish step — `tilt_overlay`/`lot_protect` stay OFF.
- `tests/test_leakage_alpha_lineage.py` — published figures still match the engine.
- `tests/test_gtm_copy_lint.py` — no prohibited/unqualified claims in `docs/GTM_*.md`.
- `docs/_provenance.json` — build-time record (commit, data fingerprint, claim→source map) for Rule
  204-2. Git history is the immutable archive.
- **GTM copy** (`docs/GTM_*.md`) is sign-off-gated: no external send without principal review.

## Leads, analytics, booking
- **Web3Forms**: the lead form posts here (key/endpoint in `taxlab.html` CONFIG). To send the prospect
  an instant copy of their analysis, enable the **autoresponder** in the Web3Forms dashboard (the form
  already submits their email). The on-page success card already delivers the figures + Calendly link.
- **Plausible**: loaded on every page. Custom funnel events fired via `track()` /
  `window.plausible(...)`: `state_selected`, `portfolio_adjusted`, `lead_submitted`, `lead_error`,
  `booking_opened`, `booking_scheduled` (taxlab); `map_state_clicked` (statemap);
  `diagnostic_to_taxlab` (leakage). `booking_scheduled` is the true conversion.
- **Calendly**: the success-card iframe; `booking_*` events come from its postMessage API.
- **State landing pages** (`<slug>-tax.html`, e.g. `california-tax.html`): 51 server-rendered SEO
  pages built by `drift states` from `statepage.py`. Each carries an inline Web3Forms email capture
  (`source:"state_page"`, tagged with the state + a lead-quality flag) so organic traffic converts in
  place, plus a CTA into `leakage.html?state=XX`. Regenerate after any `STATE_ALPHA`/`statemap.py`
  change; refresh the share cards with `node scripts/og_states.mjs`.

## Moving to the custom domain (driftwoodplanning.com — or whichever is purchased)
The full site hosts on the domain via GitHub Pages (same repo, same deploy; the site serves at the
domain ROOT, no `/project/` subpath; github.io URLs auto-redirect). **Sequence matters — do not flip
canonicals before DNS is live:**
1. Purchase the domain (verify a trademark screen first: "Driftwood Wealth Partners" and
   "Driftwood Wealth/Advisors" are existing, unrelated financial firms).
2. At the registrar: apex `A` records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
   `185.199.111.153`; `www` CNAME → `alecmessino.github.io`. Wait for DNS to resolve.
3. Repo Settings → Pages → Custom domain = `www.driftwoodplanning.com` (writes `docs/CNAME`) →
   wait for the certificate → check **Enforce HTTPS**.
4. `python scripts/set_domain.py https://www.driftwoodplanning.com` — rewrites the base URL
   everywhere (single source: `src/drift/site.py`); then rebuild
   (`drift states`, `drift hub`, leakage/statemap/taxlab/thesis) + `python scripts/stamp_provenance.py`.
5. `pytest -q tests/test_site_domain.py` must pass (asserts no stale-host references), then commit+push.
6. Re-submit `sitemap.xml` in Google Search Console under the new property.

## 2026 redesign — decisions & Phase 2 backlog

**The four-plate homepage (decided and executed 2026-07-29).** `hub.html` is now a folio of four
plates: **I The Constraint** ("Uncoordinated decisions leak what you keep") → **II The Coordination
Engine** (the seven-node lattice, carried over unchanged) → **III Governance Register** → **IV The
Ask**, reversed to ink. Three sections were removed because each answered a question another plate
already answered, not because the page was long: a six-condition self-audit (duplicated the hero's
recognition beat), a standalone dollar band, and the four-step capability sheet. Page height fell from
~6,160px to ~4,000px as a byproduct.
- **The capability path moved, it was not deleted.** Diagnose → Measure → Coordinate → Manage now
  lives on `the-practice.html` as section III, where "how the work runs" is the page's actual subject.
  `tests/test_drift_hub.py::test_capability_sequence_lives_on_the_practice_not_the_homepage` was
  **retargeted, not relaxed**: it still pins all four verbs, their order, and `id="capabilities"`, and
  it additionally bars the homepage from growing a second copy.
- **The register's dollar column is gone.** "Potential" (≈$14,800/yr and siblings) became "Next
  review" (a date). Those figures were the top UNSOURCED rows in `FIGURE_PROVENANCE.md`; a review date
  proves the matter is *carried*, which is the actual claim, and needs no model behind it.
- The resolved-row floor (≥25%, below) is met: two of eight rows are resolved-and-dated.

**Six Systems vs. Seven Systems — resolved (2026-07-29).** The nav taught "Six Systems" while the
homepage lattice, `coordination-framework.html`, and the Coordination Engine all teach **seven**
(Investments, Taxes, Cash Flow, Estate, Protection, Business Ownership, Family / Purpose).
`six-systems.html` was a content-free stub whose own meta description enumerated six, omitting
Business Ownership. **Seven is canonical.** The nav entry is now "The Seven Systems" pointing at
`coordination-framework.html` (which actually enumerates them, and was orphaned until this change);
`six-systems.html` is a redirect stub. The label lives in `scripts/phase2_nav.py::FAMILIES`, which was
fixed too, so re-running the generator cannot reintroduce it.

**Statemap vs. Tax Atlas — consolidated (decided 2026-07-26, executed same day).** The 2026 redesign
briefly introduced `tax-atlas.html`, a single-ink-ramp, 3-toggle state comparison map on the new
`driftwood.css` design system. It shipped alongside `statemap.html` for one day; the two-Atlas state
was never meant to be permanent (see the original entry this replaces, in git history). Consolidated
same-day: `statemap.html` is the one canonical Atlas — `tax-atlas.html` is now a redirect stub
(`meta refresh` + `canonical`, same pattern as `howitworks.html`/`record.html`). Reasoning unchanged:
`statemap.html` is the live, Python-computed engine (`drift statemap`, `src/drift/statemap.py`),
carries 6 dedicated tests (`tests/test_drift_statemap.py`, including citation and no-fabricated-alpha
guards), and is load-bearing in the funnel. `tax-atlas.html` had no independent data engine of its
own and its simpler 3-toggle/income-drag view had no equivalent on `statemap.html` — that view is
retired, not preserved, an accepted cost of one comprehensive Atlas over two partial ones.
- Wordmark unified site-wide first (see the mandate below), so `statemap.html`'s nav/footer already
  read on-brand before the redirect landed — no separate "shell" reskin of its dense 8-tab/cartogram
  layout was needed beyond that. All inbound links (`hub.html`, `taxlab.html`, `the-practice.html`,
  `the-record.html`, `dw-context.js` SIBLINGS/CONSUMERS) repointed to `statemap.html` directly, not
  left to redirect through the stub.

**Figure provenance (standing mandate, 2026-07-26).** Every public dollar/percent figure on the site
must have a row in `FIGURE_PROVENANCE.md` (repo root) classifying it DERIVED / ASSUMED / UNSOURCED.
No new public figure ships without an entry. See that file for the current audit and open
UNSOURCED items.

**Resolved-row ratio on the homepage sample register (standing design rule, 2026-07-26).** The
"Coordination, kept in one register" table (`hub.html`) mixes open/monitoring/time-sensitive matters
with resolved-and-dated ones ("Resolved ✓ · Driftwood · Mar 2026"). A resolved, dated row is the most
trust-building row type on the page — it proves the register produces outcomes, not just promises —
so **keep resolved-and-dated rows at ≥25% of the sample register.** **Met as of 2026-07-29:** the
Plate III register is 8 rows / 2 resolved-and-dated (25%). The earlier concern (that raising the ratio
would require inventing a dollar figure) dissolved when the dollar column was replaced by "Next
review" — a resolved row now carries a close date rather than a captured amount, so the floor can be
held without any un-derived number.

**Sitemap — audited and fixed 2026-07-31** (the 2026-07-26 backlog item below is now closed).
Removed: `library.html`, `familyoffice.html` (deleted in `3caa0d6c`, 404 live), `howitworks.html`,
`record.html` (noindex redirect stubs), and `states.html` (a sentinel that was only ever filtered out
and replaced by the edition index — its presence made the list read as if the flat alias were being
announced). Added: `insights.html`, `driftwood-review.html`, `commentary.html`,
`coordination-framework.html`, `the-practice.html`, `the-record.html`, and the seven masthead
destinations that were missing. `tests/test_drift_sitemap_core.py` now enforces the standing rule —
**anything in the primary navigation is in the sitemap, and nothing in the sitemap is a redirect stub
or noindex** — so the next Insights-shaped omission fails rather than ships.

Two things that audit surfaced:
- **`partners.html` was `noindex`** while sitting in the masthead on 51 pages, carrying a
  self-referential canonical and a search-written description. Nothing documented the directive and
  no test asserted it; it read as a leftover from when the page was a draft, and was removed.
- **OPEN — `partners.html` and `cpa-collab.html` overlap.** "For CPAs, Attorneys & Advisors" and
  "For CPAs & Estate Attorneys" are near-duplicates; the masthead links the first, the second is
  reachable only by URL. Not resolved here (it is an IA call, not a bug): either fold `cpa-collab`
  into `partners` with a redirect, or give them genuinely different jobs.

**Stale sitemap entries (`src/drift/statepage.py::_CORE_SITEMAP`, found 2026-07-26, FIXED 2026-07-31 — see above).**
Four problems, same root cause (the list wasn't updated as pages were added/retired):
- `library.html`, `familyoffice.html` — 404 on the live site (deleted in `3caa0d6c`, predates the
  2026 redesign).
- `howitworks.html`, `record.html` — now `noindex, follow` redirect stubs (2026-07 blocker-2 fix);
  should be dropped from the sitemap, not just left to redirect out.
- `tax-atlas.html` — never added (was never in the sitemap to begin with; now moot, it's also a
  redirect stub as of the statemap consolidation below).
- `the-practice.html`, `the-record.html` — real, canonical, live pages, missing from the sitemap
  entirely.
**Phase 2 item:** rewrite `_CORE_SITEMAP` (remove the four stale/stub entries, add the two missing
live ones), regenerate `docs/sitemap.xml` via `drift states`, resubmit in Google Search Console.

**The Driftwood Review — publication template (built 2026-07-30, `driftwood-review.html`).** A
quarterly institutional publication whose credibility rests on being visibly *fixed*. Four decisions
worth keeping:

- **Seven divisions, unalterable order** (Lead Essay → Research Notes → Tax & Planning → Market
  Structure → Practice Updates → Reading List → Appendix). A division may be thin in a quarter; it is
  not reordered or dropped. The order lives in `tests/test_drift_review.py::DIVISIONS`, which is the
  specification — changing the page without changing that tuple fails.
- **Ten canonical survey plates, closed library** (`src/drift/plates.py`, rendered by
  `scripts/build_plates.py` into `src/drift/web/img/plates/`). An article is assigned the plate whose
  *structure* matches its subject; it never gets bespoke art. The plates are generated, not cropped
  from `img/survey-plate-hero.svg` — that was tried and rejected, because the master plate is a single
  confluence, so ten crops would be ten pictures of the same structure wearing ten names. They are
  generated in the master plates' hand (same ink `#1E2833`, same sounding radii 0.75/0.85/1.3).
- **Density is a property of the article, not the plate.** `data-type="research|commentary|household"`
  on a card sets CSS custom properties that cross the `<use>` shadow boundary into the plate geometry
  — the one thing that does. That is why ten files serve three disciplines without duplicating a
  coordinate. Verified empirically in a browser before the architecture was committed.
- **The Review publishes no dollar or percentage figure**, test-guarded
  (`test_the_issue_publishes_no_dollar_or_percentage_figure`). It *links* to figures; it does not
  restate them, so it adds no rows to FIGURE_PROVENANCE.md. A recurring publication is exactly where
  an unsourced number would otherwise accumulate quietly. The plates carry no data either — no axis,
  no scale, no legend — and that is guarded too.

Regenerating: edit `src/drift/plates.py` → `python3 scripts/build_plates.py` → commit the SVGs →
`python3 scripts/sync_docs.py`. The generator is deterministic (local LCG, no `random`, no clock), so
a run with no source change leaves an empty diff; a surprise diff means the geometry moved.

## Information architecture — settled 2026-07-31

Decided from what Driftwood publishes in **three to five years**, not from what the repo contains
today. That is the whole rationale, and it is why the menu does not mirror the file system.

**Primary navigation is five families and two actions, and that is all:** Our Firm · Coordination ·
Insights · Professionals · Client Access · Request a Coordination Review. Guarded by
`tests/test_drift_insights_ia.py`, which fails if a sixth family appears on any page.

**"Insights & Research" → "Insights".** *Research* is one division inside the set; it cannot also
name the set that contains it. Once the practice publishes papers, commentary, a quarterly, decision
memos and a shelf of interactive tools, "Research" is too narrow to be the label.

**Inside Insights, five divisions, in this order:**

| Division | Destination | What it holds |
|---|---|---|
| Research | `research.html` | papers, essays, the exhibits behind them |
| Commentary | `commentary.html` | short notes, published when there's something to say |
| The Driftwood Review | `driftwood-review.html` | the quarterly — the flagship |
| Decision Tools | `insights.html#decision-tools` | State Tax Atlas · Tax Diagnostic · After-Tax Review · Concentrated Position Navigator |
| Decision Library | `insights.html#decision-library` | eight worked household decisions |

**Commentary is NOT absorbed by the Review, and that is deliberate.** The two were considered for
merging and the answer is no: they are different publishing *rhythms*, and collapsing them would
cost both. Keep the distinction sharp when writing:

| | Research | Commentary | The Driftwood Review |
|---|---|---|---|
| **Job** | evidence, papers, frameworks | thinking out loud | synthesis |
| **Cadence** | evergreen | weekly-ish, as things happen | quarterly |
| **Length** | long | 300–800 words | long-form |
| **Register** | reference | reaction, observation | what mattered, why, what's changing |
| **Lifespan** | permanent | current | archival |

A quarterly that also absorbs every short note stops being something readers look forward to. The
model is a memo series, not a blog with a fancy wrapper.

**RESERVED — Decision Memos (a sixth division, not built).** It slots between The Driftwood Review
and Decision Tools:

```
Insights
├── Research
├── Commentary
├── The Driftwood Review
├── Decision Memos      ← reserved
├── Decision Tools
└── Decision Library
```

It bridges evergreen research and short commentary, and it maps onto Driftwood's core idea directly:
one decision, many downstream consequences — closer to Federal Reserve working notes than to
commentary. **Deliberately not in the masthead yet:** a menu entry with nothing behind it is the
exact defect this repo has already shipped twice (nav items that 404'd; an "Articles" entry that
round-tripped to a sibling). The category is reserved here, in writing, and enters the nav in the
same commit as its first memo — one row added to `FAMILIES` in `scripts/phase2_nav.py` and to
`INSIGHTS_CHILDREN` in `tests/test_drift_insights_ia.py`, which are the only two places the IA is
defined.

**Articles was retired from the navigation.** It named a *format*, not a subject, and formats do
not deserve navigation. It also pointed at `insights.html`, which was a `noindex` redirect stub back
to `research.html` — a sibling entry in the same menu — so the slot round-tripped the reader.
`articles.html` still exists at its URL; it is simply not in the masthead.

**`insights.html` is now the editorial landing page**, indexable, self-canonical, no longer a stub.
Decision Tools and Decision Library are **sections on it** rather than separate pages: each is a list
of links today, and two thin pages read worse than two populated sections. They graduate to
standalone pages when they outgrow it — at which point the two masthead hrefs change from
`insights.html#…` to the new files and `test_every_insights_entry_resolves_to_a_built_page` keeps
the menu honest through the move.

**"Coordination Library" → "Decision Library"** across all nine pages that used it. The old label
linked to `research.html`, which has no library section on it — the shelf named a place that did not
exist. The Research hub's own "Library" card also pointed at `research.html` (i.e. at itself); it now
points at the shelf.

**`concentration.html` is the Concentrated Position Navigator.** It previously had no product name —
it was an article headline ("How to de-risk a concentrated stock position") filed under a "Research"
eyebrow, so nothing was renamed; it was *named*. "Navigator" over "Playbook" is a real distinction:
a playbook instructs, and the page does not instruct — it helps someone navigate tradeoffs.

### Naming rule: "Review" belongs to the engagement, and to nothing else

**Coordination Review is the product.** Every free artifact takes a different noun so nothing on the
site competes with the thing a visitor is meant to book. **"Lab" is the default suffix for new
tools** — one suffix scales; six competing metaphors (Navigator / Planner / Explorer / Framework /
Diagnostic) do not.

| Noun | Means | Shipped |
|---|---|---|
| **Review** | *the engagement* — RESERVED | Coordination Review |
| **Atlas** | reference / lookup | State Tax Atlas |
| **Lab** | interactive analysis — the default | After-Tax Lab · Concentrated Position Lab |
| **Diagnostic** | finds what is wrong | Tax Diagnostic |

Also permitted to carry "Review": **The Driftwood Review** (the quarterly publication) and the
**Annual Wealth Operating Review** (the client deliverable the engagement produces), plus their
ordinary short forms in prose. `tests/test_naming_convention.py` enforces the rest, and normalises
whitespace before matching — the first rename pass was a literal string replace and silently missed
a link label broken across a line (`<a>After-Tax\n Review</a>`) on a nav-linked page.

**Renames applied 2026-07-31.** After-Tax Review → **After-Tax Lab**; Concentrated Position
Navigator → **Concentrated Position Lab**. The collision was not theoretical: `taxlab.html` carried
a button reading *"Request a Private After-Tax Review"* pointing at `coordination-review.html`, and
sat in the Coordination dropdown directly above *"Schedule a Coordination Review"*. That button now
reads "Request a Coordination Review".

**Decision Tools roadmap (NOT advertised until built).** Business Exit Lab · Equity Compensation Lab
· Roth Conversion Lab · Estate Readiness Lab · Household Liquidity Lab · Charitable Giving Lab.
`test_the_tools_advertised_are_only_the_ones_that_exist` fails if any reaches the shelf before its
page does.

**OPEN — "Tax Diagnostic" is the last tool outside the convention.** It does not collide with
anything, and "Diagnostic" is an honest description of what it does (it finds the leak; the Lab
measures the fix). Left as-is deliberately, but flagged: if the shelf should be *uniformly* Atlas +
Lab, this is the one to change, and **After-Tax Lab** / **Tax Diagnostic** sitting adjacent is the
place a visitor would notice the inconsistency first.

### The editorial taxonomy

Every piece of content has one job. Written down so a new piece gets filed rather than invented.

| Type | Purpose | Length | Frequency |
|---|---|---|---|
| Commentary | timely observations | 300–700 words | weekly |
| Essays | evergreen ideas | 1,000–2,500 words | monthly |
| Research | original work | 10–40 pages | occasionally |
| Decision Memo | single decision walkthrough | 2–4 pages | as needed *(category reserved, not built)* |
| Decision Library | evergreen decision reference | living | continuous |
| Decision Tool | interactive | living | continuous |
| The Driftwood Review | quarterly publication | 20–40 pages | quarterly |

**Commentary stays small on purpose** — 300–700 words, one observation, one idea. Closer to a
personal blog than a briefing digest. That is what makes weekly publishing survivable, and it is
why the Review does not absorb it (see the rhythm table above).

## The homepage lattice — the Brief-5 handoff README is superseded (2026-07-31)

The Brief-5 design-handoff README specified a **static** lattice: no interaction, no hover, no
animation, all twenty-one edges equal graphite. The implementation that emerged is interactive,
carries derived two-tier edge weights, and publishes five decision traces. **The decision is to keep
the implementation and treat that README as historical.** The difference is not cosmetic: the static
version *illustrates* the claim "seven systems, no decision touches just one"; the live version
*demonstrates* it — a visitor picks a decision and watches six systems move. Documentation follows
the product.

Canonical, and pinned in `tests/test_hub_lattice_decisions.py`:

- **Seven systems.** No eighth node — K8 puts four diameters through the centre, straight through
  the hub label.
- **Five decision traces**, each touching ≥5 systems. The most important interaction on the page.
- **Seven spokes** centre-to-rim, the only bold figure on the plate, and a centre that is lit at all
  times. Coordination is drawn, not asserted. See the 2026-08-01 note below.
- **Two-tier edges** — structural vs situational, *derived* from the published traces
  (`tests/test_hub_lattice_weights.py`), not asserted. This is what makes the diagram read as
  researched rather than drawn. Narrowed to a whisper at rest on 2026-08-01 so the spokes could
  carry the emphasis alone; derivation and class unchanged.
- **Graphite rest state, one blue accent**, no second hue, tokens only (no hardcoded hex).
- **Interaction retained** — explanatory, not decorative — and `prefers-reduced-motion` honoured.

### The spokes, and what they cost the structural tier (2026-08-01)

The lattice had drawn twenty-one dependencies among seven systems and **nothing touching the
centre**. COORDINATION was a floating word — the page's entire thesis was the one relation the
diagram declined to draw. Seven spokes now run centre-to-rim, and they are the only bold figure on
the plate. The centre also rests in ink permanently (it used to sit at `--muted` until a trace lit
it, so a visitor who never interacted saw the hub as the *faintest* mark in a drawing built to say
the hub is where everything meets).

This revises an earlier decision and the revision should be visible rather than quiet. **Two
emphasised figures cannot share one diagram** — that is the failure this lattice has now shipped
three times, most recently as six accented chords painting a lopsided quadrilateral across a regular
heptagon. With the spokes at full weight, keeping the structural six at their previous `.58/1.2`
reproduced it exactly. So the rim dropped back to a quiet mesh.

The derived structural tier is **narrowed, not deleted**: the six edges keep their class, keep their
derivation from the published traces, and keep a real weight difference (`0.9` vs `0.5`, still the
1.8× the tier guard requires). It is a whisper at rest — legible when the eye settles on the rim,
invisible while the eye reads the figure as a whole. The claim survives; it stopped fighting the
geometry.

The rest caption moved with the encoding. It read *"the heavier lines are the ones that move in all
of them"*, which decoded the rim tier; the heavy lines are the spokes now, so a caption left alone
would have been actively pointing at the wrong marks. `test_the_caption_decodes_the_spokes_it_now_describes`
fails if the two drift apart again.

**Already correct, and worth recording as such:** the requested hover behaviour — a system and its
direct dependencies in the accent, everything unrelated dropped back — was already implemented in
`show(i)` and needed no change. Verified in-browser, not inferred.

**No survey plate behind the lattice (removed 2026-07-31).** A hydrographic engraving used to sit
under the diagram at 5% opacity as "ground texture". It was decoration competing with an argument —
every stray mark behind the lattice is noise a reader must subtract before the seven nodes and the
structural six resolve. Removing it also made the ghosted *situational* edges legible, which the
texture had been masking. The 907 KB source asset was deleted with it.

**Where the survey vocabulary is allowed** (standing rule, so the plates stop creeping):

| Allowed | Not allowed |
|---|---|
| publications & articles — the Review's card fragments | diagrams that carry a claim (the lattice, the coordination surface) |
| page furniture — hero and footer plates | wayfinding & directory pages (Insights) |
| | anything where the plate is texture rather than content |

The Insights landing page had grown a plate band under every section head and an art panel beside
the Review; both were removed the same day. A directory is a page someone uses to *find* something,
and the plates slowed that down while spending the vocabulary on a page that makes no argument. It
is carried by type, rule, and space. Guarded by `tests/test_survey_plate_scope.py`.

**One correction taken from the review: the hub reads COORDINATION, not GOVERNANCE.** Governance is
the operating principle the practice runs *by*, not one of the things being coordinated; putting it
at the centre of the systems diagram quietly promoted it to an eighth system. It keeps its own home
in **Plate III, the Governance Register**, where it belongs as a standing process.

## Next: evidence and conversion, not layout (agreed 2026-07-31)

The architecture is settled — one frame, one masthead position, one naming convention, an IA that
holds. Further visual refinement has low marginal value. The remaining leverage is proof and funnel,
in this order.

**1. Decision Memos — SHIPPED 2026-08-01.** The category reserved on 2026-07-31 is now live, with
the rule honoured: it entered the masthead in the same commit as its first entry, never before it.

**The overlap check answered the open question, and changed the build.** `ic-memo.html` was already a
decision memo — Harris household, front matter, alternatives weighed, recorded as DR-003 — filed
under an investment-only name. So the shelf launched with **two** entries rather than one new page
duplicating an old one. The distinction that survived the check:

| | Decision Library | Decision Memo |
|---|---|---|
| **Answers** | what happens when a household does X | what we thought, and when |
| **Reader** | has not decided yet | wants the reasoning behind a decision already taken |
| **Tense** | evergreen | dated and attributed |
| **Carries** | the systems a situation touches | alternatives rejected · assumptions · reopening trigger |
| **Is** | a reference | evidence |

**The first memo is `decision-memo-domicile.html` (DM 2026-01 → DR-002)**, deliberately *not* an
investment decision — establish residency before sequencing a business sale, or after. `ic-memo.html`
on its own left the impression that Driftwood writes memos about portfolios; between them the two
show the format is about decisions, not asset classes.

It adds one section the IC memo does not have: **§ VI, what the decision set in motion** — DR-004's
conversion window exists only because this sequencing holds, and DR-005 is deferred until the sale
terms it gates are set. That is the coordination claim made concrete inside a single artifact rather
than asserted on a landing page, and it is the section to keep when writing the next memo.

**It publishes no dollar or percentage figure**, so it adds no FIGURE_PROVENANCE row. Every claim is
about order, exposure and substantiation, which is what the decision actually turned on. A memo is
precisely where an illustrative number would look authoritative and be unsourced.

Writing the next one: `tests/test_decision_memo.py` runs against every entry in `MEMOS` — add the
filename there and the guards (dateline, register entry, ≥2 rejected alternatives, disclosure) apply
automatically. Good candidates left on the Harris record: DR-005 (gifting held pending the sale — a
memo about *deferring* as a decision) and DR-001 (the ILIT — an estate decision, widening the range
again).

**2. Tax Diagnostic → Coordination Review handoff.** The highest-value funnel. Current state on
`leakage.html`: the **primary** button opens the After-Tax Lab (another free tool) and the booking
link is the secondary "or book a 15-minute introductory call". That is a legitimate
progressive-commitment ladder — Diagnostic → Lab → Review — but it means the Diagnostic's strongest
call to action spends the click on a second calculator. **Not flipped, deliberately:** which
ordering converts better is a question to measure, and inverting it on instinct would contradict
item 4. Instrument first (`diagnostic_to_taxlab` already fires; `booking_opened` /
`booking_scheduled` are the outcome), then decide.

**3. Research integration.** The working papers should reinforce the commercial narrative rather
than interrupt it — each Research entry ending in the decision it informs, not in a bibliography.

**4. Homepage CTA measurement.** Baseline the current flow before any further structural change.
`booking_scheduled` is the true conversion; everything upstream is a proxy.

## Disaster recovery
- **Lost/corrupt `tests/data/matrix_history.json`** → `TILT_SWEEP_REFRESH=1 python scripts/tilt_sweep.py`
  re-pulls and rewrites the cache (needs `TIINGO_API_KEY`); then regenerate STATE_ALPHA (above).
- **Domain**: the site currently serves from `alecmessino.github.io/project/` (canonical/OG URLs point
  there). Moving to a firm domain (e.g. `driftwoodplanning.com`) is a deferred consolidation — update the canonical/OG base in the
  templates + `sitemap.xml`/`robots.txt` and add a 301.
