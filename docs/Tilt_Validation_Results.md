# Tilt + Lot-Protection Hybrid vs Concentrated Selection — Validation Results

**Status: MECHANISM CHECK ONLY — the real-data run is pending a reachable feed.**
This records whether holding the **whole ETF matrix and tilting weights by signal strength** — and
then wrapping it in the Tax-Managed Core's tax discipline — is a better book than concentrating in
the trending top half. The numbers below come from the **synthetic** harness only; they prove the
mechanism discriminates but are **not evidence** about real ETFs. The tilt overlay
(`cross_section.tilt_overlay`) and lot-protection hybrid flag (`cross_section.lot_protect`) are
**OFF in every committed config and not wired into the live signal.**

---

## The question
The **Unconstrained Core Alpha Strategy** (the live book, `config/drift.yaml`) is long-only
cross-sectional momentum on the top half of the 18-ETF matrix: high signal capture, but ~13×/yr
turnover and ~95% short-term gains on the forward ledger — the least tax-efficient structure for a
taxable client. The **Tax-Managed Core Strategy** (the slow 40/60 sleeve, `config/slow.yaml`) trades
that down with asymmetric hysteresis + lot protection + a tax-aware no-trade band.

The earlier sweep showed a broad continuous tilt earns the best Sharpe and shallowest drawdown but
was *not* the most tax-efficient. The **hybrid** tested here keeps the tilt weighting
(`weight = base·(1 + k·z)` across the whole universe) and layers on **both** Tax-Managed Core tax
levers — the tax-aware no-trade band and lot protection (delay a near-1-year sale unless the signal
collapses) — to convert the tilt's short-term churn into long-term gains.

## What was run
```
python scripts/tilt_sweep.py                       # synthetic fallback (mechanism check)
TILT_SWEEP_REAL=1 python scripts/tilt_sweep.py     # real 40y proxy-spliced matrix (PENDING a feed)
```
**Real-data status:** the keyless chain is currently unusable from this environment — **Stooq** serves
a JavaScript anti-bot interstitial (no CSV) and **Yahoo** returns HTTP 429 (cloud-IP rate limit); no
`TIINGO_API_KEY` is set. The real run is paused pending a Tiingo key (or another reachable source);
when available, the committed cache makes it reproducible offline thereafter.

## Synthetic result (mechanism check — NOT evidence)

| variant | pre-tax | after-tax | retain | Sharpe | maxDD | turnover | ST% | names |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unconstrained Core (live)         | 1195% | 400% | 33.5% | 1.14 | 11.5% | 376% | 81% | 8.9 |
| Tax-Managed Core (slow 40/60)     | 1077% | 498% | 46.2% | 1.08 | 11.6% | 123% | 35% | 8.8 |
| Tilt k=0.5                        |  946% | 376% | 39.7% | 1.32 | 8.6% | 186% | 57% | 17.5 |
| Tilt k=0.5 +band                  |  990% | 457% | 46.2% | 1.34 | 8.8% | 111% | 33% | 17.5 |
| **Tilt k=0.5 +band+lots (HYBRID)** | 1060% | **493%** | **46.5%** | **1.37** | **8.9%** | **109%** | **29%** | 17.5 |
| Tilt k=1.0 +band+lots             | 1679% | 531% | 31.6% | 1.42 | 8.8% | 239% | 73% | 15.0 |

*retain = after-tax / pre-tax (higher = more tax-efficient). +band isolates the no-trade band; +lots
adds lot protection.*

## What the mechanism check shows
**The hybrid bridges the risk-vs-tax gap on this data:**
- **Best Sharpe (1.37)** of every tax-managed option — above the slow book's 1.08 and the bare tilt's
  1.32 — and it keeps the tilt's **shallow drawdown (8.9% vs 11.6% slow / 11.5% concentrated)**,
  holding ~17 names vs ~9.
- **Tax efficiency now matches/beats the slow book**: retention 46.5% (vs 46.2%), short-term share
  **29% (vs 35%)**, turnover **109% (lowest)** — the lot protection pushed the tilt's 57% ST down to
  29%, and after-tax return (493%) essentially ties the slow book (498%) at a higher Sharpe.
- **Lever attribution**: the no-trade **band** does most of the tax work (ST 57%→33%, retention
  39.7%→46.2%); **lot protection** adds the final increment (ST 33%→29%) and a small Sharpe lift.
- **k=0.5 is the sweet spot**: k=1.0 chases pre-tax return (and Sharpe 1.42) but goes tax-hostile
  (73% ST, 31.6% retention).

## Honest caveats
- **Synthetic, not real.** Smooth rotating-sinusoid regimes; a harness check, not a backtest. The real
  proxy-spliced run is the only thing that could support a deployment decision, and it is pending a
  reachable feed.
- **Lot-protection approximation.** Protection keys on the position's first-entry age, while the FIFO
  tax engine dates each lot — newer mid-position adds can still be short-term if sold (the same
  approximation the slow sleeve already ships). Directionally sound; the exact ST→LT split on real
  data may differ.
- **Single path, no transaction-cost realism beyond modeled per-side bps**, no capacity/spread, no
  sub-period or seed robustness yet.
- **Not wired live.** `tilt_overlay` and `lot_protect` default `False`; both shipped configs keep them
  off (guarded).

## Recommendation
The hybrid is a genuine "best of both" on the mechanism check — the tilt's Sharpe/drawdown edge **plus**
the Tax-Managed Core's tax efficiency. This justifies a **real-data** run on the proxy-spliced matrix
(swept across `k`, sub-periods, and the full sample) before any deployment decision. Promote the hybrid
to the live Tax-Managed Core benchmark only if that holds up — never on this synthetic check.
