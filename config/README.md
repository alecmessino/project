# config/ — by project

This directory mixes configuration for the monorepo's projects. Grouped here so it's clear
what belongs to what (files are **not** moved — code and workflows reference these paths).

## 🪵 Driftwood (`drift`)
| File | Purpose |
|---|---|
| `drift.yaml` | Headline **fast** momentum book — universe, lookback/vol windows, cost model, `bars_per_year`, site/exhibit settings. |
| `slow.yaml` | Companion **slow** multi-factor, tax-efficient sleeve for taxable accounts (a natively-slow base signal, not the fast book gated). |
| `avantis_models.json` | Reference Avantis ETF "model" allocations — institutional-grade baseline weights used to reconcile the Driftwood book. |

## 🏀 mrbet
| File | Purpose |
|---|---|
| `settings.yaml` | Thresholds, `β`, `σ`, bankroll, Kelly fraction, markets, poll interval. |
| `games/*.yaml` | Per-game pregame baselines (+ Bovada odds ladder); `*.example.yaml` are templates. |

> ⚾ `the_third_turn` keeps its own config under `the_third_turn/config/`.
