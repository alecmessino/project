# Driftwood Platform Architecture (v1)

A technical reference for the Driftwood **wealth-coordination platform** — the `drift` package and the
Atlas that renders on it. This is not marketing copy; it is the map a maintainer or collaborator reads
before touching the system, so corrections happen **once** and the architecture does not drift.

The platform is three layers. Everything derives from the first two.

```
Layer 1 · FACTS        canonical, cited, editioned   →  drift.state_facts, drift.leakage, drift.statemap
        ↓
Layer 2 · REASONING    a graph of structured objects →  drift.reasoning, drift.atlas
        ↓
Layer 3 · PRODUCTS     queries over the graph, rendered many ways
                       →  Atlas state pages (drift.statepage), Tax Diagnostic (drift.leakage → leakage.html),
                          Advisor Workspace (drift.taxlab), Comparison (drift.compare), Crossing Brief (drift.crossing), Household Record (drift.household)
```

**The one rule that makes it a platform:** a fact is authored once (Layer 1), reasoning about it exists
once (Layer 2), and products (Layer 3) *ask questions of the graph* — they do not embed business rules
or restate facts. Add intelligence to the graph, not to a product.

---

## Layer 1 · Facts

Canonical, primary-source-cited, versioned by tax-year **edition**. No fact is authored in two places.

| Module | Owns | Notes |
|---|---|---|
| `drift.state_facts` | `RATES` (top-effective LT/ST cap-gains rate per jurisdiction), `ESTATE` (regime · rate · exemption · cliff · note), `TERRITORY_CODES`, `IL_AG_CURVE`; `rate_display()`; `RATE_SOURCES` / `ESTATE_SOURCES` (per-state reconciliation records) | **The single source of truth** for tax + estate facts. `tax.STATE_RATES` and the Atlas display both project from `RATES`; `statemap`, `taxlab`, and the workspace JS all project estate facts from `ESTATE`. |
| `drift.leakage` | `STATE_NAMES` (code ↔ name), `STATE_ALPHA` (the illustrative Tax-Diagnostic figure per state), `build_leakage()` | `STATE_ALPHA` is a **derived** committed artifact — regenerated from `RATES` by `scripts/tax_alpha.py` (`PYTHONHASHSEED=0`), guarded by `tests/test_leakage_alpha_lineage.py`. |
| `drift.tax` | `STATE_RATES = {c: RATES[c]}` minus territories | The after-tax calculator's view of the canonical rates. |
| `drift.statemap` | the 7 environment **dimensions** (`_INCOME` regime+quirk, `_MARRIAGE`, `_ESTATE`→projects `ESTATE`, `_STEPUP`, `_MUNI`, `_QSBS`, `_LOSS`), `_CITATIONS`, `EDITIONS`, `CURRENT_EDITION`, `_state_record(code)`, `build_statemap(edition)` | `_state_record(code)` is the **environment record**: `{dim: {regime, tag, note, source, citation?}}` for `cg / marriage / estate / muni / qsbs / loss / stepup / alpha`. |

**Provenance.** Every reconciled value carries an authority + URL + effective date (`RATE_SOURCES`,
`ESTATE_SOURCES`, `_CITATIONS`), recorded in `RECONCILIATION_LOG.md` and asserted by
`tests/test_drift_atlas.py`. The dimensions expose `citation` links that the reasoning layer traverses.

**Single-source config.** `drift.site` owns `BASE_URL`, `CONTACT_EMAIL`, `BOOKING_URL`, and the firm
identity object; flip with `scripts/set_domain.py` / `scripts/set_contact.py` (string-replace across
templates, generators, and `docs/`, guarded by `tests/test_site_domain.py` / `test_correspondence.py`).

---

## Layer 2 · The Reasoning Graph

`drift.reasoning` turns facts into **decision architecture**. It is a graph, not a chain: each node is an
addressable, structured object with typed reference edges. Presentation order is
`environment → impact → decision framework → coordination priorities → actions` (the Decision Framework
is the centrepiece), but the storage is a graph any consumer — page, report, AI — can traverse.

**Primitives** (canonical, state-independent definitions, addressable by id):

- `FRAMEWORK_SIGNALS` — the Decision Framework lenses (`rate_pressure`, `estate_exposure`,
  `harvest_leverage`, `mobility_value`, `basis_coordination`). Each `reads` environment dimensions,
  `evaluate`s to a `level` (`none…severe`) + `reading`, and `opens` a coordination priority.
- `COORDINATION_PRIORITIES` — the household coordination domains (Residency, Estate, Portfolio). Each has
  a `trigger` (a signal at a minimum level), `related_signals`, `related_actions`, `affected_dimensions`,
  and a `priority` rank.
- `ACTIONS` — the sequenced register. Each `references` a priority and carries `related_signals`.
- `SIGNAL_BY_ID` / `PRIORITY_BY_ID` / `ACTION_BY_ID` — registries: every primitive is addressable.

**Instantiation.** `reasoning.build_reasoning(code, environment)` binds the primitives to one state's
environment and returns the per-state graph — structured nodes with a stable `node_id`
(`"IL:signal:estate_exposure"`) and traversed `citations` (pulled from the dimensions a node reads, an
edge to Layer 1). `drift.atlas.build_state_edition(code, edition)` composes the full record:
`{code, edition, name, environment, impact, framework, coordination, actions}`. `atlas.CHAIN` fixes the
presentation order; `atlas.build_edition(edition)` builds the whole Atlas for one edition.

Primitives are **organised from existing approved Driftwood thinking** (the dimensions, the Tax
Diagnostic, the State Context, the Moving States ripple, the coordination philosophy). Adding reasoning
means adding a primitive here — never prose in a product.

---

## Layer 3 · Products

A product is a **thin query over the graph** rendered for a context. It asks the graph a question; it
does not own intelligence.

| Product | Question it asks the graph | Status · surface |
|---|---|---|
| **Atlas state page** | render this state's full reasoning chain | live · `drift.statepage` → `/atlas/{edition}/{state}/` |
| **Tax Diagnostic** | what is *this household's* after-tax impact here? | live · `drift.leakage` → `leakage.html?state=` |
| **Advisor Workspace** | estate / Roth / asset-location tooling | live · `drift.taxlab` → `workspace.html` |
| **Comparison** | which framework signals differ, and which coordination priorities change, between two states? | live · `drift.compare` / `drift.comparepage` → `/atlas/{edition}/compare/` (instrument) + `/compare/<a>-vs-<b>/` (corridors) |
| **Crossing Brief** | what must a household change *because it is moving* — the directional operating memo | live · `drift.crossing` / `drift.crossingpage` → `/atlas/{edition}/crossing/` + `/crossing/<o>-to-<d>/` |
| **Household Record** | *where does this family's operating system live* — the index that binds the graph to a household | live · `drift.household` / `drift.householdpage` → `/atlas/{edition}/household/` + `/household/<id>/`. **References artifacts, never duplicates** — points to the Atlas page, Crossing Brief, Comparison, Registers, and Annual Review, each authoritative in its own right. |
| **Opportunity Register / Annual Review / AI** | traverse the graph by node id | future |

**Rule for new products:** consume `atlas.build_state_edition(...)` (or `build_edition`); read the
structured nodes and their edges; render. If a product needs a new business rule, the rule belongs in the
graph (a new signal/priority/action), not in the product.

---

## Data flow

```
state_facts.RATES / ESTATE / *_SOURCES        (Layer 1 — canonical facts + citations)
        │
        ├─ tax.STATE_RATES ─────────────► after-tax calculator (drift.tax, drift.taxlab)
        │
        └─ statemap._state_record(code) ─► environment record  (dimensions + citations)
                    │
                    ▼
        reasoning.build_reasoning(code, env)   (Layer 2 — the per-state graph)
                    │
                    ▼
        atlas.build_state_edition(code, edition)   (composed StateEdition record)
                    │
                    ▼
        Products (Layer 3): statepage render · Comparison · Crossing Brief · Household Record · AI
```

`scripts/tax_alpha.py` closes a loop: it recomputes `leakage.STATE_ALPHA` from `RATES`, so the
Tax-Diagnostic figure never drifts from the canonical rates (lineage-guarded).

---

## Publishing model

- **`docs/` is the deployed GitHub Pages build**, `.nojekyll` (plain static — no server 301s, no Jekyll).
  Never hand-edit `docs/*.html`; they are generated.
- **`scripts/sync_docs.py`** re-renders `docs/` from `src/drift/web/*.html` templates for *structure/CSS*
  changes, preserving the injected `window.__STATE__` data and applying build tokens (e.g.
  `<!--FIRM_ANCHOR-->` → `site.firm_anchor_html()`).
- **The nightly `.github/workflows/drift-pages.yml` job** regenerates *data* from source
  (`drift statemap | leakage | states | export | tearsheet | taxlab | …`) and commits `docs/` (incl.
  `docs/atlas/**` for the editioned tree); **`pages.yml`** deploys on the resulting push.
- **URLs.** `/atlas/{edition}/{state}/` is the canonical publication URL; the flat `{state}-tax.html`
  slugs are permanent **redirect aliases** (static meta-refresh + `rel=canonical`, the closest a
  `.nojekyll` static site gets to a 301). The sitemap lists only editioned canonicals. Editioned pages
  are three levels deep and therefore carry **absolute (`BASE_URL`) links** — a domain flip regenerates
  or `set_domain.py`-rewrites them.

---

## Versioning strategy

- **Editions.** `statemap.EDITIONS = {"2026": {as_of_law, last_reviewed, changelog}}`,
  `CURRENT_EDITION = "2026"`. Each edition freezes its provenance snapshot; `/atlas/2026/…` stays citable
  forever after a later edition lands. `build_statemap` / `_state_record` / `build_state_edition` /
  `build_reasoning` all take a defaulted `edition`.
- **Facts** are reconciled to primary sources with a dated record (`*_SOURCES`, `RECONCILIATION_LOG.md`).
- **Derived artifacts** (`STATE_ALPHA`) are regenerated deterministically and lineage-guarded, so a fact
  change propagates by re-running the generator, not by hand-editing.
- **URL stability** is a first-class guarantee: canonical editioned URLs never move; flat slugs redirect
  forever.

---

## Knowledge-object schema

Every reasoning node is a typed object addressable by `node_id = "{STATE}:{kind}:{id}"`.

```
signal        { node_id, id, kind:"signal", title, question, reads:[dim…],
                opens:[priority_id…], level:"none|low|moderate|high|severe", score, reading,
                citations:[{url,label}…]  ← traversed from `reads` dimensions }

coordination  { node_id, id, kind:"coordination", title, domain, coordinate_with, priority:int,
                rationale, affected_dimensions:[dim…], related_signals:[signal_id…],
                related_actions:[action_id…], crossing_question, citations:[…] }

action        { node_id, id, kind:"action", title, owner, references:priority_id,
                related_signals:[signal_id…], crossing_phase:"before|during|after", step }

impact        { node_id, id:"after_tax_impact", kind:"impact", title, inputs, affected_dimensions,
                diagnostic_ref, illustrative_alpha_pct, before_pct, after_pct, reading }
```

**Edges** (the graph): `signal.reads → dimension` · `signal.opens → coordination` ·
`coordination.related_signals/related_actions` · `action.references → coordination`. Consumers traverse
these; they never re-derive them.

---

## Extension points

- **New annual edition** → add a key to `EDITIONS`, snapshot its facts, bump `CURRENT_EDITION`; the
  `/atlas/{new}/` tree and sitemap generate automatically; prior editions stay frozen and citable.
- **New fact** (a dimension, a rate, an estate figure) → author it **once** in `state_facts` /
  `statemap`, add a `*_SOURCES` citation; every projection updates.
- **New Decision Framework signal** → append to `FRAMEWORK_SIGNALS` with `reads` / `opens` / `evaluate`;
  it evaluates on every state and renders everywhere the graph renders. Same pattern for a new
  coordination priority (`COORDINATION_PRIORITIES`) or action (`ACTIONS`).
- **New product** → consume `atlas.build_state_edition` / `build_edition`, query the nodes/edges, render.
  Put any new rule in the graph, not the product. **`drift.compare` is the reference implementation:**
  `build_comparison(a, b)` is a pure set-diff over two graph records (which signals change level, which
  coordination priorities open/close) — it authors nothing, and its browser instrument only *lays out*
  already-decided levels/readings, it never re-evaluates a rule. Copy that shape for the Crossing Brief
  and the Household Record.
- **Domain change** → `scripts/set_domain.py <url>` (single-source `site.BASE_URL`); regenerate `docs/`.
- **Guardrails to keep green:** `pytest -q` (canonical/enumeration/reconciliation/reasoning guards,
  disclosures, typography, domain, correspondence) + `node tests/web/run.js` (the DOM-shim workspace
  flows). A fact or reasoning change that breaks a guard is surfacing drift, not a test to loosen.
