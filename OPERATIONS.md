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

**Stale sitemap entries (`src/drift/statepage.py::_CORE_SITEMAP`, found 2026-07-26, not yet fixed).**
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

**OPEN — the Review is not yet in the site navigation (Phase 2 item, deliberate).** 50 source pages
carry the `.dwnav--phase2` masthead; only `driftwood-review.html` links the Review, from its own copy
of the dropdown. Propagating it is one line in `scripts/phase2_nav.py` (`("The Driftwood Review",
"driftwood-review.html", "driftwood-review.html")` under *Insights & Research*) followed by
`python3 scripts/phase2_nav.py && python3 scripts/sync_docs.py`. **It was not run, because it forces
an IA decision that should be made deliberately:** *Insights & Research* already holds State Tax
Atlas / Research / Articles / Commentary, and `articles.html` + `insights.html` are already redirect
stubs pointing at `research.html`. Adding a fifth entry makes a crowded menu worse. The real question
is whether the Review *absorbs* Commentary and Articles — a quarterly with a Commentary division is
arguably where that content now belongs — leaving *Insights & Research* as Atlas / Research /
The Driftwood Review. Until that is settled the page is reachable by direct link only.

## Disaster recovery
- **Lost/corrupt `tests/data/matrix_history.json`** → `TILT_SWEEP_REFRESH=1 python scripts/tilt_sweep.py`
  re-pulls and rewrites the cache (needs `TIINGO_API_KEY`); then regenerate STATE_ALPHA (above).
- **Domain**: the site currently serves from `alecmessino.github.io/project/` (canonical/OG URLs point
  there). Moving to a firm domain (e.g. `driftwoodplanning.com`) is a deferred consolidation — update the canonical/OG base in the
  templates + `sitemap.xml`/`robots.txt` and add a 301.
