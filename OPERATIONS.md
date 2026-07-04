# Driftwood — Operations Runbook

Continuity guide for the Driftwood site. The architecture lives in
`README_DRIFT.md`; the compliance posture in `docs/Structural_Alpha_Methodology.md`. This is the
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
drift export   --source yahoo --config config/drift.yaml --out docs/equities.html
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
   "Driftwood Capital/Advisors" are existing, unrelated financial firms).
2. At the registrar: apex `A` records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
   `185.199.111.153`; `www` CNAME → `alecmessino.github.io`. Wait for DNS to resolve.
3. Repo Settings → Pages → Custom domain = `www.driftwoodplanning.com` (writes `docs/CNAME`) →
   wait for the certificate → check **Enforce HTTPS**.
4. `python scripts/set_domain.py https://www.driftwoodplanning.com` — rewrites the base URL
   everywhere (single source: `src/drift/site.py`); then rebuild
   (`drift states`, `drift hub`, leakage/statemap/taxlab/thesis) + `python scripts/stamp_provenance.py`.
5. `pytest -q tests/test_site_domain.py` must pass (asserts no stale-host references), then commit+push.
6. Re-submit `sitemap.xml` in Google Search Console under the new property.

## Disaster recovery
- **Lost/corrupt `tests/data/matrix_history.json`** → `TILT_SWEEP_REFRESH=1 python scripts/tilt_sweep.py`
  re-pulls and rewrites the cache (needs `TIINGO_API_KEY`); then regenerate STATE_ALPHA (above).
- **Domain**: the site currently serves from `alecmessino.github.io/project/` (canonical/OG URLs point
  there). Moving to a firm domain (e.g. `driftwoodplanning.com`) is a deferred consolidation — update the canonical/OG base in the
  templates + `sitemap.xml`/`robots.txt` and add a 301.
