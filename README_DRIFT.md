# Driftwood 🪵

A **momentum** (trend-following) signal system for region- and factor-tilted
**equity ETFs**. Driftwood is the structural sibling of `mrbet`: it reuses the
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
drift simulate --replay prices.csv --config config/drift.yaml   # stream from a CSV

# Live feed (real data, keyless via Yahoo) — defaults to the region/factor matrix:
drift live --source yahoo --backtest --config config/drift.yaml

# Cross-sectional (relative-strength) rotation — the headline strategy:
drift rank      --config config/drift.yaml                      # current ranking + weights
drift xbacktest --config config/drift.yaml                      # universe backtest

# Dashboard / exhibits:
drift serve  --config config/drift.yaml                         # live dashboard at :8000
drift export --config config/drift.yaml --out docs/equities.html  # static dashboard

# Credibility & track record:
drift studies   --config config/drift.yaml                      # 5-study backtest report
drift tearsheet --config config/drift.yaml                      # long-history, OOS, vs buy&hold
drift ledger    --config config/drift.yaml                      # advance the forward paper ledger
drift hub       --docs docs --out docs/index.html               # equity landing page
```

`prices.csv` columns: `asof,close[,high,low,volume[,instrument]]`.

## Site (GitHub Pages, equity-only)

`docs/index.html` is the Driftwood hub (the public front door); it links the
**thesis**, the append-only forward **ledger**, the long-history **tearsheet**
(strategy vs buy-and-hold with an in-sample/out-of-sample split), the live
**dashboard**, and the **case studies**. The daily `drift-pages.yml` Action
regenerates them all keyless (Yahoo Finance) and the Pages workflow deploys
`docs/`. The mrbet betting dashboard is kept separate at `docs/mrbet.html` and is
not linked from the equity hub.

## The strategy

The headline is a **trend-throttled cross-sectional rotation** over the region ×
factor ETF matrix (`cross_section.py`):

- **Selection** — each month, rank the universe by vol-normalized trend and hold
  the strongest half, long-only, inverse-volatility weighted.
- **Exposure** — total invested exposure is scaled by the breadth of positive
  absolute trend (full in a broad uptrend, throttled toward a floor in a broad
  bear): the drawdown-control overlay.

A per-instrument **time-series** model (`triggers.py`, absolute trend + breakout +
vol-target) also exists and drives the signal cards/`live` stream.

## Feeds

Behind the same `PriceFeed` protocol, so the engine and backtest don't care where
bars come from. The product is keyless:

- **`yahoo`** — Yahoo Finance daily bars, **no API key** (the default). Uses
  explicit epoch bounds for true daily history (decades) and retries with backoff.
- **`polygon`** — optional Polygon.io aggregates; set `POLYGON_API_KEY` in `.env`.

Every window is in **bars**: re-tune `lookback`, `vol_window`,
`breakout_channel`, and `engine.bars_per_year` together if you change frequency.

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
