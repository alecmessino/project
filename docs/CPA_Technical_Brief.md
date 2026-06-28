# Structural Alpha — Technical Brief for CPAs and Tax Advisors

**Audience:** the client's accountant / tax advisor (the gatekeeper). **Purpose:** explain, in
quantitative and mechanical terms, where Driftwood / CWS Planning generates measurable value for a
taxable household — and to be precise about what that value is and is not. **Tone:** institutional;
no marketing claims. Companion to the client-facing **Tax-Leakage Diagnostic** (`leakage.html`) and the
canonical **`Structural_Alpha_Methodology.md`**.

---

## 1. Thesis in one paragraph

We do **not** claim a market-timing or stock-selection edge. Our research is explicit that the
momentum/timing signal added no risk-adjusted value (≈ +0.01 Sharpe over 40 years), so it ships
**neutral** and is not the deployed strategy. What we deliver is **Structural Alpha**: deliberate,
factor-tilted equity **exposure** (engineered beta — Small/Value, Emerging Markets, International, held
via low-cost Avantis funds) combined with **mechanical tax management**. The exposure is a risk-premia
choice, **not a forecast that those funds out-perform**. The quantifiable, repeatable edge is the tax
management — the part a passive benchmark simply *leaks*. This brief is about that edge.

## 2. The quantified result (what to interrogate)

On an identical 18-ETF universe, holding the investment decisions fixed and varying **only** the tax
treatment, the engine recovers the following in **after-tax CAGR** versus a concentrated, high-turnover
book taxed naively (`scripts/tax_alpha.py`, 40-year proxy-spliced path):

| Tax environment | After-tax CAGR — naive | After-tax CAGR — managed | **Structural Alpha (tax)** |
|---|---:|---:|---:|
| Federal only | 3.1%/yr | 6.4%/yr | **+3.2%/yr** |
| Illinois | 2.3%/yr | 5.9%/yr | **+3.6%/yr** |
| New York | 1.3%/yr | 5.4%/yr | **+4.1%/yr** |
| California | 0.8%/yr | 5.2%/yr | **+4.3%/yr** |

Three things a CPA should note immediately:
- It is **after-tax**, and it is **not** a pre-tax return claim — pre-tax CAGR is in fact slightly
  *lower* on the managed book (9.3% vs 9.9%). The value is entirely in what is *kept*.
- It **rises with the marginal rate** — the higher the client's bracket/state, the larger the leak we
  plug. This is the opposite of luck; it is rate arithmetic.
- It is **illustrative** (FIFO lot accounting on the book's own marks, paid-as-you-go, single
  historical path), not a guarantee. The mechanics below are what produce it.

The assumption-free part decomposes ≈ **55–60% basis management** and ≈ **40–45% harvesting + rate
arbitrage**; **asset location** is the household-specific third driver, quantified per client.

## 3. Driver one — Basis management (lot protection + hysteresis)

**Mechanic.** The engine holds positions through noise (hysteresis) and protects unrealized lots from
being trimmed, so realizations are deferred and, when they occur, are more likely **long-term**. On the
concentrated book ~**94%** of realized gains are short-term; the managed book cuts that to ~**50%** and
roughly halves turnover (344% → 141%).

**Why it matters (the rate arbitrage).** Short-term gains are taxed as ordinary income; long-term at
preferential rates. The federal spread alone is **40.8% → 23.8%** (37% + 3.8% NIIT vs 20% + 3.8% NIIT),
≈ **17 points**, widening with state tax (CA: 54.1% → 37.1%). Converting a short-term realization into a
long-term one is a direct, mechanical pickup of that spread.

**Engine reference.** `drift.tax.after_tax_track` runs a FIFO dollar-lot simulation, dating each lot and
splitting realizations short- vs long-term by holding period (`lt_holding_bars`). **CPA coordination:**
elect **specific-identification** cost basis at the custodian; the strategy assumes lot-level control,
not average cost.

## 4. Driver two — Asset location

**Mechanic.** Place the **highest-tax-drag** sleeve (the high-turnover, short-term-gain generator) into
**tax-advantaged** accounts (Roth first for tax-free compounding, then Traditional), and isolate the
**low-turnover, qualified-dividend** core in the **taxable** account, where it is held for the §1014
step-up. This is strictly better than a naive proportional spread across account types.

**Quantification.** Annual tax saved versus the proportional split is

  `annual_saved = (T·A / W) · (mom_drag_rate − passive_drag_rate)`,

with `T` = taxable balance, `A` = traditional + roth, `W = T + A` (`drift.taxlab.location_alpha3`,
which also returns a reinvested terminal figure and a sensitivity band via `location_alpha3_range`).
The benefit is maximized at a balanced taxable/advantaged split and scales with the drag spread. **This
is personalized in the Tax Lab** from the client's actual account balances, bracket, and state — the
brief states the mechanism, not a one-size number.

**CPA coordination:** confirm contribution/Roth-conversion capacity, beneficiary designations, and the
interaction with RMDs and IRMAA thresholds.

## 5. Driver three — Tax-loss harvesting + rate arbitrage

**Mechanic.** Realize losses and **net them short-term-first** against the highest-rate gains, banking
a carryforward; maintain market exposure with **wash-sale-safe substitutes** (e.g. VT ↔ VTI/VXUS
sleeves) through the 30-day window. Holding the index as **individual sleeves** (rather than a single
fund) lets losses be harvested at the **security level** — in most years some sleeves fall even when the
blended index rises, so the book banks structural losses a single ETF cannot.

**Why short-first.** A harvested loss is worth "the rate of the gain it offsets." Netting against
ordinary-rate short-term gains first extracts the maximum value from each loss — the same rate-arbitrage
logic as Driver one, applied to losses.

**Engine reference.** The carryforward netting (short-first, then long-term) is implemented in
`after_tax_track`; the rate-independent gross realizations are exposed by `gain_profile` so any
bracket/state can be applied downstream. **CPA coordination:** monitor wash-sale exposure across
substitutes and any duplicate holdings in *other* accounts (including a spouse's); reconcile to the
**1099-B**.

## 6. Methodology, assumptions, and limits (state these plainly)

- **FIFO dollar-lot accounting on the book's own daily marks** — a model of custodian lot accounting,
  not the custodian's actual records; the client's real basis governs.
- **Rates:** top-of-bracket federal (37% ST / 20% LT) + 3.8% NIIT + representative top **state** rates
  (`drift.tax.STATE_RATES`, including the WA LT excise, MA higher ST, and the LT-exclusion states).
  Verify against the client's actual marginal rates.
- **Horizon / path:** a single ~40-year history, **partly proxy-spliced** pre-2006; figures are
  cumulative and **paid-as-you-go**. A single path is not a distribution of outcomes.
- **Determinism:** the lot-protection redistribution is hash-seed sensitive (~1–2% run-to-run); set
  `PYTHONHASHSEED=0` for bit-exact reproduction.
- **Illustrative only — not tax advice.** The advisor and the CPA confirm suitability and the filing
  figures.

## 7. Substantiation boundary (what we will and will not claim)

| We claim | We do not claim |
|---|---|
| A **deterministic, quantified** after-tax benefit from basis management, asset location, and harvesting. | Any pre-tax outperformance of the strategy or of the underlying funds. |
| Deliberate factor **exposure** (engineered beta) as a risk-premia choice. | That the factor tilt **will out-perform** the market. |
| The momentum research is honest **proof of work**, demoted to a research satellite. | A market-timing or signal edge — it ships neutral. |

Driftwood is a research brand of **CWS Planning**, a **registered investment adviser**; Form ADV and
Form CRS are available at adviserinfo.sec.gov. Performance figures herein are **hypothetical /
backtested** (retroactive application of a model to historical data; no client capital was invested;
past performance does not guarantee future results).

## 8. CPA coordination checklist

- [ ] Elect **specific-identification** cost basis at the custodian (enables lot/holding-period control).
- [ ] Confirm **account-location** capacity (Roth/Traditional contribution room, conversion strategy).
- [ ] Manage **wash sales** across substitutes and across all household accounts; reconcile to 1099-B.
- [ ] Coordinate **§1014 step-up**: keep the appreciated taxable core for basis step-up at death.
- [ ] Plan **withdrawals** to manage bracket, IRMAA, and RMDs; fund Roth conversions in low-income years.
- [ ] Re-confirm **state residency** assumptions — the Structural Alpha figure is state-rate dependent.

## 9. References

- `docs/Structural_Alpha_Methodology.md` — canonical framing + substantiation boundary.
- `docs/Tilt_Validation_Results.md` → "Tax-Alpha decomposition" — the empirical run.
- `scripts/tax_alpha.py` — the decomposition (after-tax CAGR, by state, adversarially cross-checked).
- `drift.tax.after_tax_track` / `gain_profile`; `drift.taxlab.location_alpha3` — the engine functions.
- `leakage.html` — the client-facing one-page Before/After diagnostic.
