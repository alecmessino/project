# scripts/prospecting — Visual Prospecting Automation

Personalized Driftwood "After-Tax Review" tearsheets for outbound sales, rendered with
Playwright from the local site build in `docs/`.

## What it does

`generate_tearsheets.js` reads a CSV of leads and, for each row, renders a **personalized**
After-Tax Review and screenshots it to `outputs/`:

- `outputs/<Prospect_Name>_Driftwood_Analysis.png` — full-page personalized dossier
  (household bar, Asset Location & Capital-Flow, Tax-Drag metrics, Estate cliff, the
  Alpha-Turnover Frontier — all sections revealed in one image). Note: this shot is very
  tall; the two crops below are the share-friendly ones.
- `outputs/<Prospect_Name>_Driftwood_AssetLocation.png` — compact close-up of the
  Asset-Location / Tax-Drag panel (taxable/Traditional/Roth placement, Location Alpha,
  tax saved vs fee).
- `outputs/<Prospect_Name>_Driftwood_Frontier.png` — a focused close-up of the
  Alpha-Turnover Frontier chart (identical for same-state/bracket leads, since it depends
  on tax rates, not portfolio size).

## Which page it drives — and why it is *not* `taxlab.html`

The brief named `docs/taxlab.html`, but that page is the **static public exhibit**: a single
fixed hero chart. It has no state dropdown, no portfolio slider, and no Asset-Location /
Tax-Drag / Alpha-Turnover widgets, so per-lead inputs don't change what it renders.

The interactive tool that owns those controls is **`docs/workspace.html`** (the Advisor
Workspace, `data-page="taxlab"`). It is *explicitly designed for personalized cold-outreach
deep-links* — its own source documents `?view=lead&state=IL&port=2000000`. So this script
targets `workspace.html` by default.

> Run against the static exhibit instead with `PAGE=taxlab.html node …` — it will render the
> same hero image for every lead (no per-lead personalization is possible there).

Personalization is applied two ways for robustness: (1) URL params (`?state=&port=&bracket=`,
the page's designed path), and (2) direct DOM interaction — selecting the state, moving the
portfolio sliders, and opening the frontier. **No files under `src/drift/` or `docs/` are
modified**; only the live DOM is mutated at screenshot time.

## Usage

```bash
npm install                                    # installs playwright-core (already in package.json)
node scripts/prospecting/generate_tearsheets.js
```

Uses the container's bundled Chromium at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`
(same convention as `scripts/og_cards.mjs`). A tiny static server serves `docs/` on a random
localhost port; all non-local requests (analytics, Calendly) are blocked so runs are hermetic.

### CSV format — `austin_leads.csv`

| column | required | notes |
|---|---|---|
| `Name` | yes | used for the output filename |
| `State` | no (default `TX`) | 2-letter code or full name ("Texas") |
| `Portfolio_Size` | yes | `1500000`, `$1,500,000`, `1.5M`, `750k` all parse |
| `Bracket` | no (default `37`) | federal ordinary-rate %, e.g. `37` |

### Config (env vars)

`LEADS_CSV`, `OUT_DIR`, `DOCS_DIR`, `PAGE` (default `workspace.html`), `CHROMIUM_EXE`,
`VW`/`VH` (viewport, default 1440×1024), `DSF` (device scale factor, default 2), `BRACKET`.

## Verified

Run against the two sample leads produces correctly personalized, **distinct** output —
e.g. Asset-Location "Location Alpha" of **+$3.66M** for the $1.5M lead vs **+$5.09M** for the
$5M lead, both TX at the 37% bracket. `outputs/*.png` is gitignored (regenerate on demand).

## A note on `western_springs_signals.md` (gatekeeper research)

The companion "gatekeeper signal" research is scoped to **firm-level center-of-influence (COI)
prospecting from public sources** — CPA firms, estate-planning attorneys, and business-law /
M&A boutiques as referral-network targets. It deliberately does **not** compile a dossier that
profiles named private individuals or families by inferred wealth / "liquidity events," and it
does not use any terms-of-service-violating scraping. See the top of that file for the method
and the boundary.
