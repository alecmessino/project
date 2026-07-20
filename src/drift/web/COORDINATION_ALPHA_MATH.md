# The Coordination-Opportunity Figure — how the math works (internal)

**Audience:** internal — advisors, compliance, anyone asked "where does the ~$33k–$48k number come from, and is that all of it?"
**Status:** reference. Reflects the shipped model as of July 2026. **Changes nothing** about the published figure; this only documents and stress-tests it.
**One-line answer:** it's a real 30-year, after-tax backtest of two portfolios taxed at each state's own rates — and it deliberately counts **only portfolio tax management**, so the number you see is a **conservative floor**, not the whole coordination opportunity.

---

## 1. TL;DR

- The number rendered as "**~$40,000/yr per $1M**" (Illinois) is literally **`alpha% × $10,000`**. Illinois's `alpha` is `4.0` → `$40k`. The band across all states is **WA 3.3% → $33k … MA/NYC 4.8% → $48k**.
- `alpha` = the **after-tax CAGR a tax-managed book keeps over a concentrated, tax-naive one**, measured on a single 30-year proxy-spliced path of 18 ETFs (1996–2026), with taxes paid as-you-go at that state's real long-term/short-term capital-gains rates.
- It monetizes exactly **two levers**: (1) lot protection + hysteresis (turning short-term churn into long-term gains) and (2) tax-loss harvesting + rate arbitrage. Asset location is a real third lever but is reported **separately** (household-specific), not folded in.
- **Everything else the Atlas shows — estate/death tax, gifting, residency, QSBS, muni preference, basis step-up, marriage — contributes $0 to this figure.** Our own `coordination.html` already puts **~$395,000** on one estate move it never adds in. So the true coordination opportunity is materially **larger** than the headline.
- It is honest and reproducible: `pretax_after (9.1%) < pretax_before (9.4%)` — we explicitly **do not** claim the tax-managed book earns more pre-tax; the entire win is after-tax efficiency. Regenerate any time with one command (§7) — guarded by a test.

---

## 2. The pipeline (exactly how the number is built)

```
tests/data/matrix_history.json        18 ETFs, ~30y proxy-spliced daily prices (1996–2026)
        │  cross_book_entries()        run the cross-sectional momentum book TWO ways  (src/drift/cross_section.py)
        ├─ BEFORE  = "Unconstrained Core": concentrated top-half, high turnover  (config/drift.yaml)
        │            → ~94% of gains realized SHORT-TERM, no harvesting
        └─ AFTER   = "Structural hybrid": full-universe gentle tilt + no-trade band + lot protection
                     ( _hybrid(fast, 0.5) — tilt_overlay/lot_protect ON for the MODEL ONLY )
        │
        │  decompose(BEFORE, AFTER, state_rates, 30y)   PER STATE   (scripts/tax_alpha.py)
        │     lot_after_tax(): FIFO dollar-lot walk, pays tax each rebalance
        │        · splits gains short vs long by 252-day holding period
        │        · harvest=True nets realized losses SHORT-first (rate arbitrage)
        │     before = CAGR(BEFORE, taxed naively)      after = CAGR(AFTER, harvesting on)
        │     alpha  = after − before        (annualized after-tax %/yr)
        ▼
STATE_ALPHA[state] = {before, after, alpha}     committed cache in src/drift/leakage.py:28-56
        │  coordination_opportunity_per_m(alpha) = round(alpha/100 × 1_000_000, −2)   ( = alpha% × $10k )
        ▼
displayed:  "~$40,000/yr per $1M taxable"  ·  "about +4.0%/yr"  ·  Atlas tag "$40k/$1M"
```

Two things to internalize:
- **The `$/1M` step is a flat, one-year, non-compounded multiply** (`src/drift/leakage.py:59-67`). There is no discounting and no 30-year terminal-wealth number in the dollar. The 30-year compounding lives *upstream*, inside the after-tax CAGR that produces `alpha`.
- **The return path is real, not assumed.** Returns are the actual proxy-spliced ETF prices run through the momentum book; only the *tax treatment* varies. There is no assumed rate of return.

Key functions: `lot_after_tax` / `decompose` / `all_state_alpha` (`scripts/tax_alpha.py`), `coordination_opportunity_per_m` / `STATE_ALPHA` (`src/drift/leakage.py`), state rates `RATES` (`src/drift/state_facts.py`), federal rates `TaxSettings` (`src/drift/config.py`).

---

## 3. Worked example (validated output, this run)

The concentrated ("BEFORE") book and the structural ("AFTER") book are identical pre-tax; the only differences are turnover/holding-period and harvesting. Taxed at each state's rates, the after-tax gap (`alpha`) decomposes cleanly:

```
 state   after-tax CAGR   lot+hysteresis   +harvest   = alpha    $/1M
 —(fed)     2.7 → 6.3%         2.4            1.3         3.7     $37k
 IL         1.8 → 5.9%         2.6            1.5         4.0     $40k
 NY         0.8 → 5.3%         2.8            1.7         4.5     $45k
 CA         0.4 → 5.1%         2.9            1.8         4.7     $47k
 (full table range: WA 3.3 → $33k … MA / NYC 4.8 → $48k)
```

- **"Kept-of-the-gain":** federal-only, the concentrated book keeps **9%** of its pre-tax gain after tax; the structural book keeps **41%**. That is the whole story in one number.
- **Pre-tax:** BEFORE 9.4%/yr vs AFTER 9.1%/yr — the structural book earns *slightly less* pre-tax. The win is 100% after-tax. (This inversion is deliberately preserved; it's what keeps the claim honest and Marketing-Rule-safe.)

**Why the number differs by state (it's driven by the *short-term* rate):** the concentrated book realizes ~94% short-term, so the more a state taxes short-term gains, the more that naive book leaks and the larger the recoverable alpha.
- **WA = $33k (lowest):** Washington's excise hits **long-term gains only** (short-term rate 0%). So it barely touches the mostly-short-term naive book but *does* tax the tax-managed book's long-term gains — the recovery shrinks below the federal baseline.
- **IL = $40k:** flat 4.95% on both ST and LT pulls the naive book down to 1.8% while the managed book only falls to 5.9%.
- **MA = $48k (highest):** a 12.5% short-term rate (incl. the millionaire surtax) crushes the high-ST naive book to 0.6% while the LT-heavy managed book only drops to 5.3% — the widest gap.

---

## 4. What the figure counts — and what it does NOT

**IN (the only monetized levers):**
| Lever | Share of the figure | Mechanism |
|---|---|---|
| Lot protection + hysteresis | ~60–65% | converts short-term churn → long-term gains (lower rate) |
| Tax-loss harvesting + rate arbitrage | ~35–40% | banks realized losses, nets them short-first against the highest-taxed gains |
| Asset location | reported **separately** | shelters the taxable drag into Roth/Traditional — household-specific, quantified per client in the Tax Lab, **not summed into the headline** |

All three are **portfolio** levers on a **taxable brokerage** book.

**OUT (shown on the Atlas as factual regime dimensions, but $0 in the dollar figure):**
estate / death tax · gifting & freeze techniques (SLAT / GRAT / FLP discounts / ILIT) · residency & relocation · QSBS §1202 · municipal-bond preference · basis step-up §1014 · marriage / filing status.

The Atlas is explicit that the "Coordination Opportunity" dimension is *"a descriptive estimate … a reference dimension, not a product claim,"* while the other seven are *"factual regime dimensions"* with no dollar attached.

---

## 5. "Is it higher / are we missing something?" — Yes. It's a floor.

The published figure is a **floor for portfolio tax efficiency**, not a ceiling for total household coordination value. The largest omitted categories, ordered by likely size:

1. **Estate / death tax — the biggest gap.** Our own `coordination.html` worked example dollarizes one Illinois estate move at **~$395,000 one-time** ($680,634 → $285,714 on a coordinated $5M estate) — an order of magnitude larger than the ~$40k/yr portfolio figure, and for an HNW Illinois household a single move can exceed a *decade* of the portfolio alpha. **Not in the number.**
2. **Gifting / freeze techniques (SLAT, GRAT, FLP discounts, §162-funded ILIT).** These remove future *growth* from the estate; compounding-growth-removed is inherently larger than an annual portfolio drag. Not in the number.
3. **Residency / relocation.** "A 4.95% state income tax becomes 0%; Illinois's $4M estate trap disappears on the Texas side." Sequencing a business sale around residency (the ~$17M-gain case in `VALIDATION_RUN_01.md`) is a very large, uncounted line. Not in the number.
4. **QSBS §1202** — for a founder, potentially the single biggest item (multi-million exclusion). The Atlas only flags conform/decouple. Not in the number.
5. **Muni preference & §1014 step-up** — smaller and steadier, still real. Not in the number.

**Honest framing to use externally:** *"The ~$33k–$48k per $1M is what disciplined portfolio tax management alone recovers each year. It does not yet include the estate, gifting, residency, or QSBS coordination we do — those are typically larger and one-time. Treat the number as a floor."*

**Important caveat — do not lift the number by inflating the existing alpha.** The portfolio alpha is already specified aggressively inside its own lane: the BEFORE book is a deliberately punitive concentrated/high-turnover strawman, and the AFTER book uses research flags (`tilt_overlay` / `lot_protect`) that are **OFF in every shipped live config** (research-only). The path to a bigger, defensible number is **adding new monetized levers**, not re-tuning the portfolio model.

---

## 6. How to grow the number honestly (if we choose to, later)

Not done here — this is a roadmap, each item gated:
- Build a **monetized estate/gifting lever** off the existing `taxlab.py` estate model (`il_estate_tax`, the fed/state exemption logic) → an illustrative one-time $ that could be shown alongside (not blended into) the annual portfolio figure.
- Build a **residency-sequencing lever** off the existing IL→TX comparison.
- Each new number requires: its own model + assumptions, an **Evidence Register entry**, an **automated guard test**, a review date, and counsel sign-off — and stays labeled illustrative/hypothetical/diagnostic-gated. Level-2 modeling is never dressed with Level-1 statutory confidence.

---

## 7. Reproduce it yourself (validation receipt)

From repo root:

```bash
# regenerate the exact STATE_ALPHA table from the model (self-execs with PYTHONHASHSEED=0)
PYTHONPATH=src TAX_ALPHA_STATES=1 python3 scripts/tax_alpha.py

# human-readable per-lever decomposition (the §3 table, Sharpe, ST%, kept-of-gain)
PYTHONPATH=src python3 scripts/tax_alpha.py

# the guard: recompute from the model + assert the published headline never overstates the table
PYTHONPATH=src python3 -m pytest -q tests/test_leakage_alpha_lineage.py
```

Last validated (this run): the regenerated table **matched** the committed `STATE_ALPHA` (WA 3.3, IL 4.0, MA 4.8, CA 4.7, NYC 4.8, Federal 3.7); `test_leakage_alpha_lineage.py` → **4 passed**.

**Assumptions / constants to know:** federal 37% short-term / 20% long-term + 3.8% NIIT, plus each state's real (LT, ST) rate from `state_facts.RATES`; 252-day long-term threshold; **30-year** window (`TAX_ALPHA_YEARS=40` reproduces the prior full-sample run); BEFORE 96%/AFTER 53% short-term share; hybrid tilt `k=0.5`. Determinism is hash-seed-fixed; run-to-run drift is ~0.1 %/yr, which is why the lineage test uses a 0.2 %/yr tolerance.

---

## 8. Compliance guardrails (do not erode)

- **Illustrative / hypothetical, not a forecast.** It's an after-tax, paid-as-you-go result on a single proxy-spliced path — a *tax-efficiency* result, **not** a pre-tax return claim and **not** a forecast that any fund out-performs.
- **Diagnostic-gated, reference dimension, not a product claim.** Every surface ends with "your actual figure depends on your holdings; the diagnostic computes it."
- **Keep the honest inversion** (`pretax_after < pretax_before`) — it's load-bearing for SEC Marketing Rule 206(4)-1 framing.
- **`tilt_overlay` / `lot_protect` stay OFF in shipped configs** and out of the live signal (neutral-tilt guard test).
- **Evidence Register protocol** governs any new or raised number: entry + automated guard + review date before it ships.
- Backtested/hypothetical performance disclosure and RIA identity language apply to any surface that shows the figure.

*This document is internal reference only. It does not modify any published figure, model, or disclosure.*
