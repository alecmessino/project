# Driftwood Evidence Register

*Every quantitative claim published on the site, with its lineage. If a number isn't in this
register, it doesn't ship. If a number is challenged — by a prospect, a CPA, or a regulator —
this is where the answer lives.*

**Protocol.** Before any new statistic appears on the site: add its entry here (all fields),
name its automated guard if one exists, and give it a review date. When a figure is retired
from the site, mark its entry *Retired* rather than deleting it — the history is part of the
record. Owner of the register: **Alec Messino** (firm principal). Companion documents:
`Editorial_Style_Guide.md` (voice), `Content_Hierarchy.md` (where numbers are allowed to appear).

Two standing rules from the numbers audit:

1. **One number per page.** Home → the recovery band. Our Story → $400M. Diagnostic → dollars
   recovered. Tax Lab → the visitor's own dollars. Research → 0.65 ≈ 0.65. Everything else is
   supporting cast.
2. **Dollars beat percentages** for family-facing pages; percentages and ratios belong to the
   research layer.

---

## 1 · $400 million moved

| Field | Value |
| --- | --- |
| Claim | During the founder's time at Dimensional Fund Advisors, a project surfacing tax-inefficient funds led advisors to move more than $400 million. |
| Appears | Our Story (`about.html`) |
| Source | Founder's direct professional experience (attested); narrative claim, not a performance figure |
| Methodology / assumptions | None — a factual account of client-directed flows, not a result Driftwood claims credit for as performance |
| Why it exists | Proves institutional experience through a story rather than a résumé; the site's most memorable number |
| Owner | Alec Messino |
| Last verified | 2026-07-05 (attestation) |
| Review | Only if the narrative wording changes; keep phrasing consistent with the attested facts |
| Automated guard | None (narrative). Wording changes go through compliance review |

## 2 · +3.7–4.7%/yr illustrative after-tax recovery

| Field | Value |
| --- | --- |
| Claim | On an identical exposure, structural tax & fee management recovers an illustrative +3.7–4.7%/yr after tax, spanning no-tax states to California |
| Appears | Homepage pillar 1 · Tax Diagnostic hero · State Tax Guide / all 51 state pages · Tax Lab |
| Source | Internal leakage engine (`src/drift/leakage.py`) over the 30-year proxy-spliced return cache; empirical backbone in `scripts/tax_alpha` |
| Methodology / assumptions | Identical holdings, taxed naively vs tax-managed (lot selection, patient trading, loss harvesting); 30-year horizon; FIFO lot accounting; federal + state; hypothetical, no client capital |
| Why it exists | The firm's substantiated edge, expressed as a range (ranges read honest); the homepage's ONE number |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | On every return-cache refresh; re-run lineage test |
| Automated guard | `tests/test_leakage_alpha_lineage.py` (regression-locks the band to the engine); hub hero equality asserts in `tests/test_drift_hub.py` |

## 3 · $90,000 → $410,000 kept from $1 million of gains *(was: 9% → 41%)*

| Field | Value |
| --- | --- |
| Claim | Of $1 million in realized gains compounded over 30 years, the modeled tax-naive book keeps ~$90,000 of the gain's value; the tax-managed book ~$410,000 |
| Appears | Homepage pillar 3 (dollar form) · Tax Diagnostic before/after bars (percentage form) |
| Source | Same leakage engine as entry 2 (`keep_pct` before/after); dollar form is `keep_pct% × $1,000,000`, computed in `src/drift/hub.py` — one source of truth |
| Methodology / assumptions | 30-year horizon; federal-only illustration; high-turnover concentrated book vs tax-managed same holdings; hypothetical |
| Why it exists | Retained-gain percentages fail the "41% of what?" test; affluent families think in dollars |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | On return-cache refresh (moves with entry 2) |
| Automated guard | `tests/test_drift_hub.py` asserts the dollar stat equals the engine keep-rates × $1M |

## 4 · 9.1% pre-tax beat 9.4% pre-tax (the honest inversion)

| Field | Value |
| --- | --- |
| Claim | In the model, the tax-managed book earned slightly less pre-tax (9.1% vs 9.4%) and still produced more after-tax wealth |
| Appears | Homepage "How it works" lead line · Tax Diagnostic small print |
| Source | Leakage engine headline (`pretax_before` / `pretax_after`), surfaced through the hub state |
| Methodology / assumptions | Same run as entries 2–3; the pre-tax gap is the cost of tax-aware trading; hypothetical |
| Why it exists | The credibility proof for sophisticated readers: the firm is explicitly NOT claiming pre-tax outperformance |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | On return-cache refresh; the rendered sentence hides itself if the inversion ever stops holding |
| Automated guard | `tests/test_drift_hub.py` asserts `pretax_after < pretax_before`; the template renders the line only when the inversion holds |

## 5 · 0.65 ≈ 0.65 (out-of-sample survival)

| Field | Value |
| --- | --- |
| Claim | The complement strategy's out-of-sample Sharpe (0.65, ~4,000 test bars ≈ 16 years) matched its in-sample fit (0.648) — the approach wasn't fit to the past |
| Appears | Homepage pillar 2 · long-history tearsheet |
| Source | Train/test split of the multi-decade backtest (`tearsheet.html` embedded state; optimizer lineage in `scripts/tilt_optimize.py`) |
| Methodology / assumptions | Walk-forward split; net of modeled costs; hypothetical; the split dates live in the tearsheet state |
| Why it exists | The most differentiated research claim on the site — persistence over peak Sharpe. Needs its one-line translation wherever it appears |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | On any re-fit or universe change |
| Automated guard | Hub reads it from the tearsheet state (`build_hub`); perf-figure assertions in `tests/test_drift_hub.py` |

## 6 · Live ledger figures (+41.4% · Sharpe 1.37 vs VT 1.23 / VTI 1.10 · −16% max DD)

| Field | Value |
| --- | --- |
| Claim | The hypothetical Model Portfolio has returned +41.4% since 2024-09-16 (449 sessions), Sharpe 1.37 vs 1.23/1.10 for VT/VTI, −16% max drawdown |
| Appears | Homepage appendix line (dated) · dashboard · ledger — research layer only |
| Source | Append-only `docs/ledger.json`, marked daily by the nightly workflow; never recomputed retroactively |
| Methodology / assumptions | Hypothetical backtest applied forward; 18-ETF universe; 5 bps/side modeled cost; not a client account |
| Why it exists | Demonstrates the complement strategy's live behavior, honestly dated |
| Owner | Automated (nightly cron) · Alec reviews monthly |
| Last verified | Auto — refreshes nightly (figures above as of 2026-07-02 data) |
| Review | Monthly eyeball; freshness guards fail the build on stale data |
| Automated guard | Freshness guards + append-only ledger tests (`tests/test_drift_ledger.py`, blotter-source tests) |
| Note | **Numeric collision risk:** +41.4% (return) vs $410,000/41% (keep-rate) — keep the return in the appendix and never let the two share a viewport without labels |

## 7 · 58% vs 59% max drawdown (multi-decade backtest)

| Field | Value |
| --- | --- |
| Claim | Across the multi-decade backtest, strategy max drawdown ≈ 58% vs 59% for buy-and-hold |
| Appears | Hub appendix stat line · tearsheet |
| Source | Long-history tearsheet state |
| Why it exists | Honesty (the strategy does not claim drawdown protection) — but it communicates little to prospects |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | Flagged by the numbers audit as one of the five weakest; **candidate for removal from the hub appendix line** (keep on the tearsheet). Pending owner decision |
| Automated guard | `test_build_hub_reads_tearsheet_drawdown_headline` |

## 8 · State tax dataset (rates · estate cliffs · QSBS · munis · basis step-up · per-state recovery)

| Field | Value |
| --- | --- |
| Claim | Per-state capital-gains treatment across seven dimensions, and the illustrative recovery available in each state |
| Appears | State Tax Guide (`statemap.html`) · 51 state pages · Tax Diagnostic state table · Tax Lab |
| Source | Internal dataset (`src/drift/statemap.py`, `src/drift/statepage.py`) compiled from public state law |
| Methodology / assumptions | 2026 law as enacted; top marginal rates; the recovery figure inherits entry 2's engine and assumptions |
| Why it exists | Instantly useful, instantly understood — the most shareable factual layer on the site |
| Owner | Alec Messino |
| Last verified | 2026 law at build time |
| Review | **Annually each January** (legislative sessions), plus ad-hoc on major state tax legislation. Audit action: add a visible "as of 2026 law" source line to the pages — open item |
| Automated guard | Dataset-shape tests (`tests/test_drift_statemap.py`); no-fabrication boundary tests |

## 9 · Tax Lab model assumptions

| Field | Value |
| --- | --- |
| Claim | Default household $2.5M ($1.5M taxable / $1.0M tax-advantaged); 7% growth; 30-year horizon; 3% realized gain per unit of turnover; model turnover 3.95×/yr with 95.2% short-term share; proposed blended ER from ~21 bps vs a 40 bps legacy assumption |
| Appears | Tax Lab (all views); every dollar figure it outputs |
| Source | `src/drift/tax*.py` engines + embedded assumptions block; model portfolios from `config/avantis_models.json` |
| Methodology / assumptions | All listed values are editable inputs; outputs carry sensitivity ranges (the ±band pattern) rather than point estimates |
| Why it exists | Personalization is the Tax Lab's job; the assumptions ARE the product and must stay visible near every headline dollar |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | Annually with tax-bracket updates; on any model-portfolio change |
| Automated guard | `tests/test_drift_tax.py` (methodology copy + math), Tax-Alpha lineage test |

## 10 · Estate figures (Illinois cliff · 2026 federal exemption · HB2601)

| Field | Value |
| --- | --- |
| Claim | Illinois estate-tax cliff behavior, the 2026 federal exemption, and the proposed HB2601 exemption, modeled against 2026 law |
| Appears | Tax Lab estate view |
| Source | Enacted 2026 law + the HB2601 proposal as introduced (explicitly labeled proposed) |
| Why it exists | The estate cliff is the sharpest dollars-at-stake illustration for Illinois families |
| Owner | Alec Messino |
| Last verified | 2026 legislative status at build time |
| Review | **Each legislative session**; HB2601 line must be updated or removed when the bill resolves. Page already says "confirm the filing figure with your estate attorney" |
| Automated guard | Estate-view rendering tests in `tests/web/run.js` |

## 11 · Research-study metrics (case studies page)

| Field | Value |
| --- | --- |
| Claim | Six educational backtests: e.g. cross-sectional +45.5% net (Sharpe 1.35), region-neutral +46.3% (1.36), trend-vs-random-walk control (+36.8% vs +1.5%, Sharpe 2.39), 15/18 profitable names, 40-bar best window |
| Appears | Research studies page only |
| Source | `src/drift/case_studies.py` over the committed 18-ETF matrix cache (521 bars) |
| Methodology / assumptions | Walk-forward, net of modeled cost; the synthetic-control Sharpe is a **teaching device** and must never be quoted outside its study |
| Why it exists | Shows *why* the complement strategy behaves as it does — intellectual rigor, contained to the research layer |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | On data-cache refresh |
| Automated guard | `tests/test_drift_case_studies.py` |

## 12 · Concentration tool scores (22 strategies × 6 axes)

| Field | Value |
| --- | --- |
| Claim | 22 de-risking strategies scored 1–5 across liquidity, speed, fees, tax cost, customization, simplicity, plus committee fit notes |
| Appears | Single asset risk (`concentration.html`) |
| Source | `src/drift/concentration.py` — one analyst's read of typical mechanics, explicitly labeled orientation |
| Why it exists | Decision-console teaching artifact; qualitative scores, not performance claims |
| Owner | Alec Messino |
| Last verified | 2026-07-05 |
| Review | Annually, or when a strategy's typical mechanics change (e.g. new exchange-fund structures) |
| Automated guard | `tests/test_concentration.py` (full coverage: every cell scored, every strategy carries fit notes) |
