# Structural Alpha — Methodology

**Status: canonical narrative reference for CWS Planning / Driftwood client-facing copy.**
This document defines the firm's value proposition and the exact boundary of what each claim is
allowed to assert. Every word of client-facing copy (the hub, thesis, Tax Lab, and the research
exhibits) must map to one of the three pillars below — and no further. It is written to be defensible
under **SEC Marketing Rule 206(4)-1**: claims are substantiated, exposure is not dressed up as a
return forecast, and hypothetical performance stays labeled as such.

---

## The pivot, in one line

We are building **engineered beta, not market timing.**

The firm's value proposition is **Structural Alpha**: the deliberate maintenance of specific,
factor-tilted *exposure* combined with active, *mechanical* tax management. It is **not** "Signal
Alpha" — we do not claim to time or rotate markets for return. The real-data research is explicit on
this point and we lead with the conclusion, not against it.

### Why we made the pivot (the honest finding)

Across a 40-year proxy-spliced backtest of the global region/size/style ETF matrix
(`tests/data/matrix_history.json`) and a modern-era cost/capacity optimization, the momentum /
timing signal added **no risk-adjusted value**: the tilt overlay contributed roughly **+0.01 Sharpe
and ~0.5% of return**, and the "optimum" of the parameter sweep collapsed toward near buy-and-hold.
The measurable, repeatable edge was never the signal. It was (1) **mechanical tax management** and
(2) **deliberate factor exposure**. We say so plainly. Retiring a weak claim and standing on a
defensible one is the stronger compliance and business position.

---

## The substantiation boundary (the compliance spine)

| Pillar | What we MAY claim | What we may NOT claim | Where it is substantiated |
|---|---|---|---|
| **1 · Tax + fee edge** (the quantified "Structural Alpha" number) | A **deterministic, quantified** benefit a passive benchmark simply *leaks*: tax-loss harvesting, **lot protection + hysteresis** (short-term → long-term conversion), asset location across taxable / Traditional / Roth, and a lower blended fund cost. | — (it is a modeled, illustrative figure, not a guarantee) | `taxlab.location_alpha3`, `tax.after_tax_track` / `tax.gain_profile` (FIFO lot engine), and the blended-ER fee delta in `firm_models.py`. |
| **2 · Factor exposure** ("engineered beta") | That we **deliberately hold** small/value, emerging-markets, and international **exposure** via the firm's Avantis sleeves — a risk-premia *exposure* choice we make on purpose. | That these funds **will out-perform** the market. No factor-outperformance forecast. | `firm_models.py` IPS weights (AVUS / AVUV / AVDE / AVES). A holdings fact, not a return claim. |
| **3 · Momentum / timing** | An **honest description** of it where it still appears as a clearly-labeled **research satellite** (proof-of-work that we explored the full landscape). | Leading with it, or implying it is the source of the track record. | The Driftwood engine ships **neutral tilt** (config tilts all 1.0; guarded by `test_shipped_configs_ship_neutral_tilt`). The momentum overlay is **off in every shipped config and out of the live signal**. |

**Net framing.** "Structural Alpha" is the **umbrella**: a distinct, *compounded* benefit over a
**generic passive benchmark**, built from two deliberate structural choices — and explicitly **not**
market timing. It works because it captures the specific risk premia we want *while* our engine
harvests tax benefits a passive benchmark leaks.
- **Engineered beta** — the deliberate Avantis factor **exposure** (Small/Value, Emerging Markets,
  International): the specific risk premia we choose to hold. Risk-premia *exposure*, **not** a forecast
  of factor outperformance.
- **Mechanical tax management** — the **deterministic, quantified** component (lot protection +
  hysteresis + asset location + harvesting): the part a passive benchmark *leaks* and we plug. This is
  the literal "Estimated Structural Alpha (Tax + Fee Optimization)" figure.
- **Momentum / market timing** — an honestly-labeled **research satellite**, demoted out of the primary
  client path. We claim **no** timing edge.

---

## How this maps to the surfaces

### Primary client funnel (leads with Structural Alpha)
- **Hub** → **Thesis** → **Tax Lab.** These lead **exclusively** with the Structural-Alpha /
  Tax-Managed Core narrative: the tax + fee edge, the engineered factor exposure, the risk-managed
  posture. The factor tilt is always framed as deliberate **exposure**, never as an outperformance
  forecast; the page keeps the standing phrase *"not a forecast that these funds out-perform."*

### Exploratory Research appendix (proof-of-work, not the pitch)
- The momentum **Dashboard**, **Model Portfolio ledger**, and **long-history tearsheet** are
  relegated to a clearly-labeled **"Exploratory Research"** / performance-history appendix. They stay
  intact — they prove we rigorously explored the full investment landscape — but they are reached as
  *proof of work*, not from the hero. Each carries an honest banner:
  > *These are exploratory research models. The shipped engine prioritizes Structural Alpha via
  > tax-engineering and engineered factor exposure; the momentum/trend signal here ships neutral and
  > is not the strategy a client deploys.*
- The momentum *description* on those pages stays accurate (it really is cross-sectional momentum) —
  required for compliance honesty. We stop **leading** with it; we do not scrub it.

---

## Compliance guards (must all survive)

- Keep **"not a forecast that these funds out-perform"** wherever factor exposure is presented; frame
  the tilt as **exposure**, never outperformance.
- Keep the **neutral-tilt** shipped-config guard (`test_shipped_configs_ship_neutral_tilt`); the
  `tilt_overlay` / `lot_protect` research flags stay **off** in shipped configs and **out of the live
  signal**.
- Keep every **hypothetical-performance**, **RIA-identity** (registered investment adviser, Form
  ADV/CRS, adviserinfo.sec.gov), and **audience** disclosure already in place (the maximal-subtle
  posture is RIA-principal approved — see `docs/Compliance_Disclosure_Changes.md`).
- The "Estimated Structural Alpha" figure stays labeled **illustrative tax + fee modeling**, with its
  sensitivity range — not a performance promise.

---

## Why this is the stronger position

1. **It turns a "weakness" into a strength.** Conceding that momentum / timing (Signal Alpha) is not an
   edge sounds like an admission of failure. In high-net-worth tax planning it reads as the opposite: a
   disciplined manager who knows exactly where the real value comes from and refuses to sell luck.
2. **It builds a Tax-Managed Core moat.** A generic index fund is available for ~3 bps; a prospect can
   buy one tomorrow. What they *cannot* buy off the shelf is an engine that automatically optimizes the
   asset location and lot protection of *these specific factor tilts* (Small/Value, EM, International).
   We move from selling a fund to selling an engine.
3. **It aligns with the CPA mindset.** A CPA does not care about beating the S&P 500 by 1% on luck. A
   CPA cares deeply about saving their client ~1.5% a year in tax leakage — a repeatable, defensible,
   *structural* number. That audience is exactly who the Tax-Leakage Diagnostic and the Gatekeeper
   Brief are written for.

---

## Three deliverables this methodology anchors

1. **Methodology rewrite** (this document + the client-copy reframe) — *first*.
2. **Tax-Leakage Diagnostic** — a one-page Before/After artifact: a concentrated, high-turnover book
   *leaking* tax versus the Structural-Alpha book *plugging* the leaks. Its numbers come from the
   Tax-Alpha decomposition (hold the same weight path, vary only the tax treatment) so the diagnostic
   is empirical, not asserted.
3. **CPA / Gatekeeper Technical Brief** — an institutional, quantitative brief on basis management,
   asset location, and TLH mechanics, aimed at the accountant who gate-keeps the client relationship.
   Same substantiation boundary; no outperformance claim.
