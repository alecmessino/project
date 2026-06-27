# Continuous-Tilt vs Concentrated Selection — Validation Results

**Status: MECHANISM CHECK ONLY — the real-data run could not complete in this environment.**
This records an exploration of whether holding the **whole ETF matrix and tilting weights by signal
strength** is a better book than concentrating in the trending top half. The numbers below come from
the **synthetic** harness only; they prove the mechanism discriminates but are **not evidence** about
real ETFs. The tilt overlay (`cross_section.tilt_overlay`) is **OFF in every committed config and is
not wired into the live signal.**

---

## The question

The live book is long-only cross-sectional momentum on the top half of the 18-ETF matrix
(`config/drift.yaml`): high signal capture, but ~13×/yr turnover and ~95% short-term gains on the
forward ledger — the least tax-efficient structure for a taxable client, which is exactly what the
firm's tax thesis argues against. The alternative tested here: hold the **whole universe**, set each
weight to `base·(1 + k·z)` (base = gross/N, `z` = cross-sectional z-score of the trend score), floor
long-only, cap at `max_weight`, renormalize to gross — rebalancing gently so the tax-aware no-trade
band and tax-loss harvesting do more of the work.

## What was run

```
TILT_SWEEP_REAL=1 python scripts/tilt_sweep.py    # real 40y proxy-spliced matrix (the real test)
python scripts/tilt_sweep.py                       # synthetic fallback (mechanism check)
```

**Outcome: the real-data pull is blocked in this environment** (the Yahoo feed is unreachable through
the agent proxy, same as the FIP and slow-book sweeps), so the run fell back to the deterministic
synthetic 18-ticker matrix with rotating leadership. Identical series across all four variants — only
the selection rule changes.

## Synthetic result (mechanism check — NOT evidence)

| variant | pre-tax | after-tax | retain | Sharpe | maxDD | turnover | ST% | names |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Concentrated (live)     | 1195% | 400% | 33.5% | 1.14 | 11.5% | 376% | 81% | 8.9 |
| Slow sleeve 40/60       | 1081% | 499% | 46.2% | 1.08 | 11.6% | 123% | 35% | 8.8 |
| Continuous tilt k=0.5   |  946% | 376% | 39.7% | **1.32** | **8.6%** | 186% | 57% | **17.5** |
| Continuous tilt k=1.0   | 1505% | 431% | 28.6% | **1.36** | 9.4% | 297% | 92% | 15.0 |

*retain = after-tax / pre-tax (higher = more tax-efficient).*

## What the mechanism check shows — and does not

**Directionally consistent with the thesis:**
- The continuous tilt delivers the **best risk-adjusted return** (Sharpe 1.32–1.36 vs 1.14
  concentrated) and the **shallowest drawdown** (8.6% vs 11.5%), holding ~17 names vs ~9 — diversification
  cuts volatility, as expected.
- The gentle tilt (k=0.5) is **more tax-efficient than concentrated** (39.7% vs 33.5% retention, 57%
  vs 81% short-term share) — gradual re-weighting realizes fewer short-term gains than binary
  enter/exit.

**Against a naive "tilt is strictly better" conclusion:**
- On this synthetic data the **Slow sleeve (40/60) is the most tax-efficient** (46% retention, 35% ST%,
  123% turnover) and has the highest after-tax return — its asymmetric hysteresis + lot protection
  beat the tilt's every-name-every-rebalance churn (186% turnover).
- The aggressive tilt (k=1.0) chases pre-tax return but at 92% short-term share — tax-hostile, no better
  than concentrated on retention.

## Honest caveats

- **Synthetic, not real.** The rotating-sinusoid regimes are smooth and may flatter or penalize specific
  books; this is a harness check, not a backtest. The real proxy-spliced run is the only thing that
  could support a deployment decision, and it did not run here.
- **No transaction-cost realism beyond the modeled per-side bps**, no capacity/spread modeling, and a
  single synthetic path (no sub-period or seed robustness).
- **Not wired live.** `tilt_overlay` defaults `False`; `config/drift.yaml` and `config/slow.yaml` keep it
  off (guarded by `test_tilt_overlay_off_by_default_and_in_shipped_configs`).

## Recommendation

The tilt's Sharpe/drawdown edge is promising enough to justify a **real-data** run on the proxy-spliced
matrix (when the feed is reachable), swept across `k`, sub-periods, and seeds, and compared head-to-head
with the slow sleeve on **after-tax, risk-adjusted** terms. Promote a variant to a real sleeve only if
that holds up — never on this synthetic check.
