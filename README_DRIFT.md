# Driftwood 🪵

A time-series-**momentum** (trend-following) signal system for public markets —
equities and crypto. Driftwood is the structural sibling of `mrbet`: it reuses the
same harness (an interchangeable data-feed protocol → a streaming engine → a
conjunctive trigger gate → signals, plus a cost-aware backtest), but the model is
the **mirror image**. Where mean reversion fades an extreme, Driftwood rides it.

> The name: `drift` is the deterministic trend term of a price process; driftwood
> is carried by the current. The thesis is that recent, volatility-adjusted price
> drift **persists** over the near horizon.

It is a **signal** system — it flags and sizes trend opportunities; it does not
place trades.

## Why a separate package?

`mrbet` and `drift` share *design*, not *code-with-betting-in-it*. Driftwood has
no odds, no over/under, no game clock, no basketball. The reusable ideas that
carried over are purely structural:

| Harness piece (mrbet) | Driftwood analog |
|---|---|
| `OddsProvider` protocol | `PriceFeed` protocol (`feed/base.py`) |
| `Snapshot(state, lines)` | `Snapshot(asof, bars)` |
| `Engine.process_snapshot` | `Engine.process_snapshot` (rolling per-instrument history) |
| conjunctive `to_signal` gate | conjunctive `to_signal` gate (`triggers.py`) |
| `reversion.py` (pure math) | `signal.py` — vol-normalized momentum + Donchian breakout |
| `probability.py` EV/Kelly | `sizing.py` — vol targeting + continuous Kelly, net of cost |
| backtest / forward capture | `backtest.py` — walk-forward, cost-aware |

## Install & run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q tests/test_drift_*.py        # the Driftwood suite

drift demo --config config/drift.yaml  # full pipeline on a seeded synthetic trend
drift backtest --series prices.csv --instrument SPY --config config/drift.yaml
drift simulate --replay prices.csv --config config/drift.yaml   # stream live-style signals
```

`prices.csv` columns: `asof,close[,high,low,volume[,instrument]]`.

## The model in one paragraph

For each instrument the engine keeps a rolling window of bars. The **trend score**
is the cumulative log return over `lookback` bars divided by `sigma·√lookback`
(per-bar volatility times the root of the window) — a z-score that is ~N(0,1)
under a random walk and large when price has drifted far beyond its own noise. A
**Donchian channel breakout** must independently confirm the direction. The
position is then **volatility-targeted** (quieter instruments get more notional to
hit the same risk budget) and **fractional-Kelly-capped**. A trade only fires if
the expected edge — a `continuation` fraction of recent drift — survives the
round-trip transaction cost over the assumed holding horizon.

See `methodology_drift.md` for the math and the honest caveats (cost sensitivity,
anomaly decay, the unvalidated `continuation` coefficient).
