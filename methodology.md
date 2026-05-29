# Methodology

How `mrbet` flags live NBA total / team-total bets, and how it captures the data
to validate itself.

## The mean-reversion thesis

When both teams start cold, the sportsbook over-drops the live total chasing
recent pace. Mean reversion says remaining scoring regresses toward each side's
**pregame** expected rate, so a depressed live line is frequently value on the
**OVER** (and a spiked line is value on the **UNDER**).

For a period of length `L` minutes with pregame baseline `T_pre`, after `e`
minutes elapsed with `S` points scored and `r = L − e` remaining:

```
fair_final = S + r · [ β · (T_pre / L)  +  (1 − β) · (S / e) ]
```

- **β (beta)** is the reversion weight. β = 1 → remaining play scores at the
  pregame rate (full reversion); β = 0 → it continues at the current pace.
- Empirical fit on 79 real 2026 playoff games: **β ≈ 1.0** (scoring reverts
  almost entirely to the pregame rate). Configured value: **0.90**.

A bet is flagged only when the line moved enough vs pregame, the model
independently sees enough edge, EV ≥ 0 at the offered odds, and enough time
remains in the period.

## Forward Capture

**Forward Capture: real-time recording of live odds to bypass historical
paywalls.**

Historical in-play odds are paywalled on every provider (The Odds API free tier
returns `401 HISTORICAL_UNAVAILABLE_ON_FREE_USAGE_PLAN`; ESPN exposes only
pregame open/close). Rather than pay, we record the **live** line as games are
played and grade it forward — closing-line value (CLV) needs no final score, and
win/loss fills in afterward. This produces *real* edge numbers on the free tier.

## The 9-Point Cadence

To minimize API usage while still capturing the key liquidity points, we sample
the live line only at the natural stoppages of Q1–Q3 — the ~6:00 and ~3:00
mandatory timeouts plus each quarter break. Expressed as **game-clock minutes
elapsed from tip-off**:

| Mark | Minute | Stoppage |
|-----:|:------:|:---------|
| 1 | **6**  | Q1 timeout 1 (~6:00) |
| 2 | **9**  | Q1 timeout 2 (~3:00) |
| 3 | **12** | End of Q1 |
| 4 | **18** | Q2 timeout 1 |
| 5 | **21** | Q2 timeout 2 |
| 6 | **24** | Halftime (End of Q2) |
| 7 | **30** | Q3 timeout 1 |
| 8 | **33** | Q3 timeout 2 |
| 9 | **36** | End of Q3 |

That is **9 odds calls per game** instead of ~150 at 60-second polling
(~17× fewer credits). On a 79-game backtest this 9-point cadence still retained
**86%** of the opportunities dense 1-minute sampling found. We stop after Q3:
once under the per-period minimum minutes-remaining, there isn't enough time for
reversion to pay out, so Q4 marks are intentionally omitted.

### How the poller spends credits

The FREE ESPN scoreboard drives the game clock. The poll loop wakes on a short
interval, but only spends a (paid) Odds API call when the clock crosses an
**uncaptured** cadence mark; captured marks persist across runs. Between marks it
refreshes the clock/score for free.

### Live-broadcast time mapping

For querying a historical endpoint by wall-clock (paid plans only), game-clock
minutes are stretched to real time with a ~**2.2×** broadcast multiplier from
tip-off (timeouts, reviews, halftime). See `efficient_backtest.py`.
