# Driftwood Methodology

How Driftwood flags and sizes trend-following positions, and the assumptions you
must validate before trusting the numbers.

## The momentum thesis

Time-series momentum: an instrument that has trended over a recent lookback,
*relative to its own volatility*, tends to keep trending over the near horizon
(Moskowitz, Ooi & Pedersen, "Time Series Momentum", 2012; Jegadeesh & Titman,
1993). It is the mirror of mean reversion — instead of betting an extreme reverts
to a baseline, we bet that drift persists.

### Trend score

For a lookback of `L` bars with per-bar return volatility `σ` (estimated over
`vol_window` bars), the cumulative log return `R = log(P_t / P_{t-L})` has, under
a random-walk null, standard deviation `σ·√L`. So

```
score = R / (σ · √L)
```

is a z-score: ~N(0, 1) when there is no trend, and large in magnitude when price
has drifted far more than noise explains. A flat or zero-volatility series scores
0 by construction — it can never manufacture a signal.

### Independent confirmation

A strong score alone never fires. An N-bar **Donchian channel breakout** must
agree: the latest close must make a new `breakout_channel`-bar high (for longs) or
low (for shorts). This is the trend-following analog of mrbet requiring an
independent model edge on top of a raw line move — the guard against chasing
noise.

## Sizing: volatility targeting + fractional Kelly

A trend position has a continuous payoff, so the over/under-CDF math is replaced
by:

- **Vol targeting** — `weight = sign · clamp(target_vol / annualized_vol, 0,
  max_leverage)`. Each position contributes a roughly constant volatility budget.
- **Continuous Kelly** — growth-optimal leverage `f* = μ / σ²`, reported for
  reference and bounded by `max_leverage`.
- A **fractional-Kelly scaler** (`kelly_fraction`) on the vol-target weight, the
  direct analog of mrbet's quarter-Kelly staking.

## The cost hurdle — the part that actually matters

Short-horizon trend strategies live or die on transaction cost. The expected edge
is modeled as a `continuation` fraction of recent per-bar drift, and a trade only
qualifies if that edge, accrued over the assumed `hold_bars`, beats the round-trip
cost:

```
edge_after_cost = continuation · drift_per_bar · hold_bars − 2 · (cost_bps / 1e4)
```

The backtest charges `cost_bps_per_side` on every change in weight, so paper alpha
that only exists gross of frictions is killed on contact. Keep `cost_bps_per_side`
honest: ~1–5 bps for liquid equities, materially more for thin crypto pairs.

## Entry vs. exit (hysteresis)

Entry is strict (gated Signal: strong score + breakout + net edge). Once in a
position the backtest **holds** while the score keeps its sign and stays above a
looser `exit_score_threshold`, exiting only when the trend fades or flips. Without
this band a noisy trend churns in and out around the entry threshold and loses
money even when the gross direction is right — the first thing the synthetic
backtest caught during development.

## The conjunctive trigger

A position fires only if **all** hold (mirroring mrbet's deliberately conjunctive
gate):

1. `|score| ≥ score_threshold` — trend is strong vs. the instrument's own noise.
2. A same-direction Donchian breakout (independent confirmation).
3. `edge_after_cost ≥ min_edge_after_cost` — survives the round trip.
4. `|target_weight| ≥ min_weight` — the vol-targeted position is non-negligible.

## Honest caveats (read before trusting live output)

- **`continuation` is an UNVALIDATED default** (ships at 0.10), exactly like
  mrbet's reversion weight β. The expected-edge / net-edge numbers are only as
  good as this coefficient — fit it against logged data per asset class.
- **Anomaly decay.** Time-series momentum is public and partly arbitraged;
  out-of-sample / walk-forward validation matters more than an in-sample curve.
- **Costs and capacity** dominate at short horizons. The synthetic demo uses 5
  bps; your real fills, slippage, borrow, and (for crypto) funding will differ.
- **Bars, not wall-clock.** All windows are in bars — re-tune `lookback`,
  `vol_window`, `breakout_channel`, and `engine.bars_per_year` together when you
  change frequency (daily vs. 15-minute crypto).
