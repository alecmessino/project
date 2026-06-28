# Tilt + Lot-Protection Hybrid vs Concentrated Selection — Validation Results

**Status: REAL-DATA RUN COMPLETE (40y proxy-spliced, via Tiingo from CI).**
Whether holding the **whole ETF matrix and tilting weights by signal strength** — wrapped in the
Tax-Managed Core's tax discipline (no-trade band + lot protection) — is a better book than
concentrating in the trending top half. The `tilt_overlay` / `lot_protect` flags are **OFF in every
committed config and not wired into the live signal**; this is research only. The real 40-year matrix
is cached at `tests/data/matrix_history.json` so `TILT_SWEEP_REAL=1 python scripts/tilt_sweep.py`
reproduces it offline.

---

## The four books
- **Unconstrained Core Alpha Strategy** (live, `config/drift.yaml`): long-only momentum on the top half
  — high signal capture, high turnover, ~94% short-term gains.
- **Tax-Managed Core Strategy** (slow 40/60, `config/slow.yaml`): hysteresis + lot protection + the
  tax-aware band.
- **Continuous tilt** (`weight = base·(1 + k·z)` across the whole universe).
- **Hybrid** = the tilt + BOTH Tax-Managed Core tax levers (band + lot protection).

## REAL DATA — full sample (40.1y, proxy-spliced; the canonical run)

| variant | pre-tax | after-tax | retain | Sharpe | maxDD | turnover | ST% | names |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unconstrained Core (live)         | 4367% | 901% | 20.6% | **0.64** | 56.7% | 344% | 94% | 6.6 |
| **Tax-Managed Core (slow)**       | 3299% | **1188%** | **36.0%** | 0.59 | 62.3% | 156% | 44% | 6.6 |
| Tilt k=0.5                        | 3467% | 858% | 24.7% | 0.60 | 57.4% | 195% | 87% | 13.1 |
| Tilt k=0.5 +band                  | 3402% | 1079% | 31.7% | 0.60 | 57.6% | 142% | 54% | 13.1 |
| **Hybrid (k=0.5 +band+lots)**     | 3353% | 1078% | 32.2% | 0.60 | 58.0% | 141% | 50% | 13.1 |
| Tilt k=1.0 +band+lots             | 4164% | 902% | 21.7% | 0.62 | 56.3% | 274% | 91% | 11.0 |

## REAL DATA — by decade (sub-period robustness)

| decade (tickers) | metric | Unconstr. | Slow | Hybrid (+band+lots) |
|---|---|---:|---:|---:|
| 1986–1996 (9)  | after-tax / retain / Sharpe | 83% / 51.5% / 0.79 | 92% / **68.3%** / 0.69 | 85% / 58.7% / **0.79** |
| 1996–2006 (14) | after-tax / retain / Sharpe | 95% / 45.4% / **0.82** | 89% / **63.3%** / 0.67 | 108% / 58.9% / 0.77 |
| 2006–2016 (18) | after-tax / retain / Sharpe | 41% / 47.4% / 0.39 | 33% / **75.9%** / 0.27 | **52%** / 63.3% / 0.38 |
| 2016–2026 (18) | after-tax / retain / Sharpe | 86% / 50.7% / 0.66 | 94% / 65.8% / 0.61 | **114% / 61.9% / 0.69** |

## Synthetic vs real — what changed (the honest reconciliation)

| claim (synthetic) | synthetic | **real (full sample)** | verdict |
|---|---|---|---|
| Tilt/hybrid has the best Sharpe | 1.37 vs 1.14 | **0.60 vs 0.64** | ❌ does not replicate — the edge inverts slightly |
| Tilt/hybrid has the shallowest drawdown | 8.9% vs 11.5% | **58% vs 57%** | ❌ no edge — real DDs are uniformly deep (incl. 2008) |
| Hybrid beats the slow book on tax | 46.5% vs 46.2% retain | **32.2% vs 36.0% retain** | ❌ slow book is still the tax champion (full sample) |
| The tax levers cut ST churn | 57%→29% ST | **87%→50% ST, 195%→141% turnover** | ✅ confirmed — they work as designed |
| The tilt is far more diversified | ~17 vs ~9 names | **13 vs 7 names** | ✅ confirmed |

**What this means.** The synthetic harness *overstated* the tilt's risk-adjusted edge: its smooth
rotating regimes manufactured a Sharpe/drawdown advantage that real markets do not pay. On the full
40-year sample the **Tax-Managed Core (slow) remains the most tax-efficient and highest after-tax book
(1188%, 36% retention)**; the hybrid lands *between* the bare tilt and the slow book — its tax
machinery genuinely works (ST 87%→50%), but it does not dominate.

**The real signal is in the sub-periods.** The full-sample number is dragged down by the early decades,
when only 9–14 of the 18 ETFs existed (the rest are proxy back-fill), muting the tilt's breadth. In
the **full-universe era (2006–2026)** the hybrid is the best after-tax book in *both* decades, and in
**2016–2026 it leads on after-tax (114%) AND Sharpe (0.69)** — diversification + tax efficiency pay
once the universe is actually broad. So the hybrid's edge is real but *regime- and breadth-dependent*,
not a free lunch.

## Caveats
- **Proxy splice**: 14 of 18 tickers are back-filled before inception with style-faithful Vanguard /
  DFA / WisdomTree proxies; pre-2006 history is approximate.
- **Lot-protection approximation**: protection keys on the position's first-entry age, while the FIFO
  tax engine dates each lot — newer adds can still be short-term if sold.
- **Determinism**: the `+band+lots` rows carry ~1–2% run-to-run variation from set-iteration order in
  the lot-protection redistribution (hash-seed dependent); it does not change any conclusion. Set
  `PYTHONHASHSEED=0` for bit-exact reproduction.
- **Single path, modeled per-side cost only** — no spread/capacity/borrow realism.
- **Not wired live**; both flags default off and are guarded.

## Recommendation
Do **not** promote the hybrid over the Tax-Managed Core wholesale — on the full sample the slow book
still wins on after-tax. But the hybrid is a legitimate, more-diversified, tax-efficient book that is
the **best after-tax option in the recent full-universe era (2006–2026)**. Next step before any
deployment: a cost/capacity-aware run focused on the full-universe period, sweeping `k` and the
no-trade band, and comparing on after-tax, risk-adjusted terms.

---

## Modern-era optimization (2006–present) — `scripts/tilt_optimize.py`
Deterministic (`PYTHONHASHSEED=0`) grid over tilt aggressiveness `k` × no-trade band, on the
20-year full-universe window, net of cost. Benchmarks on the same window (5 bps/side):
Unconstrained Core after-tax **165.5%** (Sharpe 0.51, turn 368%, ST 96%); Tax-Managed Core (slow)
after-tax **181.6%** (Sharpe 0.45, turn 150%, ST 41%).

**AFTER-TAX RETURN %** (rows `k`, cols band) — **SHARPE** in parentheses:

| k \ band | 2% | 4% | 6% | 8% | 10% |
|---|---|---|---|---|---|
| 0.3  | 250 (.51) | 308 (.50) | 337 (.46) | 439 (.49) | **486 (.49)** |
| 0.5  | 208 (.52) | 241 (.51) | 275 (.49) | 302 (.50) | 344 (.52) |
| 0.75 | 187 (.52) | 204 (.52) | 243 (.53) | 256 (.52) | 261 (.51) |
| 1.0  | 188 (.53) | 195 (.53) | 212 (.53) | 217 (.51) | 216 (.50) |

Turnover and short-term share fall monotonically toward the low-`k` / wide-band corner (e.g. k=0.3,
band=10% → **3% turnover, 1% ST**; k=1.0, band=2% → 291% turnover, 96% ST).

### What the grid actually says (read this before celebrating the 486%)
- **The momentum signal adds no risk-adjusted value here.** Sharpe is flat (**0.45–0.53**) across the
  *entire* grid and across both benchmarks — turning `k` up (more aggressive momentum) does **not**
  raise Sharpe; it only adds turnover and short-term tax drag.
- **The "after-tax optimum" is degenerate.** The selection rule (max after-tax s.t. turnover ≤ slow and
  ST% ≤ 50%) lands at **k=0.3, band=10% → 486% after-tax, 3% turnover, 1% ST** — but that is a
  *near-static, mildly-tilted, equal-weight buy-and-hold of all 18 ETFs*, not a momentum strategy. Its
  high after-tax number is **tax deferral + diversified beta**, not alpha: it barely trades, so it
  realizes almost no taxable gains. Its edge survives 15 bps/side untouched (485.3%) precisely because
  there is nothing to trade.
- **It is not a free lunch.** That cell's max drawdown is **65.5%** — *deeper* than the slow book (61%)
  and the concentrated book (56%): a fully-invested broad basket that tilts toward small/EM took the
  full 2008 hit. The Sharpe (0.49) reflects high return against high risk.

### Honest conclusion
The optimization does **not** validate a momentum-alpha deployment. What it validates is that, in the
modern era, **after-tax return is dominated by tax efficiency (low turnover) and diversification, not
by the momentum signal** — the logical optimum of "maximize after-tax, keep turnover defensible" is to
*barely trade a broad ETF basket*, which is essentially low-cost, tax-managed, broadly-diversified
indexing (asset location + minimal realization). That is the firm's genuine, defensible edge — and it
is exactly the **Tax-Managed Core** thesis — **not** a momentum claim.

**Recommendations:**
- **Marketing:** position the Tax-Managed Core on **breadth + tax management** (it leverages an ETF
  universe that didn't exist 30 years ago to compound more *after tax* than concentrated or
  high-turnover legacy books). Do **not** market the momentum tilt as alpha — the data does not support
  it (flat Sharpe).
- **Engine split:** the large-account-only hybrid case is **weak** — if the edge is tax-deferred broad
  beta, a large account gets the same from a broad, tax-managed, low-turnover basket without the
  momentum machinery. Keep momentum aggressiveness **low** (`k≈0.3`) and the band **wide** if used at
  all; the value is in *not trading*, not in the signal.
- **Risk:** any broad fully-invested version carries a ~60–65% historical drawdown — size and disclose
  accordingly.

*Caveats: single real path; proxy-spliced pre-2006 excluded by the window; flat-bps cost is a capacity
proxy, not a market-impact model; research only — `tilt_overlay`/`lot_protect` are OFF in every shipped
config and not wired to the live signal.*
