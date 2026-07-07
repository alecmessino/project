# Driftwood 🪵

Driftwood is **two things that share a name**:

1. **A momentum signal engine** — a trend-following system for region- and factor-tilted
   **equity ETFs** (`src/drift/`, `src/drift/feed/`). It is the structural sibling of
   [`mrbet`](../mrbet/README.md): same harness (feed protocol → streaming engine →
   conjunctive trigger gate → signals + a cost-aware backtest), mirror-image model — where
   mean reversion fades an extreme, Driftwood rides it.
2. **A wealth-management research site** — the public, institutional-editorial website an
   RIA presents (`src/drift/web/` → built into `docs/`): the front door, the **After-Tax
   Review**, the **State Tax Atlas**, the **Tax Diagnostic**, and **Insights**. The
   momentum engine produces the hypothetical "Model Portfolio" figures the site cites.

> The name: `drift` is the deterministic trend term of a price process; driftwood is
> carried by the current. The thesis is that recent, volatility-adjusted price drift
> **persists** over the near horizon.

It is a **signal / research** system — it flags and sizes trend opportunities and
publishes illustrative modeling; it does not place trades and is not investment advice.

Operational runbook (build, deploy, compliance gates): **[`OPERATIONS.md`](../../OPERATIONS.md)**.

---

## The two halves

| | Signal engine | Wealth site |
|---|---|---|
| Source | `src/drift/*.py`, `src/drift/feed/` | `src/drift/web/*.html`, `driftwood.css` |
| Output | rankings, backtests, ledgers, tearsheet | `docs/*.html` (GitHub Pages) |
| CLI | `drift rank / xbacktest / studies / tearsheet / ledger` | `drift hub / export / taxlab / thesis / leakage / statemap` |
| Data | Yahoo Finance daily bars (keyless) | rendered from the engine's state, no live data |

## Why a separate package from `mrbet`?

`mrbet` and `drift` share *design*, not *code-with-betting-in-it*. Driftwood has no odds,
no over/under, no game clock, no basketball. The reusable ideas that carried over are
purely structural:

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

# Credibility & track record:
drift studies   --config config/drift.yaml                      # 5-study backtest report
drift tearsheet --config config/drift.yaml                      # long-history, OOS, vs buy&hold
drift ledger    --config config/drift.yaml                      # advance the forward paper ledger
```

`prices.csv` columns: `asof,close[,high,low,volume[,instrument]]`.

## The site (GitHub Pages)

The public site is served from `docs/` (GitHub Pages, `.nojekyll`). Pages are **rendered
templates**: edit the source in `src/drift/web/*.html`, then either run the `drift` CLI
(`drift hub/export/taxlab/…`) or, for structure-only edits, `python scripts/sync_docs.py`
to regenerate `docs/` while preserving the injected `window.__STATE__` data. `driftwood.css`
and `docs/fonts/` are committed static assets — edit `src/drift/web/driftwood.css` and copy
it across (`sync_docs.py` does this).

```bash
drift export --config config/drift.yaml --out docs/equities.html  # static dashboard
drift hub    --docs docs --out docs/index.html                    # front door (run last)
python scripts/sync_docs.py                                        # re-render docs from templates
```

The daily `.github/workflows/drift-pages.yml` Action regenerates the exhibits keyless
(Yahoo Finance) and `pages.yml` deploys `docs/`. Note: the `mrbet` betting dashboard also
publishes into `docs/` (`docs/mrbet.html` + `docs/board.json` etc.) and is intentionally
**not** linked from the Driftwood site.

## The strategy (engine)

The headline is a **trend-throttled cross-sectional rotation** over the region × factor
ETF matrix (`cross_section.py`):

- **Selection** — each month, rank the universe by vol-normalized trend and hold the
  strongest half, long-only, inverse-volatility weighted.
- **Exposure** — total invested exposure is scaled by the breadth of positive absolute
  trend (full in a broad uptrend, throttled toward a floor in a broad bear): the
  drawdown-control overlay.

A per-instrument **time-series** model (`triggers.py`, absolute trend + breakout +
vol-target) also exists and drives the signal cards / `live` stream.

## Feeds

Behind the same `PriceFeed` protocol, so the engine and backtest don't care where bars
come from. The product is keyless:

- **`yahoo`** — Yahoo Finance daily bars, **no API key** (the default). Explicit epoch
  bounds for true daily history (decades), retries with backoff.
- **`polygon`** — optional Polygon.io aggregates; set `POLYGON_API_KEY` in `.env`.

Every window is in **bars**: re-tune `lookback`, `vol_window`, `breakout_channel`, and
`engine.bars_per_year` together if you change frequency.

## The model in one paragraph

For each instrument the engine keeps a rolling window of bars. The **trend score** is the
cumulative log return over `lookback` bars divided by `sigma·√lookback` — a z-score that
is ~N(0,1) under a random walk and large when price has drifted far beyond its own noise.
A **Donchian channel breakout** must independently confirm the direction. The position is
then **volatility-targeted** and **fractional-Kelly-capped**. A trade fires only if the
expected edge — a `continuation` fraction of recent drift — survives the round-trip
transaction cost over the assumed holding horizon.

See [`methodology.md`](./methodology.md) for the math and the honest caveats (cost
sensitivity, anomaly decay, the unvalidated `continuation` coefficient).
